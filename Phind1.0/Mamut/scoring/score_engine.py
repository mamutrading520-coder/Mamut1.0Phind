"""
Token score engine for Mamut.

NOTE: This is a stub implementation. The full implementation should
compute a composite score from the analysis sub-scores (authority risk,
creator risk, concentration risk, flow score, momentum score) and emit
a ScoreCalculated event on the event bus.
"""
from typing import Dict, Any
from datetime import datetime
from monitoring.logger import setup_logger
from core.event_bus import Event, get_event_bus

logger = setup_logger("ScoreEngine")


class ScoreEngine:
    """Calculates composite token scores and emits ScoreCalculated events."""

    def __init__(self):
        self.event_bus = get_event_bus()
        self.scored_count = 0
        self.failed_count = 0

    def _compute_score(self, token_data: Dict[str, Any]) -> float:
        """
        Compute a weighted composite score from available sub-scores.

        Sub-score weights (can be tuned):
          - flow_score         30 %
          - momentum_score     20 %
          - authority_risk     20 % (inverted)
          - creator_risk       15 % (inverted)
          - concentration_risk 15 % (inverted)
        """
        try:
            flow_score = float(token_data.get("flow_score", 50.0))
            momentum_score = float(token_data.get("momentum_score", 50.0))
            authority_risk = float(token_data.get("authority_risk_score", 50.0))
            creator_risk = float(token_data.get("creator_risk_score", 50.0))
            concentration_risk = float(token_data.get("concentration_risk_score", 50.0))

            score = (
                flow_score * 0.30
                + momentum_score * 0.20
                + (100.0 - authority_risk) * 0.20
                + (100.0 - creator_risk) * 0.15
                + (100.0 - concentration_risk) * 0.15
            )
            return max(0.0, min(100.0, score))
        except Exception as e:
            logger.error(f"Error computing score: {e}")
            return 50.0

    async def score_and_emit(self, event: Event) -> bool:
        """
        Compute score for the token in *event* and emit ScoreCalculated.

        Args:
            event: TokenPassed event

        Returns:
            True if scored and emitted successfully, False otherwise
        """
        try:
            token_data = event.data
            mint = token_data.get("mint")
            symbol = token_data.get("symbol", "UNKNOWN")

            final_score = self._compute_score(token_data)

            score_event = Event(
                event_type="ScoreCalculated",
                data={
                    **token_data,
                    "final_score": final_score,
                },
                source="ScoreEngine",
                timestamp=datetime.utcnow(),
            )

            await self.event_bus.emit(score_event)
            self.scored_count += 1
            logger.debug(f"ScoreCalculated: {symbol} ({mint[:8] if mint else '?'}...) = {final_score:.2f}")
            return True

        except Exception as e:
            logger.error(f"Error in score_and_emit: {e}")
            self.failed_count += 1
            return False

    def get_stats(self) -> Dict[str, Any]:
        return {
            "scored_count": self.scored_count,
            "failed_count": self.failed_count,
        }
