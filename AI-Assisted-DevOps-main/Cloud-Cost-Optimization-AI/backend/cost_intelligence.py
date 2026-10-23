"""
Cost intelligence layer (AI-free): current/previous/forecast/top-resources/anomalies.
Uses aws_client.run_aws for CLI interactions and aws_scanner for resource inventory fallback.
Caches results in-memory with a TTL to avoid hammering Cost Explorer.
"""
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import time

from aws_client import run_aws, AWSCLIError, AWSCredentialsError, AWSPermissionError, CommandTimeoutError
from aws_scanner import scan_region

# Simple in-memory TTL cache
_CACHE: Dict[Tuple[str, str, Tuple], Tuple[float, Any]] = {}
_CACHE_TTL = 15 * 60  # 15 minutes


def _cache_get(key: Tuple[str, str, Tuple]):
    entry = _CACHE.get(key)
    if not entry:
        return None
    ts, val = entry
    if time.time() - ts > _CACHE_TTL:
        del _CACHE[key]
        return None
    return val


def _cache_set(key: Tuple[str, str, Tuple], value: Any):
    _CACHE[key] = (time.time(), value)


def _first_day_of_month(d: date) -> date:
    return d.replace(day=1)


def _last_day_of_prev_month(d: date) -> date:
    first = _first_day_of_month(d)
    return first - timedelta(days=1)


def _format_date(d: date) -> str:
    return d.isoformat()


def _parse_ce_daily_series(parsed: Dict[str, Any]) -> Tuple[float, List[Dict[str, Any]]]:
    # Return (total, [ {date, amount, services: {service: amount}} ])
    total = 0.0
    series: List[Dict[str, Any]] = []
    try:
        results = parsed.get("ResultsByTime", []) if isinstance(parsed, dict) else []
        for day in results:
            time_period = day.get("TimePeriod", {})
            start = time_period.get("Start")
            groups = day.get("Groups", []) or []
            day_total = 0.0
            services: Dict[str, float] = {}
            # If Grouped by SERVICE
            for g in groups:
                keys = g.get("Keys", [])
                metrics = g.get("Metrics", {})
                amt = 0.0
                if "UnblendedCost" in metrics:
                    try:
                        amt = float(metrics["UnblendedCost"].get("Amount", "0"))
                    except Exception:
                        amt = 0.0
                svc = keys[0] if keys else ""
                services[svc] = services.get(svc, 0.0) + amt
                day_total += amt
            series.append({"date": start, "amount": day_total, "services": services})
            total += day_total
    except Exception:
        pass
    return total, series


def get_current_cost(region: str) -> Dict[str, Any]:
    key = (region, "cost_current", ())
    cached = _cache_get(key)
    if cached:
        return cached

    today = date.today()
    start = _first_day_of_month(today)
    # CE end is exclusive; use tomorrow to include today
    end = today + timedelta(days=1)

    args = [
        "ce",
        "get-cost-and-usage",
        "--time-period",
        f"Start={_format_date(start)},End={_format_date(end)}",
        "--granularity",
        "DAILY",
        "--metrics",
        "UnblendedCost",
        "--group-by",
        "Type=DIMENSION,Key=SERVICE",
        "--output",
        "json",
    ]

    parsed, stderr = run_aws(args, region=region, timeout=60)
    total, series = _parse_ce_daily_series(parsed if parsed else {})

    out = {"available": True, "total": total, "series": series}
    _cache_set(key, out)
    return out


def get_previous_month_cost(region: str) -> Dict[str, Any]:
    key = (region, "cost_previous", ())
    cached = _cache_get(key)
    if cached:
        return cached

    today = date.today()
    last = _last_day_of_prev_month(today)
    start = last.replace(day=1)
    end = last + timedelta(days=1)

    args = [
        "ce",
        "get-cost-and-usage",
        "--time-period",
        f"Start={_format_date(start)},End={_format_date(end)}",
        "--granularity",
        "DAILY",
        "--metrics",
        "UnblendedCost",
        "--group-by",
        "Type=DIMENSION,Key=SERVICE",
        "--output",
        "json",
    ]

    parsed, stderr = run_aws(args, region=region, timeout=60)
    total, series = _parse_ce_daily_series(parsed if parsed else {})

    # per-service breakdown from the month
    service_totals: Dict[str, float] = {}
    try:
        results = parsed.get("ResultsByTime", []) if isinstance(parsed, dict) else []
        # Sum across ResultsByTime groups
        for day in results:
            groups = day.get("Groups", []) or []
            for g in groups:
                keys = g.get("Keys", [])
                metrics = g.get("Metrics", {})
                amt = 0.0
                if "UnblendedCost" in metrics:
                    try:
                        amt = float(metrics["UnblendedCost"].get("Amount", "0"))
                    except Exception:
                        amt = 0.0
                svc = keys[0] if keys else ""
                if svc:
                    service_totals[svc] = service_totals.get(svc, 0.0) + amt
    except Exception:
        service_totals = {}

    out = {"available": True, "total": total, "series": series, "services": service_totals}
    _cache_set(key, out)
    return out


def get_forecast(region: str, days: int = 15) -> Dict[str, Any]:
    key = (region, "cost_forecast", (days,))
    cached = _cache_get(key)
    if cached:
        return cached

    tomorrow = date.today() + timedelta(days=1)
    end = tomorrow + timedelta(days=days)

    args = [
        "ce",
        "get-cost-forecast",
        "--time-period",
        f"Start={_format_date(tomorrow)},End={_format_date(end)}",
        "--metric",
        "UNBLENDED_COST",
        "--granularity",
        "DAILY",
        "--output",
        "json",
    ]

    try:
        parsed, stderr = run_aws(args, region=region, timeout=60)
    except AWSPermissionError:
        raise
    except AWSCredentialsError:
        raise
    except CommandTimeoutError:
        raise
    except AWSCLIError as e:
        # If CE cannot forecast due to insufficient data, the CLI often returns an error mentioning "DataAlreadyFinalized" or "Forecast" related messages.
        reason = str(e)
        out = {"available": False, "reason": reason}
        _cache_set(key, out)
        return out

    # parsed expected to have ForecastResultsByTime
    total = 0.0
    series: List[Dict[str, Any]] = []
    try:
        fr = parsed.get("ForecastResultsByTime", []) if isinstance(parsed, dict) else []
        for d in fr:
            start = d.get("TimePeriod", {}).get("Start")
            amt = 0.0
            if "MeanValue" in d:
                try:
                    amt = float(d.get("MeanValue", 0.0))
                except Exception:
                    amt = 0.0
            series.append({"date": start, "amount": amt})
            total += amt
    except Exception:
        pass

    out = {"available": True, "total": total, "series": series}
    _cache_set(key, out)
    return out


def _try_group_by_resource_id(region: str, start: date, end: date) -> Optional[List[Dict[str, Any]]]:
    # Attempt to group by RESOURCE_ID
    args = [
        "ce",
        "get-cost-and-usage",
        "--time-period",
        f"Start={_format_date(start)},End={_format_date(end)}",
        "--granularity",
        "MONTHLY",
        "--metrics",
        "UnblendedCost",
        "--group-by",
        "Type=DIMENSION,Key=RESOURCE_ID",
        "--output",
        "json",
    ]
    try:
        parsed, stderr = run_aws(args, region=region, timeout=60)
    except Exception:
        return None

    out: List[Dict[str, Any]] = []
    try:
        results = parsed.get("ResultsByTime", []) if isinstance(parsed, dict) else []
        for period in results:
            groups = period.get("Groups", []) or []
            for g in groups:
                keys = g.get("Keys", [])
                metrics = g.get("Metrics", {})
                amt = 0.0
                if "UnblendedCost" in metrics:
                    try:
                        amt = float(metrics["UnblendedCost"].get("Amount", "0"))
                    except Exception:
                        amt = 0.0
                rid = keys[0] if keys else None
                if rid and amt > 0:
                    out.append({"resource_id": rid, "cost": amt})
    except Exception:
        return None

    return out if out else None


def _heuristic_rank_resources(region: str, service_costs: Dict[str, float], limit: int) -> List[Dict[str, Any]]:
    # Use aws_scanner to inventory resources, then heuristically assign costs
    inv = scan_region(region)
    resources = inv.get("resources", [])

    # Group resources by service substring in resource_type
    svc_map: Dict[str, List[Dict[str, Any]]] = {}
    for r in resources:
        # Infer service name from resource_type prefix
        rt = r.get("resource_type", "")
        if rt.startswith("ec2"):
            svc = "Amazon Elastic Compute Cloud - Compute"
        elif rt.startswith("rds"):
            svc = "Amazon Relational Database Service"
        elif rt.startswith("s3") or rt.get("resource_type") == "s3:bucket":
            svc = "Amazon Simple Storage Service"
        elif rt.startswith("lambda"):
            svc = "AWS Lambda"
        else:
            svc = "other"
        svc_map.setdefault(svc, []).append(r)

    scored: List[Dict[str, Any]] = []
    for svc, items in svc_map.items():
        svc_cost = service_costs.get(svc, 0.0)
        # Compute weights
        weights = []
        for it in items:
            w = 1.0
            cfg = it.get("configuration", {}) or {}
            rt = it.get("resource_type", "")
            # heuristics
            if rt == "ec2:instance" or rt.startswith("ec2"):
                itype = cfg.get("instance_type") or ""
                # simple heuristics: larger instance types contain 'xlarge' or numbers
                if "xlarge" in itype:
                    w = 10.0
                elif "large" in itype:
                    w = 5.0
                elif any(ch.isdigit() for ch in itype):
                    w = 3.0
                else:
                    w = 1.0
            elif rt == "ec2:volume":
                size = cfg.get("size_gb") or cfg.get("Size") or 0
                try:
                    w = float(size) if size else 1.0
                except Exception:
                    w = 1.0
                # unattached volumes (state == 'available') get a boost
                if cfg.get("state") == "available":
                    w *= 1.5
            elif rt == "s3:bucket":
                # unknown size; give neutral weight
                w = 1.0
            elif rt.startswith("rds"):
                # prefer instance class
                cls = cfg.get("instance_class") or ""
                if "db.r" in cls or "db.m" in cls:
                    w = 5.0
                else:
                    w = 2.0
            elif rt.startswith("lambda"):
                w = 0.5
            else:
                w = 1.0
            weights.append(max(0.1, w))

        total_weight = sum(weights) or 1.0
        # Distribute svc_cost proportionally
        for it, w in zip(items, weights):
            est = svc_cost * (w / total_weight)
            scored.append({
                "resource_id": it.get("id"),
                "resource_type": it.get("resource_type"),
                "name": it.get("name"),
                "region": it.get("region"),
                "cost": round(est, 6),
                "cost_basis": "estimated",
            })

    # sort by cost descending
    scored.sort(key=lambda x: x.get("cost", 0.0), reverse=True)
    return scored[:limit]


def get_top_resources(region: str, limit: int = 10) -> Dict[str, Any]:
    key = (region, "cost_top_resources", (limit,))
    cached = _cache_get(key)
    if cached:
        return cached

    today = date.today()
    start = _first_day_of_month(today)
    end = today + timedelta(days=1)

    # try resource-level grouping first
    resource_grouped = _try_group_by_resource_id(region, start, end)
    if resource_grouped:
        # resource_grouped contains resource_id and cost; attempt to enrich with scanner
        inv = scan_region(region)
        res_map = {r.get("id"): r for r in inv.get("resources", [])}
        out = []
        for item in resource_grouped:
            rid = item.get("resource_id")
            cost = item.get("cost", 0.0)
            rmeta = res_map.get(rid, {})
            out.append({
                "resource_id": rid,
                "resource_type": rmeta.get("resource_type"),
                "name": rmeta.get("name") or rid,
                "region": rmeta.get("region") or region,
                "cost": cost,
                "cost_basis": "exact",
            })
        out.sort(key=lambda x: x.get("cost", 0.0), reverse=True)
        out = out[:limit]
        _cache_set(key, out)
        return out

    # Fallback: group by SERVICE and heuristically assign costs
    # Get service totals for the same time range
    args = [
        "ce",
        "get-cost-and-usage",
        "--time-period",
        f"Start={_format_date(start)},End={_format_date(end)}",
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
    service_totals: Dict[str, float] = {}
    try:
        results = parsed.get("ResultsByTime", []) if isinstance(parsed, dict) else []
        for period in results:
            groups = period.get("Groups", []) or []
            for g in groups:
                keys = g.get("Keys", [])
                metrics = g.get("Metrics", {})
                amt = 0.0
                if "UnblendedCost" in metrics:
                    try:
                        amt = float(metrics["UnblendedCost"].get("Amount", "0"))
                    except Exception:
                        amt = 0.0
                svc = keys[0] if keys else ""
                if svc:
                    service_totals[svc] = service_totals.get(svc, 0.0) + amt
    except Exception:
        service_totals = {}

    estimated = _heuristic_rank_resources(region, service_totals, limit)
    _cache_set(key, estimated)
    return estimated


def _compute_anomalies_from_series(current_series: List[Dict[str, Any]], prev_series: List[Dict[str, Any]], threshold: float = 0.2) -> List[Dict[str, Any]]:
    # Build a date->amount map from current_series
    series = {d["date"]: d.get("amount", 0.0) for d in current_series}
    # Build ordered dates
    dates = sorted(series.keys())
    anomalies = []
    for i, dt in enumerate(dates):
        # trailing 7-day average excluding current day
        window_start = max(0, i - 7)
        if i == 0 or window_start == i:
            continue
        window_dates = dates[window_start:i]
        if not window_dates:
            continue
        avg = sum(series[d] for d in window_dates) / len(window_dates)
        today_amt = series[dt]
        if avg <= 0:
            continue
        pct = (today_amt - avg) / avg
        if abs(pct) >= threshold:
            severity = "medium"
            if abs(pct) >= 0.5:
                severity = "high"
            elif abs(pct) >= 0.2:
                severity = "medium"
            anomalies.append({
                "date": dt,
                "service": None,
                "amount": today_amt,
                "pct_change": round(pct * 100.0, 2),
                "severity": severity,
            })
    return anomalies


def get_anomalies(region: str, threshold: float = 0.2) -> Dict[str, Any]:
    key = (region, "cost_anomalies", (threshold,))
    cached = _cache_get(key)
    if cached:
        return cached

    # Try AWS CE anomalies first
    try:
        parsed, stderr = run_aws([
            "ce",
            "get-anomalies",
            "--time-period",
            f"Start={_format_date(date.today() - timedelta(days=60))},End={_format_date(date.today() + timedelta(days=1))}",
            "--output",
            "json",
        ], region=region, timeout=30)
        # If parsed has Anomalies
        anomalies = parsed.get("Anomalies", []) if isinstance(parsed, dict) else []
        if anomalies:
            # Normalize
            out = {"available": True, "anomalies": anomalies}
            _cache_set(key, out)
            return out
    except AWSPermissionError:
        raise
    except AWSCredentialsError:
        raise
    except CommandTimeoutError:
        raise
    except AWSCLIError:
        # proceed to fallback
        pass

    # Fallback: compute from current + previous month series
    current = get_current_cost(region)
    previous = get_previous_month_cost(region)
    current_series = current.get("series", [])
    prev_series = previous.get("series", [])
    anomalies = _compute_anomalies_from_series(current_series, prev_series, threshold=threshold)
    out = {"available": True, "anomalies": anomalies, "series": current_series}
    _cache_set(key, out)
    return out
