from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from typing import Iterable, List, Tuple, Dict, Any


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
    # Expanded keyword lists (common variants)
    keyword_ko: tuple[str, ...] = (
        "팝업",
        "팝업스토어",
        "팝업 스토어",
        "팝업샵",
        "팝업 샵",
        "팝업전",
        "팝업 전",
    )
    keyword_en: tuple[str, ...] = (
        "popup",
        "pop-up",
        "pop up",
        "popup store",
        "popup shop",
        "pop-up store",
        "pop-up shop",
        "popup event",
        "pop-up event",
    )
    keyword_ja: tuple[str, ...] = (
        "ポップアップ",
        "ポップアップストア",
        "ポップアップショップ",
        "ポップアップ イベント",
    )
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

    def find_keyword_hits(self, titles: Iterable[str]) -> List[str]:
        hits: List[str] = []
        kws = tuple({*(k.lower() for k in (self.keyword_ko + self.keyword_en + self.keyword_ja))})
        for t in titles:
            if not t:
                continue
            tl = t.lower()
            for kw in kws:
                if kw and kw in tl:
                    hits.append(kw)
        # De-duplicate preserving order
        seen = set()
        uniq: List[str] = []
        for h in hits:
            if h not in seen:
                seen.add(h)
                uniq.append(h)
        return uniq

    def match_keywords(self, titles: Iterable[str]) -> bool:
        return len(self.find_keyword_hits(titles)) > 0

    def match_duration(self, start: date | None, end: date | None) -> bool:
        if not (start and end):
            return False
        delta = (end - start).days
        if delta < 0:
            return False
        return delta <= self.max_days_heuristic

    def classify(
        self,
        *,
        category: str | None,
        titles: Iterable[str],
        start: date | None,
        end: date | None,
    ) -> Tuple[bool, Dict[str, Any]]:
        reasons: List[str] = []
        details: Dict[str, Any] = {}

        cat_ok = self.match_category(category)
        if cat_ok:
            reasons.append("category")
            details["category"] = category

        kw_hits = self.find_keyword_hits(titles)
        kw_ok = len(kw_hits) > 0
        if kw_ok:
            reasons.append("keyword")
            details["keywordHits"] = kw_hits

        dur_ok = self.match_duration(start, end)
        if dur_ok:
            reasons.append("duration")
            if start and end:
                details["durationDays"] = (end - start).days

        # Decision: category alone is sufficient. Otherwise require (keyword AND duration).
        is_popup = cat_ok or (kw_ok and dur_ok)
        details["rule"] = "|".join(reasons) if reasons else ""
        return is_popup, details
