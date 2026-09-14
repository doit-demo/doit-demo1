import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

KEYWORDS = {
    "태양광": 25,
    "신재생에너지": 18,
    "영농형태양광": 25,
    "햇빛소득": 25,
    "발전사업": 15,
    "공유재산": 12,
    "유휴부지": 12,
    "에너지": 8,
    "RE100": 10,
    "REC": 6,
    "RPS": 6,
    "농촌": 8,
    "임대": 6,
}

SOURCES = [
    {
        "name": "Google News RSS",
        "url": "https://news.google.com/rss/search?q=%ED%83%9C%EC%96%91%EA%B4%91%20%EA%B3%B5%EA%B3%A0&hl=ko&gl=KR&ceid=KR:ko",
        "type": "rss",
    },
    {
        "name": "Google News RSS - 신재생",
        "url": "https://news.google.com/rss/search?q=%EC%8B%A0%EC%9E%AC%EC%83%9D%EC%97%90%EB%84%88%EC%A7%80%20%EA%B3%B5%EA%B3%A0&hl=ko&gl=KR&ceid=KR:ko",
        "type": "rss",
    },
    {
        "name": "Google News RSS - 영농형",
        "url": "https://news.google.com/rss/search?q=%EC%98%81%EB%86%8D%ED%98%95%ED%83%9C%EC%96%91%EA%B4%91&hl=ko&gl=KR&ceid=KR:ko",
        "type": "rss",
    },
]

OUT = Path("data/notices.json")
STATUS = Path("monitor-status.json")


def fetch(url: str, timeout: int = 20) -> str:
    req = Request(url, headers={"User-Agent": "DSOLAR-Solar-Notice-Monitor/1.0"})
    with urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


def parse_rss(xml: str, source_name: str, source_url: str):
    items = []
    entries = re.findall(r"<item>(.*?)</item>", xml, flags=re.S | re.I)
    for raw in entries:
        title = clean(re.search(r"<title.*?>(.*?)</title>", raw, flags=re.S | re.I).group(1)) if re.search(r"<title.*?>(.*?)</title>", raw, flags=re.S | re.I) else ""
        link = re.search(r"<link.*?>(.*?)</link>", raw, flags=re.S | re.I)
        pub = re.search(r"<pubDate.*?>(.*?)</pubDate>", raw, flags=re.S | re.I)
        desc = re.search(r"<description.*?>(.*?)</description>", raw, flags=re.S | re.I)
        if not title:
            continue
        text = f"{title} {clean(desc.group(1) if desc else '')}"
        score = sum(weight for key, weight in KEYWORDS.items() if key.lower() in text.lower())
        if score < 15:
            continue
        items.append({
            "title": title,
            "description": clean(desc.group(1) if desc else "")[:500],
            "url": (link.group(1).strip() if link else source_url),
            "source": source_name,
            "published": (pub.group(1).strip() if pub else ""),
            "score": min(score, 100),
            "matched_keywords": [k for k in KEYWORDS if k.lower() in text.lower()],
            "collected_at": datetime.now(timezone.utc).isoformat(),
        })
    return items


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if OUT.exists():
        try:
            existing = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:
            existing = []
    by_url = {x.get("url"): x for x in existing if x.get("url")}
    errors = []
    collected = 0

    for source in SOURCES:
        try:
            xml = fetch(source["url"])
            rows = parse_rss(xml, source["name"], source["url"])
            collected += len(rows)
            for row in rows:
                by_url[row["url"]] = row
            time.sleep(0.5)
        except Exception as e:
            errors.append({"source": source["name"], "error": str(e)})

    rows = list(by_url.values())
    rows.sort(key=lambda x: (x.get("score", 0), x.get("collected_at", "")), reverse=True)
    OUT.write_text(json.dumps(rows[:500], ensure_ascii=False, indent=2), encoding="utf-8")

    status = {
        "status": "ok" if not errors else "partial",
        "last_run": datetime.now(timezone.utc).isoformat(),
        "collector": "live-rss",
        "sources": len(SOURCES),
        "collected_this_run": collected,
        "stored_total": len(rows[:500]),
        "errors": errors,
    }
    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
