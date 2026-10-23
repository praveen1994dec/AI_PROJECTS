import shutil
import subprocess
import json
from typing import Any, Optional, Tuple, Dict, Union


class AWSCLIError(Exception):
    pass


class AWSCredentialsError(AWSCLIError):
    pass


class AWSPermissionError(AWSCLIError):
    pass


class CommandTimeoutError(AWSCLIError):
    pass


def _check_aws_installed() -> None:
    if shutil.which("aws") is None:
        raise AWSCLIError("AWS CLI not found. Please install the AWS CLI and ensure it's on PATH.")


def _parse_json_or_text(output: bytes) -> Union[Dict[str, Any], list, str, None]:
    text = output.decode("utf-8").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def run_aws(
    aws_args: list,
    region: Optional[str] = None,
    timeout: int = 30,
    parse_json: bool = True,
) -> Tuple[Union[Dict[str, Any], list, str, None], str]:
    """Run an AWS CLI command and return (parsed_output, stderr).

    - aws_args: list of aws CLI tokens after the leading "aws" (e.g. ['ec2','describe-instances']).
    - region: optional AWS region string; when provided, adds --region <region> to the command.
    - timeout: seconds before timing out the subprocess.
    - parse_json: attempt to JSON-decode stdout; otherwise return raw text.

    Raises AWSCLIError / AWSCredentialsError / AWSPermissionError / CommandTimeoutError on failure.
    """
    _check_aws_installed()

    cmd = ["aws"] + aws_args
    if region:
        # insert region flag if not already present
        if "--region" not in aws_args and not any(a.startswith("--region=") for a in aws_args):
            cmd += ["--region", region]

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise CommandTimeoutError(f"AWS CLI command timed out after {timeout}s: {' '.join(cmd)}")

    stderr = proc.stderr.decode("utf-8", errors="ignore")

    # Detect common error cases
    if proc.returncode != 0:
        # Credentials missing
        if "Unable to locate credentials" in stderr or "Unable to locate AWS credentials" in stderr:
            raise AWSCredentialsError(stderr.strip() or "AWS credentials not configured.")
        # Permission denied / AccessDenied
        if "AccessDenied" in stderr or "is not authorized to perform" in stderr or "UnauthorizedOperation" in stderr:
            raise AWSPermissionError(stderr.strip() or "Insufficient IAM permissions to run this command.")
        # Generic aws cli error
        raise AWSCLIError(stderr.strip() or "AWS CLI command failed with non-zero exit status.")

    parsed = None
    if parse_json:
        parsed = _parse_json_or_text(proc.stdout)
    else:
        parsed = proc.stdout.decode("utf-8", errors="ignore")

    return parsed, stderr
