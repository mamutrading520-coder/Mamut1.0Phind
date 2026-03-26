"""
Decision mapper for Mamut.

Maps a final score to one of three decisions:
  - SIGNAL_EARLY  (score >= signal_early_min_score)
  - MONITOR       (score >= monitor_min_score)
  - REJECT        (score < reject_max_score)

NOTE: This is a stub implementation.
"""
from typing import Dict, Any
from datetime import datetime
from monitoring.logger import setup_logger
from core.event_bus import Event, get_event_bus
from config.settings import Settings
from config.thresholds import DECISION_THRESHOLDS

logger = setup_logger("DecisionMapper")


class DecisionMapper:
    """Maps token scores to trading decisions and emits DecisionMade events."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.event_bus = get_event_bus()
        self.mapped_count = 0
        self.failed_count = 0

    def _map_decision(self, score: float) -> str:
        signal_min = DECISION_THRESHOLDS.get("signal_early_min_score", 70)
        monitor_min = DECISION_THRESHOLDS.get("monitor_min_score", 50)
        reject_max = DECISION_THRESHOLDS.get("reject_max_score", 30)

        if score >= signal_min:
            return "SIGNAL_EARLY"
        elif score >= monitor_min:
            return "MONITOR"
        elif score < reject_max:
            return "REJECT"
        else:
            return "WATCH"

    async def map_and_emit(self, event: Event) -> bool:
        """
        Map score to decision and emit DecisionMade.

        Args:
            event: ScoreCalculated event

        Returns:
            True if mapped and emitted, False otherwise
        """
        try:
            token_data = event.data
            mint = token_data.get("mint")
            symbol = token_data.get("symbol", "UNKNOWN")
            score = float(token_data.get("final_score", 0.0))

            decision = self._map_decision(score)

            decision_event = Event(
                event_type="DecisionMade",
                data={
                    **token_data,
                    "decision": decision,
                },
                source="DecisionMapper",
                timestamp=datetime.utcnow(),
            )

            await self.event_bus.emit(decision_event)
            self.mapped_count += 1
            logger.debug(
                f"DecisionMade: {symbol} ({mint[:8] if mint else '?'}...) = {decision} (score={score:.2f})"
            )
            return True

        except Exception as e:
            logger.error(f"Error in map_and_emit: {e}")
            self.failed_count += 1
            return False

    def get_stats(self) -> Dict[str, Any]:
        return {
            "mapped_count": self.mapped_count,
            "failed_count": self.failed_count,
        }
