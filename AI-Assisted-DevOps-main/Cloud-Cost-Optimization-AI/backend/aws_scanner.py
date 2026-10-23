"""
Cost-driven AWS resource discovery.
- Uses AWS Cost Explorer to find services with cost in the current billing cycle
  and then queries relevant resources only for those services.
- Returns aggregated resource inventory with type, id, configuration and tags.

This module depends on aws_client.run_aws for all AWS CLI interactions.
"""
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from aws_client import run_aws, AWSCLIError, AWSCredentialsError, AWSPermissionError, CommandTimeoutError


def _first_day_of_month(d: date) -> date:
    return d.replace(day=1)


def _tomorrow(d: date) -> date:
    return d + timedelta(days=1)


def get_active_services(region: Optional[str] = None) -> List[str]:
    """Query Cost Explorer for services incurring cost this billing cycle and return service names."""
    today = date.today()
    start = _first_day_of_month(today).isoformat()
    # CE requires End to be exclusive; use tomorrow
    end = _tomorrow(today).isoformat()

    args = [
        "ce",
        "get-cost-and-usage",
        "--time-period",
        f"Start={start},End={end}",
        "--granularity",
        "MONTHLY",
        "--metrics",
        "UnblendedCost",
        "--group-by",
        "Type=DIMENSION,Key=SERVICE",
        "--output",
        "json",
    ]

    parsed, stderr = run_aws(args, region=region, timeout=60)
    services: List[str] = []
    if not parsed:
        return services

    # Expect parsed to contain ResultsByTime -> [ { Groups: [ { Keys: [service], Metrics: { UnblendedCost: { Amount: "X" } } } ] } ]
    try:
        results = parsed.get("ResultsByTime", []) if isinstance(parsed, dict) else []
        for period in results:
            groups = period.get("Groups", []) or []
            for g in groups:
                keys = g.get("Keys", [])
                metrics = g.get("Metrics", {})
                amount = 0.0
                if "UnblendedCost" in metrics:
                    amt_str = metrics["UnblendedCost"].get("Amount", "0")
                    try:
                        amount = float(amt_str)
                    except (ValueError, TypeError):
                        amount = 0.0
                if amount > 0 and keys:
                    # service name usually in keys[0]
                    services.append(keys[0])
    except Exception:
        # If parsing failed, return empty list; caller may choose to run a broader scan
        return []

    # Deduplicate
    return sorted(list(set(services)))


def _tags_list_to_dict(tag_list: Optional[List[Dict[str, str]]]) -> Dict[str, str]:
    if not tag_list:
        return {}
    out: Dict[str, str] = {}
    for t in tag_list:
        key = t.get("Key") or t.get("key")
        value = t.get("Value") or t.get("value")
        if key:
            out[key] = value if value is not None else ""
    return out


def scan_region(region: str) -> Dict[str, Any]:
    """Scan resources in the given region using a cost-driven approach.

    Returns a dict: { "region": <region>, "resources": [ {resource}, ... ], "active_services": [...] }
    Each resource: { resource_type, id, name, region, configuration, tags }
    """
    response: Dict[str, Any] = {"region": region, "resources": [], "active_services": []}

    try:
        services = get_active_services(region=region)
    except AWSCredentialsError:
        raise
    except AWSPermissionError:
        raise
    except CommandTimeoutError:
        raise
    except AWSCLIError:
        services = []

    response["active_services"] = services

    probe_services = services or [
        "Amazon Elastic Compute Cloud - Compute",
        "Amazon Relational Database Service",
        "Amazon Simple Storage Service",
        "AWS Lambda",
    ]

    resources: List[Dict[str, Any]] = []

    for svc in probe_services:
        try:
            if "Elastic Compute Cloud" in svc or svc.lower().startswith("amazon ec2") or "EC2" in svc:
                parsed, _ = run_aws(["ec2", "describe-instances", "--output", "json"], region=region, timeout=30)
                if parsed:
                    reservations = parsed.get("Reservations", []) if isinstance(parsed, dict) else []
                    for r in reservations:
                        for inst in r.get("Instances", []) or []:
                            res = {
                                "resource_type": "ec2:instance",
                                "id": inst.get("InstanceId"),
                                "name": None,
                                "region": region,
                                "configuration": {
                                    "instance_type": inst.get("InstanceType"),
                                    "state": inst.get("State", {}).get("Name"),
                                    "launch_time": inst.get("LaunchTime"),
                                    "private_ip": inst.get("PrivateIpAddress"),
                                    "public_ip": inst.get("PublicIpAddress"),
                                    "platform": inst.get("Platform"),
                                },
                                "tags": _tags_list_to_dict(inst.get("Tags")),
                            }
                            if res["tags"].get("Name"):
                                res["name"] = res["tags"].get("Name")
                            resources.append(res)

            elif "Relational Database Service" in svc or "RDS" in svc or svc.lower().startswith("amazon rds"):
                parsed, _ = run_aws(["rds", "describe-db-instances", "--output", "json"], region=region, timeout=30)
                if parsed:
                    dbs = parsed.get("DBInstances", []) if isinstance(parsed, dict) else []
                    for db in dbs:
                        arn = db.get("DBInstanceArn")
                        tags = {}
                        if arn:
                            try:
                                tparsed, _ = run_aws(["rds", "list-tags-for-resource", "--resource-name", arn, "--output", "json"], region=region)
                                tag_list = tparsed.get("TagList") if isinstance(tparsed, dict) else []
                                tags = _tags_list_to_dict(tag_list)
                            except Exception:
                                tags = {}
                        res = {
                            "resource_type": "rds:db-instance",
                            "id": db.get("DBInstanceIdentifier"),
                            "name": db.get("DBName") or db.get("DBInstanceIdentifier"),
                            "region": region,
                            "configuration": {
                                "instance_class": db.get("DBInstanceClass"),
                                "engine": db.get("Engine"),
                                "status": db.get("DBInstanceStatus"),
                                "endpoint": db.get("Endpoint", {}),
                            },
                            "tags": tags,
                        }
                        resources.append(res)

            elif "Simple Storage Service" in svc or "S3" in svc or svc.lower().startswith("amazon s3"):
                parsed, _ = run_aws(["s3api", "list-buckets", "--output", "json"], region=region, timeout=30)
                buckets = parsed.get("Buckets", []) if isinstance(parsed, dict) else []
                for b in buckets:
                    name = b.get("Name")
                    bconf = {"creation_date": b.get("CreationDate")}
                    tags = {}
                    if name:
                        try:
                            loc, _ = run_aws(["s3api", "get-bucket-location", "--bucket", name, "--output", "json"], region=region)
                            location = None
                            if isinstance(loc, dict):
                                location = loc.get("LocationConstraint")
                            bconf["location"] = location
                        except Exception:
                            bconf["location"] = None

                        try:
                            tparsed, _ = run_aws(["s3api", "get-bucket-tagging", "--bucket", name, "--output", "json"], region=region, timeout=30)
                            tag_set = tparsed.get("TagSet") if isinstance(tparsed, dict) else []
                            tags = _tags_list_to_dict(tag_set)
                        except Exception:
                            tags = {}

                    res = {
                        "resource_type": "s3:bucket",
                        "id": name,
                        "name": name,
                        "region": region,
                        "configuration": bconf,
                        "tags": tags,
                    }
                    resources.append(res)

            elif "Lambda" in svc or svc.lower().startswith("aws lambda") or "AWS Lambda" in svc:
                parsed, _ = run_aws(["lambda", "list-functions", "--output", "json"], region=region, timeout=30)
                funcs = parsed.get("Functions", []) if isinstance(parsed, dict) else []
                for f in funcs:
                    tags = {}
                    arn = f.get("FunctionArn")
                    if arn:
                        try:
                            tparsed, _ = run_aws(["lambda", "list-tags", "--resource", arn, "--output", "json"], region=region, timeout=15)
                            tags = tparsed.get("Tags") if isinstance(tparsed, dict) else {}
                        except Exception:
                            tags = {}
                    res = {
                        "resource_type": "lambda:function",
                        "id": f.get("FunctionName"),
                        "name": f.get("FunctionName"),
                        "region": region,
                        "configuration": {
                            "runtime": f.get("Runtime"),
                            "last_modified": f.get("LastModified"),
                            "handler": f.get("Handler"),
                        },
                        "tags": tags,
                    }
                    resources.append(res)

            elif "Elastic Block Store" in svc or "EBS" in svc or "Volume" in svc:
                parsed, _ = run_aws(["ec2", "describe-volumes", "--output", "json"], region=region, timeout=30)
                vols = parsed.get("Volumes", []) if isinstance(parsed, dict) else []
                for v in vols:
                    res = {
                        "resource_type": "ec2:volume",
                        "id": v.get("VolumeId"),
                        "name": None,
                        "region": region,
                        "configuration": {
                            "size_gb": v.get("Size"),
                            "state": v.get("State"),
                            "volume_type": v.get("VolumeType"),
                        },
                        "tags": _tags_list_to_dict(v.get("Tags")),
                    }
                    resources.append(res)

            elif "Load Balancer" in svc or "ELB" in svc or "Elastic Load Balancing" in svc:
                try:
                    parsed, _ = run_aws(["elbv2", "describe-load-balancers", "--output", "json"], region=region, timeout=30)
                    lbs = parsed.get("LoadBalancers", []) if isinstance(parsed, dict) else []
                    for lb in lbs:
                        res = {
                            "resource_type": "elbv2:load-balancer",
                            "id": lb.get("LoadBalancerArn"),
                            "name": lb.get("LoadBalancerName"),
                            "region": region,
                            "configuration": {
                                "type": lb.get("Type"),
                                "scheme": lb.get("Scheme"),
                                "state": lb.get("State", {}).get("Code"),
                            },
                            "tags": {},
                        }
                        resources.append(res)
                except Exception:
                    pass

            else:
                continue

        except AWSCredentialsError:
            raise
        except AWSPermissionError:
            raise
        except CommandTimeoutError:
            raise
        except AWSCLIError:
            raise
        except Exception:
            continue

    response["resources"] = resources
    return response


if __name__ == "__main__":
    import json
    # quick local test
    print(json.dumps(scan_region("us-east-1"), indent=2))
