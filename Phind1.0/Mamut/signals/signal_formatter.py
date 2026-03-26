"""
Signal formatter for Mamut.

Formats raw signal data into human-readable messages suitable for
Telegram, Discord, or webhook delivery.

NOTE: This is a stub implementation.
"""
from typing import Dict, Any
from monitoring.logger import setup_logger

logger = setup_logger("SignalFormatter")


class SignalFormatter:
    """Formats signal data for display and dispatch."""

    def format(self, signal_data: Dict[str, Any]) -> str:
        """
        Format a signal dictionary into a readable text message.

        Args:
            signal_data: Signal data dictionary

        Returns:
            Formatted message string
        """
        try:
            symbol = signal_data.get("symbol", "UNKNOWN")
            mint = signal_data.get("mint", "")
            signal_type = signal_data.get("signal_type", "UNKNOWN")
            score = float(signal_data.get("score", 0.0))
            confidence = float(signal_data.get("confidence", 0.0))
            generated_at = signal_data.get("generated_at", "")

            lines = [
                f"🚨 MAMUT SIGNAL [{signal_type}]",
                f"Token:      {symbol}",
                f"Mint:       {mint[:16]}..." if mint else "Mint:       N/A",
                f"Score:      {score:.2f} / 100",
                f"Confidence: {confidence * 100:.1f} %",
                f"Time:       {generated_at}",
            ]

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Error formatting signal: {e}")
            return f"Signal for {signal_data.get('symbol', 'UNKNOWN')} (format error)"
