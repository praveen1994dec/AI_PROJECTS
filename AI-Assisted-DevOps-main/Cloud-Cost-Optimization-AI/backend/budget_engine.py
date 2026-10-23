from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from typing import Any, Dict, List

from cost_intelligence import get_current_cost, get_forecast
from aws_client import AWSCLIError

# In-memory budget store for now; this is a placeholder for the user-scoped table that Prompt 5 will add.
# Keys are region names, and the app currently runs without user auth.
_BUDGETS: Dict[tuple[int, str], Dict[str, Any]] = {}


def _days_remaining_in_month() -> int:
    today = date.today()
    last_day = monthrange(today.year, today.month)[1]
    return max(0, last_day - today.day)


def _forecast_for_month_end(region: str, mtd_spend: float) -> float:
    forecast = get_forecast(region, days=15)
    if not forecast or forecast.get("available") is False:
        return mtd_spend

    series = forecast.get("series", []) or []
    remaining = _days_remaining_in_month()
    if remaining <= 0:
        return mtd_spend

    projected = 0.0
    for item in series[:remaining]:
        amount = item.get("amount", 0.0)
        if isinstance(amount, (int, float)):
            projected += float(amount)
    return mtd_spend + projected


def _status_for(region: str, monthly_budget: float, mtd_spend: float, alert_threshold_percent: float) -> Dict[str, Any]:
    percent_used = 0.0 if monthly_budget == 0 else (mtd_spend / monthly_budget) * 100.0
    forecasted_month_end_spend = _forecast_for_month_end(region, mtd_spend)

    if mtd_spend > monthly_budget:
        status = "exceeded"
    elif percent_used >= float(alert_threshold_percent):
        status = "warning"
    elif forecasted_month_end_spend < monthly_budget:
        status = "on_track"
    else:
        status = "warning"

    return {
        "monthly_budget": monthly_budget,
        "alert_threshold_percent": alert_threshold_percent,
        "mtd_spend": round(mtd_spend, 2),
        "forecasted_month_end_spend": round(forecasted_month_end_spend, 2),
        "percent_used": round(percent_used, 2),
        "status": status,
        "days_remaining_in_month": _days_remaining_in_month(),
    }


def set_budget(region: str, monthly_budget: float, alert_threshold_percent: float = 80.0, user_id: int = 1) -> Dict[str, Any]:
    if not region or not region.strip():
        raise ValueError("region is required")
    if monthly_budget is None or float(monthly_budget) <= 0:
        raise ValueError("monthly_budget must be greater than 0")

    threshold = float(alert_threshold_percent)
    if not 0 <= threshold <= 100:
        raise ValueError("alert_threshold_percent must be between 0 and 100")

    budget = {
        "region": region,
        "monthly_budget": float(monthly_budget),
        "alert_threshold_percent": threshold,
    }
    _BUDGETS[(user_id, region)] = budget

    return get_budget(region, user_id=user_id)


def get_budget(region: str, user_id: int = 1) -> Dict[str, Any]:
    region_key = (region or "").strip()
    if not region_key:
        return {"configured": False}

    budget = _BUDGETS.get((user_id, region_key))
    if not budget:
        return {"configured": False}

    # Budget configuration is app-owned and must remain usable before AWS
    # credentials are configured. Spend values become available automatically
    # once Cost Explorer can be queried.
    try:
        current = get_current_cost(region_key)
        mtd_spend = float(current.get("total", 0.0) or 0.0)
    except AWSCLIError:
        mtd_spend = 0.0
    summary = _status_for(
        region_key,
        float(budget["monthly_budget"]),
        mtd_spend,
        float(budget.get("alert_threshold_percent", 80.0)),
    )
    summary["configured"] = True
    summary["region"] = region_key
    return summary


def get_all_budgets(user_id: int = 1) -> List[Dict[str, Any]]:
    budgets: List[Dict[str, Any]] = []
    for owner_id, region in sorted(_BUDGETS.keys()):
        if owner_id == user_id:
            budgets.append(get_budget(region, user_id=user_id))
    return budgets


def delete_budget(region: str, user_id: int = 1) -> bool:
    if not region:
        return False
    key = (user_id, region)
    if key in _BUDGETS:
        del _BUDGETS[key]
        return True
    return False
