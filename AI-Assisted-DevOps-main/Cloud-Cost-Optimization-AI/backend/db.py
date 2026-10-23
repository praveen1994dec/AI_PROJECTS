"""
Database initialization, connection, and queries for the Cost Detective backend.
Uses asyncpg for async PostgreSQL access.
"""
import os
import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpg
import dotenv

dotenv.load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "cloud_cost_detective")


class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Initialize the connection pool."""
        if DATABASE_URL and not DATABASE_URL.startswith("******"):
            connection_config = {"dsn": DATABASE_URL}
        elif DB_PASSWORD:
            connection_config = {
                "user": DB_USER,
                "password": DB_PASSWORD,
                "host": DB_HOST,
                "port": DB_PORT,
                "database": DB_NAME,
            }
        else:
            raise ValueError("Configure DATABASE_URL or DB_USER/DB_PASSWORD/DB_HOST/DB_PORT/DB_NAME")
        self.pool = await asyncpg.create_pool(min_size=2, max_size=10, **connection_config)
        await self._create_tables()

    async def disconnect(self):
        """Close all connections."""
        if self.pool:
            await self.pool.close()

    async def _create_tables(self):
        """Create tables on startup if they don't exist."""
        if not self.pool:
            raise RuntimeError("Database not connected")

        async with self.pool.acquire() as conn:
            # Users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Budgets table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    region VARCHAR(50) NOT NULL,
                    monthly_budget NUMERIC(12, 2) NOT NULL,
                    alert_threshold_percent INTEGER DEFAULT 80,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, region)
                )
            """)

            # Analyses table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    region VARCHAR(50) NOT NULL,
                    resources_scanned INTEGER DEFAULT 0,
                    issues_found INTEGER DEFAULT 0,
                    estimated_savings NUMERIC(12, 2) DEFAULT 0,
                    cost_summary JSONB,
                    analysis_result JSONB,
                    status VARCHAR(50) DEFAULT 'completed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Cost snapshots table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS cost_snapshots (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    region VARCHAR(50) NOT NULL,
                    snapshot_date DATE NOT NULL,
                    daily_cost NUMERIC(12, 2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, region, snapshot_date)
                )
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS budget_alerts (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    region VARCHAR(50) NOT NULL,
                    billing_period VARCHAR(7) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, region, billing_period, status)
                )
            """)

            print("Database tables initialized successfully")


# Global database instance
db = Database()


# User queries
async def get_or_create_user(email: str, password_hash: str) -> int:
    """Get existing user by email or create new one. Returns user_id."""
    if not db.pool:
        raise RuntimeError("Database not connected")

    async with db.pool.acquire() as conn:
        # Try to get existing user
        user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", email)
        if user:
            return user["id"]

        # Create new user
        user_id = await conn.fetchval(
            "INSERT INTO users (email, password_hash) VALUES ($1, $2) RETURNING id",
            email,
            password_hash,
        )
        return user_id


async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieve user by email."""
    if not db.pool:
        raise RuntimeError("Database not connected")

    async with db.pool.acquire() as conn:
        user = await conn.fetchrow("SELECT id, email, password_hash FROM users WHERE email = $1", email)
        return dict(user) if user else None


# Budget queries
async def upsert_budget(user_id: int, region: str, monthly_budget: float, alert_threshold_percent: int = 80) -> Dict[str, Any]:
    """Create or update a budget."""
    if not db.pool:
        raise RuntimeError("Database not connected")

    async with db.pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            INSERT INTO budgets (user_id, region, monthly_budget, alert_threshold_percent)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id, region)
            DO UPDATE SET monthly_budget = $3, alert_threshold_percent = $4, updated_at = CURRENT_TIMESTAMP
            RETURNING id, user_id, region, monthly_budget, alert_threshold_percent
            """,
            user_id,
            region,
            monthly_budget,
            alert_threshold_percent,
        )
        return dict(result) if result else {}


async def get_budget(user_id: int, region: str) -> Optional[Dict[str, Any]]:
    """Retrieve a budget."""
    if not db.pool:
        raise RuntimeError("Database not connected")

    async with db.pool.acquire() as conn:
        budget = await conn.fetchrow(
            "SELECT id, user_id, region, monthly_budget, alert_threshold_percent FROM budgets WHERE user_id = $1 AND region = $2",
            user_id,
            region,
        )
        return dict(budget) if budget else None


async def get_all_budgets(user_id: int) -> List[Dict[str, Any]]:
    """Retrieve all budgets for a user."""
    if not db.pool:
        raise RuntimeError("Database not connected")

    async with db.pool.acquire() as conn:
        budgets = await conn.fetch(
            "SELECT id, user_id, region, monthly_budget, alert_threshold_percent FROM budgets WHERE user_id = $1 ORDER BY region",
            user_id,
        )
        return [dict(b) for b in budgets]


async def claim_budget_alert(user_id: int, region: str, billing_period: str, status: str) -> bool:
    """Atomically reserve one alert for a status during a billing period."""
    if not db.pool:
        return False
    async with db.pool.acquire() as conn:
        result = await conn.fetchval(
            """
            INSERT INTO budget_alerts (user_id, region, billing_period, status)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id, region, billing_period, status) DO NOTHING
            RETURNING id
            """,
            user_id, region, billing_period, status,
        )
        return result is not None


async def release_budget_alert(user_id: int, region: str, billing_period: str, status: str) -> None:
    """Release a reserved alert when delivery fails so it can be retried."""
    if not db.pool:
        return
    async with db.pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM budget_alerts WHERE user_id = $1 AND region = $2 AND billing_period = $3 AND status = $4",
            user_id, region, billing_period, status,
        )


# Analysis queries
async def create_analysis(
    user_id: int,
    region: str,
    resources_scanned: int,
    issues_found: int,
    estimated_savings: float,
    cost_summary: Dict[str, Any],
    analysis_result: Dict[str, Any],
) -> int:
    """Store an analysis result."""
    if not db.pool:
        raise RuntimeError("Database not connected")

    async with db.pool.acquire() as conn:
        analysis_id = await conn.fetchval(
            """
            INSERT INTO analyses (user_id, region, resources_scanned, issues_found, estimated_savings, cost_summary, analysis_result, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, 'completed')
            RETURNING id
            """,
            user_id,
            region,
            resources_scanned,
            issues_found,
            estimated_savings,
            json.dumps(cost_summary),
            json.dumps(analysis_result),
        )
        return analysis_id


async def get_analyses(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve past analyses for a user."""
    if not db.pool:
        raise RuntimeError("Database not connected")

    async with db.pool.acquire() as conn:
        analyses = await conn.fetch(
            """
            SELECT id, region, resources_scanned, issues_found, estimated_savings, created_at
            FROM analyses
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            user_id,
            limit,
        )
        return [dict(a) for a in analyses]


async def get_analysis(user_id: int, analysis_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a specific analysis."""
    if not db.pool:
        raise RuntimeError("Database not connected")

    async with db.pool.acquire() as conn:
        analysis = await conn.fetchrow(
            """
            SELECT id, user_id, region, resources_scanned, issues_found, estimated_savings, cost_summary, analysis_result, created_at
            FROM analyses
            WHERE id = $1 AND user_id = $2
            """,
            analysis_id,
            user_id,
        )
        if not analysis:
            return None

        row = dict(analysis)
        # Parse JSONB fields
        if row.get("cost_summary"):
            row["cost_summary"] = json.loads(row["cost_summary"]) if isinstance(row["cost_summary"], str) else row["cost_summary"]
        if row.get("analysis_result"):
            row["analysis_result"] = json.loads(row["analysis_result"]) if isinstance(row["analysis_result"], str) else row["analysis_result"]
        return row


# Cost snapshot queries
async def upsert_cost_snapshot(user_id: int, region: str, snapshot_date, daily_cost: float) -> int:
    """Create or update a daily cost snapshot."""
    if not db.pool:
        raise RuntimeError("Database not connected")

    async with db.pool.acquire() as conn:
        snapshot_id = await conn.fetchval(
            """
            INSERT INTO cost_snapshots (user_id, region, snapshot_date, daily_cost)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id, region, snapshot_date)
            DO UPDATE SET daily_cost = $4, created_at = CURRENT_TIMESTAMP
            RETURNING id
            """,
            user_id,
            region,
            snapshot_date,
            daily_cost,
        )
        return snapshot_id


async def get_cost_snapshots(user_id: int, region: str, days: int = 90) -> List[Dict[str, Any]]:
    """Retrieve cost snapshots for a region over the past N days."""
    if not db.pool:
        raise RuntimeError("Database not connected")

    async with db.pool.acquire() as conn:
        snapshots = await conn.fetch(
            """
            SELECT snapshot_date, daily_cost FROM cost_snapshots
            WHERE user_id = $1 AND region = $2 AND snapshot_date >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY snapshot_date ASC
            """,
            user_id,
            region,
            days,
        )
        return [dict(s) for s in snapshots]
