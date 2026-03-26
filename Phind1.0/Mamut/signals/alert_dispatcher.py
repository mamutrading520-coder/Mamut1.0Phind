"""
Alert dispatcher for Mamut.

Persists signals to the database and optionally POSTs them to a
configured webhook URL (e.g. Telegram bot, Discord webhook).

NOTE: This is a stub implementation.
"""
from typing import Dict, Any
from datetime import datetime
import httpx
from monitoring.logger import setup_logger
from core.event_bus import Event, get_event_bus
from storage.sqlite_store import SQLiteStore
from config.settings import Settings

logger = setup_logger("AlertDispatcher")


class AlertDispatcher:
    """Dispatches signals to configured alert channels."""

    def __init__(self, store: SQLiteStore, settings: Settings):
        self.store = store
        self.settings = settings
        self.event_bus = get_event_bus()
        self.dispatched_count = 0
        self.failed_count = 0
        self._http_client = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=10)
        return self._http_client

    async def _send_webhook(self, signal_data: Dict[str, Any]) -> bool:
        """Send signal to configured webhook URL (if any)."""
        webhook_url = self.settings.webhook_url
        if not webhook_url:
            return True  # No webhook configured – skip silently

        try:
            client = await self._get_http_client()
            resp = await client.post(webhook_url, json=signal_data)
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"Webhook delivery failed: {e}")
            return False

    async def dispatch_and_emit(self, event: Event) -> bool:
        """
        Persist signal to DB, send webhook and emit AlertDispatched.

        Args:
            event: SignalGenerated event

        Returns:
            True if dispatched, False otherwise
        """
        try:
            signal_data = event.data
            mint = signal_data.get("mint")
            symbol = signal_data.get("symbol", "UNKNOWN")

            # Persist to DB
            self.store.create_signal(signal_data)

            # Dispatch webhook
            await self._send_webhook(signal_data)

            # Emit AlertDispatched
            dispatched_event = Event(
                event_type="AlertDispatched",
                data=signal_data,
                source="AlertDispatcher",
                timestamp=datetime.utcnow(),
            )
            await self.event_bus.emit(dispatched_event)

            self.dispatched_count += 1
            logger.info(
                f"AlertDispatched: {symbol} ({mint[:8] if mint else '?'}...) "
                f"signal_id={signal_data.get('signal_id', 'N/A')}"
            )
            return True

        except Exception as e:
            logger.error(f"Error in dispatch_and_emit: {e}")
            self.failed_count += 1
            return False

    async def close(self) -> None:
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()

    def get_stats(self) -> Dict[str, Any]:
        return {
            "dispatched_count": self.dispatched_count,
            "failed_count": self.failed_count,
        }
