import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

KEYWORDS = {
    "태양광": 30,
    "신재생에너지": 18,
    "영농형태양광": 30,
    "햇빛소득": 30,
    "발전사업": 16,
    "공유재산": 14,
    "유휴부지": 14,
    "에너지": 8,
    "RE100": 10,
    "REC": 6,
    "RPS": 6,
    "농촌": 8,
    "임대": 6,
}

# 공개 RSS부터 안정적으로 운용. 공식 API/페이지는 별도 adapter로 추가한다.
SOURCES = [
    {"name":"Google News · 태양광 공고", "url":"https://news.google.com/rss/search?q=%ED%83%9C%EC%96%91%EA%B4%91%20%EA%B3%B5%EA%B3%A0&hl=ko&gl=KR&ceid=KR:ko"},
    {"name":"Google News · 신재생에너지 공고", "url":"https://news.google.com/rss/search?q=%EC%8B%A0%EC%9E%AC%EC%83%9D%EC%97%90%EB%84%88%EC%A7%80%20%EA%B3%B5%EA%B3%A0&hl=ko&gl=KR&ceid=KR:ko"},
    {"name":"Google News · 영농형태양광", "url":"https://news.google.com/rss/search?q=%EC%98%81%EB%86%8D%ED%98%95%ED%83%9C%EC%96%91%EA%B4%91&hl=ko&gl=KR&ceid=KR:ko"},
    {"name":"Google News · 햇빛소득", "url":"https://news.google.com/rss/search?q=%ED%96%87%EB%B9%9B%EC%86%8C%EB%93%9D%20%EA%B3%B5%EA%B3%A0&hl=ko&gl=KR&ceid=KR:ko"},
    {"name":"Google News · 발전사업 공고", "url":"https://news.google.com/rss/search?q=%EB%B0%9C%EC%A0%84%EC%82%AC%EC%97%85%20%EA%B3%B5%EA%B3%A0%20%ED%83%9C%EC%96%91%EA%B4%91&hl=ko&gl=KR&ceid=KR:ko"},
    {"name":"Google News · 공유재산 태양광", "url":"https://news.google.com/rss/search?q=%EA%B3%B5%EC%9C%A0%EC%9E%AC%EC%82%B0%20%ED%83%9C%EC%96%91%EA%B4%91&hl=ko&gl=KR&ceid=KR:ko"},
]

OUT = Path("data/notices.json")
STATUS = Path("monitor-status.json")
MAX_ROWS = 1000


def fetch(url: str, timeout: int = 25) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 DSOLAR-Notice-Monitor/1.0"})
    with urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def clean(text: str) -> str:
    text = re.sub(r"<!\[CDATA\[|\]\]>", "", text or "")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()


def tag_score(text: str):
    low = text.lower()
    matched = [k for k in KEYWORDS if k.lower() in low]
    score = min(100, sum(KEYWORDS[k] for k in matched))
    if "태양광" in matched and any(k in matched for k in ("발전사업", "영농형태양광", "햇빛소득", "공유재산")):
        score = min(100, score + 8)
    return score, matched


def parse_rss(xml: str, source_name: str, source_url: str):
    rows = []
    for raw in re.findall(r"<item>(.*?)</item>", xml, flags=re.S | re.I):
        def pick(tag):
            m = re.search(fr"<{tag}(?:\s[^>]*)?>(.*?)</{tag}>", raw, flags=re.S | re.I)
            return clean(m.group(1)) if m else ""

        title, link, pub, desc = pick("title"), pick("link"), pick("pubDate"), pick("description")
        if not title:
            continue
        text = f"{title} {desc}"
        score, matched = tag_score(text)
        if score < 15:
            continue
        rows.append({
            "title": title,
            "description": desc[:700],
            "url": link or source_url,
            "source": source_name,
            "published": pub,
            "score": score,
            "matched_keywords": matched,
            "collected_at": datetime.now(timezone.utc).isoformat(),
        })
    return rows


def key_for(row):
    return row.get("url") or (row.get("source", ""), row.get("title", ""), row.get("published", ""))


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
    except Exception:
        existing = []

    by_key = {key_for(x): x for x in existing}
    errors, source_status = [], []
    collected = 0

    for source in SOURCES:
        checked_at = datetime.now(timezone.utc).isoformat()
        try:
            rows = parse_rss(fetch(source["url"]), source["name"], source["url"])
            for row in rows:
                by_key[key_for(row)] = row
            collected += len(rows)
            source_status.append({"name": source["name"], "status": "ok", "items": len(rows), "checked_at": checked_at})
        except Exception as e:
            err = str(e)
            errors.append({"source": source["name"], "error": err})
            source_status.append({"name": source["name"], "status": "error", "items": 0, "error": err, "checked_at": checked_at})
        time.sleep(0.5)

    rows = list(by_key.values())
    rows.sort(key=lambda x: (x.get("score", 0), x.get("published", ""), x.get("collected_at", "")), reverse=True)
    rows = rows[:MAX_ROWS]
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    status = {
        "status": "ok" if not errors else "partial",
        "last_run": datetime.now(timezone.utc).isoformat(),
        "collector": "live-public-rss",
        "schedule": "hourly",
        "sources": len(SOURCES),
        "collected_this_run": collected,
        "stored_total": len(rows),
        "errors": errors,
        "source_status": source_status,
    }
    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
