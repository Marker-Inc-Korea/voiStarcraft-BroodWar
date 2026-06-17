from __future__ import annotations

import json
from pathlib import Path

from .models import IntentState


class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> IntentState:
        if not self.path.exists():
            return IntentState()
        return IntentState.from_dict(json.loads(self.path.read_text(encoding="utf-8")))

    def save(self, state: IntentState) -> None:
        tmp = self.path.with_suffix(f"{self.path.suffix}.tmp")
        tmp.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self.path)
