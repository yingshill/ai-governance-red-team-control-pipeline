"""Control registry — single source of truth for which controls to run."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .base import BaseControl
from .citation_enforcer import CitationEnforcer
from .drift_detector import DriftDetector
from .human_in_loop import HumanInLoopTrigger
from .jailbreak_detector import JailbreakDetector
from .pii_filter import PIIFilter


@dataclass
class ControlRegistry:
    """Container for the set of controls active in this environment."""

    controls: list[BaseControl]

    @classmethod
    def load_default(cls) -> "ControlRegistry":
        """Return the default set of controls wired for production."""
        return cls(
            controls=[
                PIIFilter(),
                JailbreakDetector(),
                CitationEnforcer(),
                HumanInLoopTrigger(),
                DriftDetector(),
            ]
        )

    def all(self) -> list[BaseControl]:
        """Return all registered controls."""
        return list(self.controls)

    def get(self, control_ids: Iterable[str]) -> list[BaseControl]:
        """Return controls whose ``control_id`` is in ``control_ids``."""
        wanted = set(control_ids)
        return [c for c in self.controls if c.control_id in wanted]
