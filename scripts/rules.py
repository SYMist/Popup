from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from typing import Iterable


@dataclass(frozen=True)
class PopupRules:
    """Rules to determine whether a Festa is a popup event.

    Category allowlist uses normalized tokens so that variants like
    "POP-UP", "POP UP", "popup_event" all resolve to canonical forms
    (e.g., "POPUP", "POPUPEVENT").
    """

    # Store normalized category tokens (letters only, uppercased)
    allowed_categories: tuple[str, ...] = (
        # Common variants observed or anticipated
        "POPUP",        # POP-UP / POPUP / POP UP
        "POPUPEVENT",   # POPUP_EVENT / POP-UP EVENT
        "POPUPSTORE",   # POPUP_STORE
    )
    keyword_ko: tuple[str, ...] = ("팝업",)
    keyword_en: tuple[str, ...] = ("popup",)
    keyword_ja: tuple[str, ...] = ("ポップアップ",)
    max_days_heuristic: int = 90

    def _normalize_category(self, category: str | None) -> str:
        if not category:
            return ""
        # Keep only letters, uppercase; collapse delimiters like '-'/'_'/' '
        return re.sub(r"[^A-Z]", "", category.upper())

    def match_category(self, category: str | None) -> bool:
        token = self._normalize_category(category)
        if not token:
            return False
        return token in self.allowed_categories

    def match_keywords(self, titles: Iterable[str]) -> bool:
        kws = set(self.keyword_ko + self.keyword_en + self.keyword_ja)
        for t in titles:
            if not t:
                continue
            tl = t.lower()
            for kw in kws:
                if kw.lower() in tl:
                    return True
        return False

    def match_duration(self, start: date | None, end: date | None) -> bool:
        if not (start and end):
            return False
        delta = (end - start).days
        if delta < 0:
            return False
        return delta <= self.max_days_heuristic
