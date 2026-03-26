"""
Signal engine for Mamut.

Generates trading signals (EARLY, CONFIRMATION, ABANDON) based on the
decision made by DecisionMapper and emits SignalGenerated events.

NOTE: This is a stub implementation.
"""
import uuid
from typing import Dict, Any
from datetime import datetime
from monitoring.logger import setup_logger
from core.event_bus import Event, get_event_bus
from config.settings import Settings
from config.thresholds import SIGNAL_THRESHOLDS

logger = setup_logger("SignalEngine")


class SignalEngine:
    """Generates trading signals and emits SignalGenerated events."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.event_bus = get_event_bus()
        self.generated_count = 0
        self.failed_count = 0

    def _build_signal(self, token_data: Dict[str, Any], signal_type: str) -> Dict[str, Any]:
        score = float(token_data.get("final_score", 0.0))
        min_confidence_score = SIGNAL_THRESHOLDS.get("min_early_score", 70)
        confidence = min(1.0, score / 100.0) if score > 0 else 0.0

        return {
            **token_data,
            "signal_id": str(uuid.uuid4()),
            "signal_type": signal_type,
            "score": score,
            "confidence": round(confidence, 4),
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def generate_early_and_emit(self, event: Event) -> bool:
        """
        Generate an EARLY signal from a DecisionMade event.

        Args:
            event: DecisionMade event

        Returns:
            True if signal generated and emitted, False otherwise
        """
        try:
            token_data = event.data
            decision = token_data.get("decision", "")
            mint = token_data.get("mint")
            symbol = token_data.get("symbol", "UNKNOWN")

            signal_type = "EARLY" if decision == "SIGNAL_EARLY" else "MONITOR"
            signal_data = self._build_signal(token_data, signal_type)

            signal_event = Event(
                event_type="SignalGenerated",
                data=signal_data,
                source="SignalEngine",
                timestamp=datetime.utcnow(),
            )

            await self.event_bus.emit(signal_event)
            self.generated_count += 1
            logger.info(
                f"SignalGenerated [{signal_type}]: {symbol} ({mint[:8] if mint else '?'}...) "
                f"score={signal_data['score']:.2f} confidence={signal_data['confidence']:.2f}"
            )
            return True

        except Exception as e:
            logger.error(f"Error in generate_early_and_emit: {e}")
            self.failed_count += 1
            return False

    def get_stats(self) -> Dict[str, Any]:
        return {
            "generated_count": self.generated_count,
            "failed_count": self.failed_count,
        }
