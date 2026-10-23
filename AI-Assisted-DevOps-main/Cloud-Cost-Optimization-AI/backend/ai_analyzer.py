"""
AI-powered resource optimization analysis using OpenAI.
Analyzes infrastructure inventory and cost data to recommend optimizations.
"""
import os
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from openai import OpenAI, APIError, AuthenticationError
import dotenv

dotenv.load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID", "").strip()
AI_ENABLED = os.getenv("AI_ENABLED", "true").lower() == "true"


class AIAnalysisError(Exception):
    pass


def _build_analysis_prompt(resources: List[Dict[str, Any]], top_resources: List[Dict[str, Any]], region: str) -> str:
    """Build a detailed prompt for the AI to analyze resources for cost optimization."""
    
    # Summarize resources by type
    resources_by_type: Dict[str, int] = {}
    for r in resources:
        rt = r.get("resource_type", "unknown")
        resources_by_type[rt] = resources_by_type.get(rt, 0) + 1

    # Format top resources cost data
    top_cost_str = "\n".join([
        f"  - {r.get('name') or r.get('resource_id')}: ${r.get('cost', 0):.2f}/month ({r.get('resource_type', 'unknown')})"
        for r in top_resources[:10]
    ])

    prompt = f"""You are a cloud cost optimization expert. Analyze the following AWS infrastructure in region {region} and identify cost optimization opportunities.

## Infrastructure Summary
- Total resources: {len(resources)}
- Resource types: {json.dumps(resources_by_type, indent=2)}

## Top Cost-Driving Resources
{top_cost_str}

## Resource Details
{json.dumps(resources, indent=2)}

## Analysis Requirements
Analyze the infrastructure for:
1. Over-provisioned resources (e.g., t3.xlarge when t3.micro would suffice)
2. Idle or unattached resources (e.g., unattached EBS volumes, stopped instances)
3. Unused resources (e.g., unattached security groups, empty S3 buckets)
4. Misconfigurations (e.g., provisioned IOPS not in use, encryption overhead)
5. Legacy or outdated pricing tiers (e.g., gp2 vs gp3, t2 vs t3, old instance generations)
6. General best practices and cost optimization opportunities

## Response Format
Return ONLY valid JSON (no markdown, no code blocks) with this exact structure:
{{
    "summary": "Brief executive summary of findings",
    "total_estimated_monthly_savings": 0.00,
    "issues": [
        {{
            "resource_id": "resource identifier",
            "resource_type": "ec2:instance|rds:db-instance|s3:bucket|etc",
            "issue_type": "over_provisioned|unattached|unused|misconfigured|bad_practice",
            "severity": "high|medium|low",
            "title": "Short issue description",
            "description": "Detailed explanation of the issue and why it costs money",
            "current_cost": 0.00,
            "estimated_monthly_savings": 0.00,
            "fix_command": "Actual AWS CLI command to fix/investigate (e.g., aws ec2 modify-volume --volume-id vol-xxx --volume-type gp3)",
            "fix_description": "What the command does and why it saves money"
        }}
    ]
}}

Ensure all fix_command values are actual, executable AWS CLI commands that the user can copy and paste directly.
Be specific about IDs and parameters. Prioritize high-impact, easy-to-fix issues."""
    
    return prompt


def analyze_resources(resources: List[Dict[str, Any]], top_resources: List[Dict[str, Any]], region: str) -> Dict[str, Any]:
    """
    Call OpenAI to analyze resources and return optimization recommendations.
    
    Args:
        resources: List of resource dicts from aws_scanner.scan_region()
        top_resources: List of top-cost resource dicts from cost_intelligence.get_top_resources()
        region: AWS region being analyzed
    
    Returns:
        Dict with analysis results including issues, savings estimates, and fix commands
    """
    
    if not AI_ENABLED:
        return {
            "available": False,
            "reason": "AI analysis is disabled. Set AI_ENABLED=true and configure OPENAI_API_KEY to enable."
        }
    
    if not OPENAI_API_KEY:
        return {
            "available": False,
            "reason": "OpenAI API key not configured. Set OPENAI_API_KEY in .env or environment variables."
        }
    
    if not resources:
        return {
            "available": True,
            "summary": "No resources found in region.",
            "total_estimated_monthly_savings": 0.0,
            "issues": []
        }
    
    try:
        client = OpenAI(
            api_key=OPENAI_API_KEY,
            organization=OPENAI_ORG_ID if OPENAI_ORG_ID else None,
        )
        
        prompt = _build_analysis_prompt(resources, top_resources, region)
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a cloud cost optimization expert. Analyze AWS infrastructure and provide specific, actionable recommendations with exact AWS CLI commands."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=4000,
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Parse the JSON response
        try:
            analysis = json.loads(response_text)
        except json.JSONDecodeError:
            # If response contains markdown code blocks, try to extract JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
                analysis = json.loads(response_text)
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
                analysis = json.loads(response_text)
            else:
                raise AIAnalysisError(f"Failed to parse AI response as JSON: {response_text[:200]}")
        
        # Validate response structure
        if not isinstance(analysis, dict):
            raise AIAnalysisError("AI response is not a valid JSON object")
        
        # Ensure required fields
        analysis.setdefault("summary", "Analysis complete.")
        analysis.setdefault("total_estimated_monthly_savings", 0.0)
        analysis.setdefault("issues", [])
        analysis["available"] = True
        analysis["analyzed_at"] = datetime.utcnow().isoformat()
        analysis["region"] = region
        
        return analysis
    
    except AuthenticationError as e:
        return {
            "available": False,
            "reason": f"OpenAI authentication failed: {str(e)}. Check your API key."
        }
    except APIError as e:
        return {
            "available": False,
            "reason": f"OpenAI API error: {str(e)}"
        }
    except Exception as e:
        return {
            "available": False,
            "reason": f"Error analyzing resources: {str(e)}"
        }
