import argparse
import datetime as dt
from pathlib import Path


HEADER_PREFIX = "# Chat Log"


def insert_entry(text: str, entry: str, today: str) -> str:
    lines = text.splitlines()

    # Find first section heading (## YYYY-MM-DD)
    first_section_idx = None
    for i, line in enumerate(lines):
        if line.startswith("## "):
            first_section_idx = i
            break

    if first_section_idx is None:
        # No sections yet; create header if missing, then add today's section
        preamble = [HEADER_PREFIX, "", "- 채팅/작업 로그 누적 기록. 최신 항목이 위에 오도록 유지.", "- 파일명은 `Chat-Log.md`로 고정.", "", f"## {today}", "", entry, ""]
        return "\n".join(preamble) + "\n"

    # Check if the first section is today
    if lines[first_section_idx].strip() == f"## {today}":
        # Insert entry right after the section header and an optional blank line
        insert_at = first_section_idx + 1
        # Skip a single blank line if present
        if insert_at < len(lines) and lines[insert_at].strip() == "":
            insert_at += 1
        new_lines = lines[:insert_at] + [entry, ""] + lines[insert_at:]
        return "\n".join(new_lines) + "\n"
    else:
        # Create a new section for today above the first existing section
        new_section = [f"## {today}", "", entry, ""]
        new_lines = lines[:first_section_idx] + new_section + lines[first_section_idx:]
        return "\n".join(new_lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Append a VK merge log entry to docs/Chat-Log.md (top-most, grouped by date)")
    ap.add_argument("--pr-number", required=True)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--file", default="docs/Chat-Log.md")
    args = ap.parse_args()

    today = dt.datetime.now(dt.timezone.utc).astimezone().date().isoformat()
    entry = f"- VK Done: {args.branch} merged via PR #{args.pr_number}: {args.title}\n  - {args.url}"

    p = Path(args.file)
    text = p.read_text(encoding="utf-8") if p.exists() else HEADER_PREFIX + "\n\n"
    updated = insert_entry(text, entry, today)
    if updated != text:
        p.write_text(updated, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

