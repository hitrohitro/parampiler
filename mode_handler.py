"""Mode handling for dual frontend compiler (standard SIE++ and Victorian VCE)."""

from __future__ import annotations

import re
from dataclasses import dataclass


class ModeError(Exception):
    """Raised when mode selection or detection fails."""


@dataclass
class ModeDecision:
    mode: str
    was_auto_detected: bool


class ModeHandler:
    """Detects or validates the input frontend mode."""

    VICTORIAN_HINTS = {
        "pray",
        "whilst",
        "bestow",
        "unto",
        "commence",
        "conclude",
        "thereafter",
        "likewise",
        "reveal",
    }

    def decide_mode(self, text: str, requested_mode: str) -> ModeDecision:
        requested = (requested_mode or "auto").strip().lower()
        if requested not in {"auto", "standard", "victorian"}:
            raise ModeError(
                f"Unsupported mode '{requested_mode}'. Use auto, standard, or victorian."
            )

        if requested == "auto":
            return ModeDecision(mode=self._detect_mode(text), was_auto_detected=True)

        return ModeDecision(mode=requested, was_auto_detected=False)

    def _detect_mode(self, text: str) -> str:
        lowered = text.lower()
        for hint in self.VICTORIAN_HINTS:
            if re.search(rf"\b{re.escape(hint)}\b", lowered):
                return "victorian"
        return "standard"
