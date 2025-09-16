from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable


@dataclass(frozen=True)
class PopupRules:
    allowed_categories: tuple[str, ...] = (
        "POPUP",
        "POPUP_STORE",
        "POPUP_EVENT",
    )
    keyword_ko: tuple[str, ...] = ("팝업",)
    keyword_en: tuple[str, ...] = ("popup",)
    keyword_ja: tuple[str, ...] = ("ポップアップ",)
    max_days_heuristic: int = 90

    def match_category(self, category: str | None) -> bool:
        if not category:
            return False
        return category.upper() in self.allowed_categories

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

