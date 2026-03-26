"""
SQLite storage layer for Mamut.

NOTE: This is a stub implementation. The full implementation requires
defining ORM models for Token, Signal, CreatorProfile and implementing
all CRUD operations against a SQLite database (via SQLAlchemy or
aiosqlite). The interface below matches what the rest of the codebase
already expects.
"""
import sqlite3
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field
from monitoring.logger import setup_logger

logger = setup_logger("SQLiteStore")


# ---------------------------------------------------------------------------
# Data-transfer objects (lightweight stand-ins for ORM models)
# ---------------------------------------------------------------------------

@dataclass
class TokenRecord:
    mint: str
    name: Optional[str] = None
    symbol: Optional[str] = None
    risk_level: str = "UNKNOWN"
    passed_filters: bool = False
    rejection_reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SignalRecord:
    signal_id: str
    mint: str
    symbol: str
    signal_type: str
    score: float
    confidence: float
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CreatorProfileRecord:
    creator: str
    total_tokens_created: int = 0
    # Alias kept for backward-compat with trash_filter_engine.py
    total_tokens: int = 0
    failed_tokens: int = 0
    successful_tokens: int = 0
    average_score: float = 0.0
    wallet_age_days: int = 0
    risk_level: str = "UNKNOWN"
    is_trusted: bool = False
    is_blacklisted: bool = False
    last_token_date: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

class SQLiteStore:
    """SQLite-backed persistence layer for Mamut."""

    def __init__(self, settings):
        self.settings = settings
        db_path = getattr(settings, "database_url", "sqlite:///./mamut.db")
        # Strip SQLAlchemy prefix if present
        self.db_path = db_path.replace("sqlite:///", "")
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self) -> None:
        """Create tables if they do not exist."""
        try:
            conn = self._get_conn()
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS tokens (
                    mint TEXT PRIMARY KEY,
                    name TEXT,
                    symbol TEXT,
                    risk_level TEXT DEFAULT 'UNKNOWN',
                    passed_filters INTEGER DEFAULT 0,
                    rejection_reason TEXT,
                    created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS signals (
                    signal_id TEXT PRIMARY KEY,
                    mint TEXT,
                    symbol TEXT,
                    signal_type TEXT,
                    score REAL,
                    confidence REAL,
                    created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS creator_profiles (
                    creator TEXT PRIMARY KEY,
                    total_tokens_created INTEGER DEFAULT 0,
                    failed_tokens INTEGER DEFAULT 0,
                    successful_tokens INTEGER DEFAULT 0,
                    average_score REAL DEFAULT 0.0,
                    wallet_age_days INTEGER DEFAULT 0,
                    risk_level TEXT DEFAULT 'UNKNOWN',
                    is_trusted INTEGER DEFAULT 0,
                    is_blacklisted INTEGER DEFAULT 0,
                    last_token_date TEXT
                );
            """)
            conn.commit()
            logger.debug("Database initialised")
        except Exception as e:
            logger.error(f"Error initialising database: {e}")

    # ------------------------------------------------------------------
    # Token CRUD
    # ------------------------------------------------------------------

    def create_token(self, token_data: Dict[str, Any]) -> bool:
        try:
            conn = self._get_conn()
            conn.execute(
                """INSERT OR IGNORE INTO tokens
                   (mint, name, symbol, risk_level, passed_filters, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    token_data.get("mint"),
                    token_data.get("name"),
                    token_data.get("symbol"),
                    token_data.get("risk_level", "UNKNOWN"),
                    int(token_data.get("passed_filters", False)),
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error creating token: {e}")
            return False

    def get_token(self, mint: str) -> Optional[TokenRecord]:
        try:
            conn = self._get_conn()
            row = conn.execute("SELECT * FROM tokens WHERE mint = ?", (mint,)).fetchone()
            if row:
                return TokenRecord(
                    mint=row["mint"],
                    name=row["name"],
                    symbol=row["symbol"],
                    risk_level=row["risk_level"],
                    passed_filters=bool(row["passed_filters"]),
                    rejection_reason=row["rejection_reason"],
                )
            return None
        except Exception as e:
            logger.error(f"Error fetching token: {e}")
            return None

    def update_token(self, token: TokenRecord) -> bool:
        try:
            conn = self._get_conn()
            conn.execute(
                """UPDATE tokens SET name=?, symbol=?, risk_level=?,
                   passed_filters=?, rejection_reason=? WHERE mint=?""",
                (
                    token.name,
                    token.symbol,
                    token.risk_level,
                    int(token.passed_filters),
                    token.rejection_reason,
                    token.mint,
                ),
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating token: {e}")
            return False

    # ------------------------------------------------------------------
    # Signal CRUD
    # ------------------------------------------------------------------

    def create_signal(self, signal_data: Dict[str, Any]) -> bool:
        try:
            conn = self._get_conn()
            conn.execute(
                """INSERT OR IGNORE INTO signals
                   (signal_id, mint, symbol, signal_type, score, confidence, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    signal_data.get("signal_id"),
                    signal_data.get("mint"),
                    signal_data.get("symbol"),
                    signal_data.get("signal_type"),
                    signal_data.get("score", 0.0),
                    signal_data.get("confidence", 0.0),
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error creating signal: {e}")
            return False

    # ------------------------------------------------------------------
    # Creator profile CRUD
    # ------------------------------------------------------------------

    def get_creator_profile(self, creator: str) -> Optional[CreatorProfileRecord]:
        try:
            conn = self._get_conn()
            row = conn.execute(
                "SELECT * FROM creator_profiles WHERE creator = ?", (creator,)
            ).fetchone()
            if row:
                total = row["total_tokens_created"]
                return CreatorProfileRecord(
                    creator=row["creator"],
                    total_tokens_created=total,
                    total_tokens=total,  # backward-compat alias
                    failed_tokens=row["failed_tokens"],
                    successful_tokens=row["successful_tokens"],
                    average_score=row["average_score"],
                    wallet_age_days=row["wallet_age_days"],
                    risk_level=row["risk_level"],
                    is_trusted=bool(row["is_trusted"]),
                    is_blacklisted=bool(row["is_blacklisted"]),
                )
            return None
        except Exception as e:
            logger.error(f"Error fetching creator profile: {e}")
            return None

    def update_creator_profile(self, creator: str, updates: Dict[str, Any]) -> bool:
        try:
            conn = self._get_conn()
            # Upsert pattern
            existing = self.get_creator_profile(creator)
            if existing:
                conn.execute(
                    """UPDATE creator_profiles
                       SET total_tokens_created=?, wallet_age_days=?,
                           risk_level=?, last_token_date=?
                       WHERE creator=?""",
                    (
                        updates.get("total_tokens_created", existing.total_tokens_created),
                        updates.get("wallet_age_days", existing.wallet_age_days),
                        updates.get("risk_level", existing.risk_level),
                        updates.get("last_token_date", datetime.utcnow()).isoformat()
                        if isinstance(updates.get("last_token_date"), datetime)
                        else updates.get("last_token_date", datetime.utcnow().isoformat()),
                        creator,
                    ),
                )
            else:
                conn.execute(
                    """INSERT INTO creator_profiles
                       (creator, total_tokens_created, wallet_age_days, risk_level, last_token_date)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        creator,
                        updates.get("total_tokens_created", 0),
                        updates.get("wallet_age_days", 0),
                        updates.get("risk_level", "UNKNOWN"),
                        updates.get("last_token_date", datetime.utcnow()).isoformat()
                        if isinstance(updates.get("last_token_date"), datetime)
                        else updates.get("last_token_date", datetime.utcnow().isoformat()),
                    ),
                )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating creator profile: {e}")
            return False

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_statistics(self) -> Dict[str, Any]:
        try:
            conn = self._get_conn()
            total_tokens = conn.execute("SELECT COUNT(*) FROM tokens").fetchone()[0]
            total_signals = conn.execute("SELECT COUNT(*) FROM signals").fetchone()[0]

            risk_rows = conn.execute(
                "SELECT risk_level, COUNT(*) as cnt FROM tokens GROUP BY risk_level"
            ).fetchall()
            tokens_by_risk = {row["risk_level"]: row["cnt"] for row in risk_rows}

            sig_rows = conn.execute(
                "SELECT signal_type, COUNT(*) as cnt FROM signals GROUP BY signal_type"
            ).fetchall()
            signals_by_type = {row["signal_type"]: row["cnt"] for row in sig_rows}

            return {
                "total_tokens": total_tokens,
                "total_signals": total_signals,
                "tokens_by_risk": tokens_by_risk,
                "signals_by_type": signals_by_type,
            }
        except Exception as e:
            logger.error(f"Error fetching statistics: {e}")
            return {}

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
