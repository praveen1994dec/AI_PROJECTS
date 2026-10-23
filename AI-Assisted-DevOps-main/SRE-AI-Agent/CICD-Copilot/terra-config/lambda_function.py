import json
import boto3
import urllib.request
import urllib.error
import re


GEMINI_MODEL = "gemini-2.5-flash"
SECRET_NAME = "gemini-api-key"
REGION_NAME = "us-east-1"

secrets_client = boto3.client("secretsmanager", region_name=REGION_NAME)

def get_gemini_api_key():
    secret = secrets_client.get_secret_value(SecretId=SECRET_NAME)
    return json.loads(secret["SecretString"])["GEMINI_API_KEY"]


def build_prompt(stage, logs):
    return f"""
You are a senior CI/CD Copilot specialized in Jenkins pipelines.

Pipeline context:
- Stage name: {stage}
- Expected outcome: Build an artifact usable by later stages

Your tasks:
1. Identify the failure category (build / runtime / config / infra / dependency / auth / unknown)
2. Identify the most likely root cause
3. Provide actionable fixes
4. Suggest a patch ONLY if clearly inferable

Respond ONLY in valid JSON with this schema:
{{
  "failure_category": "",
  "root_cause": "",
  "actionable_fixes": [],
  "suggested_patch": {{
    "file": "",
    "line": "",
    "fix": ""
  }}
}}

Logs:
{logs}
"""


def call_gemini(prompt: str) -> dict:
    api_key = get_gemini_api_key()

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={api_key}"
    )

    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = json.loads(resp.read())
        text = raw["candidates"][0]["content"]["parts"][0]["text"]

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass

        return {
            "failure_category": "unknown",
            "root_cause": "LLM returned invalid JSON",
            "actionable_fixes": [
                "Inspect raw LLM output",
                "Tighten prompt constraints"
            ],
            "suggested_patch": {}
        }

def lambda_handler(event, context):
    try:
        stage = event["stage"]
        job = event["job"]
        build_id = event["build_id"]
        logs = event["logs"][:6000]

        prompt = build_prompt(stage, logs)
        ai_analysis = call_gemini(prompt)

        response = {
            "status": "FAILURE",
            "job": job,
            "build_id": build_id,
            "stage": stage,
            "analysis": ai_analysis
        }

        return {
            "statusCode": 200,
            "body": json.dumps(response)
        }

    except KeyError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": f"Missing required field: {str(e)}"
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e)
            })
        }