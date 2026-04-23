"""Control registry — single source of truth for which controls to run."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .base import BaseControl
from .citation_enforcer import CitationEnforcer
from .human_in_loop import HumanInLoopTrigger
from .jailbreak_detector import JailbreakDetector
from .pii_filter import PIIFilter


@dataclass
class ControlRegistry:
    controls: list[BaseControl]

    @classmethod
    def load_default(cls) -> "ControlRegistry":
        return cls(
            controls=[
                PIIFilter(),
                JailbreakDetector(),
                CitationEnforcer(),
                HumanInLoopTrigger(),
            ]
        )

    def all(self) -> list[BaseControl]:
        return list(self.controls)

    def get(self, control_ids: Iterable[str]) -> list[BaseControl]:
        wanted = set(control_ids)
        return [c for c in self.controls if c.control_id in wanted]
