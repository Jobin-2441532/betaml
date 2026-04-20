from dataclasses import dataclass
from enum import Enum
from config.settings import settings

class ConfidenceAction(str, Enum):
    AUTO_ASSIGN     = "auto_assign"      # > 0.85 — silent
    SHOW_EDITABLE   = "show_editable"    # 0.65–0.85 — show with edit
    SUGGEST_OPTIONS = "suggest"          # 0.45–0.65 — show options
    ASK_USER        = "ask_user"         # < 0.45 — must ask

@dataclass
class ConfidenceScore:
    raw: float
    adjusted: float
    action: ConfidenceAction
    display_label: str

class ConfidenceEngine:
    def score(self, raw: float, parse_confidence=1.0,
              user_profile_match=False, location_match=False,
              is_recurring=False, is_known_merchant=False) -> ConfidenceScore:
        adj = raw
        if is_known_merchant:   adj = min(adj + 0.10, 0.99)
        if is_recurring:        adj = min(adj + 0.05, 0.99)
        if user_profile_match:  adj = min(adj + 0.03, 0.99)
        if location_match:      adj = min(adj + 0.04, 0.99)
        if parse_confidence < 0.8: adj = max(adj - 0.10, 0.0)
        adj = round(adj, 4)
        action = self._resolve(adj)
        return ConfidenceScore(
            raw=round(raw, 4), adjusted=adj,
            action=action, display_label=self._label(action),
        )

    @staticmethod
    def _resolve(score: float) -> ConfidenceAction:
        if score >= settings.confidence_auto:    return ConfidenceAction.AUTO_ASSIGN
        if score >= settings.confidence_show:    return ConfidenceAction.SHOW_EDITABLE
        if score >= settings.confidence_suggest: return ConfidenceAction.SUGGEST_OPTIONS
        return ConfidenceAction.ASK_USER

    @staticmethod
    def _label(action: ConfidenceAction) -> str:
        return {
            ConfidenceAction.AUTO_ASSIGN:     "Auto-assigned",
            ConfidenceAction.SHOW_EDITABLE:   "Review suggested",
            ConfidenceAction.SUGGEST_OPTIONS: "Options shown",
            ConfidenceAction.ASK_USER:        "User input required",
        }[action]