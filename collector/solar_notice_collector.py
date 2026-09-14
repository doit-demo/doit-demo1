import json
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

KEYWORDS={"태양광":30,"신재생에너지":18,"영농형태양광":30,"햇빛소득":30,"발전사업":16,"공유재산":14,"유휴부지":14,"공공부지":14,"에너지":8,"RE100":10,"REC":6,"RPS":6,"농촌":8,"임대":6,"태양광발전":25,"태양광발전소":28,"태양광설치":22,"주민참여형":15,"수상태양광":22,"지붕형태양광":22,"염해농지":20}
NEGATIVE={"풍력":-12,"풍력발전":-15,"수소":-4,"전기차":-3}
SOURCES=[
 {"name":"Google News · 태양광 공고","url":"https://news.google.com/rss/search?q=%ED%83%9C%EC%96%91%EA%B4%91%20%EA%B3%B5%EA%B3%A0&hl=ko&gl=KR&ceid=KR:ko"},
 {"name":"Google News · 신재생에너지 공고","url":"https://news.google.com/rss/search?q=%EC%8B%A0%EC%9E%AC%EC%83%9D%EC%97%90%EB%84%88%EC%A7%80%20%EA%B3%B5%EA%B3%A0&hl=ko&gl=KR&ceid=KR:ko"},
 {"name":"Google News · 영농형태양광","url":"https://news.google.com/rss/search?q=%EC%98%81%EB%86%8D%ED%98%95%ED%83%9C%EC%96%91%EA%B4%91&hl=ko&gl=KR&ceid=KR:ko"},
 {"name":"Google News · 햇빛소득","url":"https://news.google.com/rss/search?q=%ED%96%87%EB%B9%9B%EC%86%8C%EB%93%9D%20%EA%B3%B5%EA%B3%A0&hl=ko&gl=KR&ceid=KR:ko"},
 {"name":"Google News · 발전사업 공고","url":"https://news.google.com/rss/search?q=%EB%B0%9C%EC%A0%84%EC%82%AC%EC%97%85%20%EA%B3%B5%EA%B3%A0%20%ED%83%9C%EC%96%91%EA%B4%91&hl=ko&gl=KR&ceid=KR:ko"},
 {"name":"Google News · 공유재산 태양광","url":"https://news.google.com/rss/search?q=%EA%B3%B5%EC%9C%A0%EC%9E%AC%EC%82%B0%20%ED%83%9C%EC%96%91%EA%B4%91&hl=ko&gl=KR&ceid=KR:ko"},
 {"name":"Google News · 주민참여 태양광","url":"https://news.google.com/rss/search?q=%EC%A3%BC%EB%AF%BC%EC%B0%B8%EC%97%AC%20%ED%83%9C%EC%96%91%EA%B4%91&hl=ko&gl=KR&ceid=KR:ko"},
 {"name":"Google News · 지붕형 태양광","url":"https://news.google.com/rss/search?q=%EC%A7%80%EB%B6%95%ED%98%95%20%ED%83%9C%EC%96%91%EA%B4%91&hl=ko&gl=KR&ceid=KR:ko"},
 {"name":"Google News · 공공부지 태양광","url":"https://news.google.com/rss/search?q=%EA%B3%B5%EA%B3%B5%EB%B6%80%EC%A7%80%20%ED%83%9C%EC%96%91%EA%B4%91&hl=ko&gl=KR&ceid=KR:ko"},
]
BIZINFO_URL="https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"
OUT=Path("data/notices.json"); STATUS=Path("monitor-status.json"); MAX_ROWS=3000

def fetch(url,timeout=30):
 req=Request(url,headers={"User-Agent":"Mozilla/5.0 DSOLAR-Notice-Monitor/2.1"})
 with urlopen(req,timeout=timeout) as r:return r.read().decode("utf-8",errors="replace")

def clean(text):return re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",re.sub(r"<!\[CDATA\[|\]\]>","",text or ""))).strip()

def tag_score(text):
 low=text.lower();matched=[k for k in KEYWORDS if k.lower() in low];negative=[k for k in NEGATIVE if k.lower() in low]
 score=min(100,max(0,sum(KEYWORDS[k] for k in matched)+sum(NEGATIVE[k] for k in negative)))
 if "태양광" in matched and any(k in matched for k in ("발전사업","영농형태양광","햇빛소득","공유재산","공공부지","유휴부지","주민참여형","지붕형태양광","수상태양광")):score=min(100,score+10)
 return score,matched

def classify(title,desc):
 text=f"{title} {desc}".lower()
 if any(k in text for k in ("영농형태양광","햇빛소득","염해농지","농촌")):return "영농형/농촌"
 if any(k in text for k in ("공유재산","유휴부지","공공부지","국유지","시유지","군유지")):return "공공부지"
 if any(k in text for k in ("지붕형태양광","공장 지붕","산업단지","물류센터","지붕 태양광")):return "지붕형"
 if any(k in text for k in ("주민참여형","마을","주민참여")):return "주민참여"
 if any(k in text for k in ("수상태양광","저수지","댐 태양광")):return "수상태양광"
 if any(k in text for k in ("발전사업","민간사업자","사업자 모집","사업자 공모")):return "발전사업"
 return "신재생 일반"

def parse_xml_items(xml_text,source_name,source_url):
 rows=[]
 try:root=ET.fromstring(xml_text)
 except ET.ParseError:return rows
 for item in root.iter():
  if item.tag.lower().split('}')[-1] not in ("item","row"):continue
  vals={c.tag.lower().split('}')[-1]:clean(c.text or "") for c in list(item)}
  title=vals.get("title") or vals.get("pblancnm") or vals.get("subject") or ""
  if not title:continue
  link=vals.get("link") or vals.get("pblancurl") or vals.get("detailurl") or source_url
  desc=vals.get("description") or vals.get("content") or vals.get("bsnsdsc") or ""
  pub=vals.get("pubdate") or vals.get("regdt") or vals.get("creatdt") or vals.get("createdate") or ""
  org=vals.get("organname") or vals.get("deptname") or vals.get("institution") or vals.get("organization") or source_name
  text=f"{title} {desc} {org}";score,matched=tag_score(text)
  if score<15:continue
  rows.append({"title":title,"description":desc[:1200],"url":link,"source":source_name,"published":pub,"organization":org,"category":classify(title,desc),"score":score,"matched_keywords":matched,"collected_at":datetime.now(timezone.utc).isoformat()})
 return rows

def fetch_bizinfo():
 key=os.getenv("BIZINFO_API_KEY","").strip()
 if not key:return [],{"name":"기업마당 지원사업 API","status":"disabled","items":0,"reason":"BIZINFO_API_KEY 미설정"}
 text=fetch(BIZINFO_URL+"?"+urlencode({"crtfcKey":key,"dataType":"json","searchCnt":"100"}));obj=json.loads(text);candidates=[]
 if isinstance(obj,dict):
  for k in ("jsonArray","items","data","result"):
   if isinstance(obj.get(k),list):candidates=obj[k];break
 rows=[]
 for x in candidates:
  if not isinstance(x,dict):continue
  title=x.get("pblancNm") or x.get("title") or x.get("subject") or "";desc=x.get("bsnsSumryCn") or x.get("description") or x.get("content") or "";url=x.get("pblancUrl") or x.get("link") or "https://www.bizinfo.go.kr/";org=x.get("jrsdInsttNm") or x.get("organName") or "기업마당";pub=x.get("creatPnttm") or x.get("regDt") or x.get("pubDate") or "";region=x.get("rcritSe") or x.get("areaNm") or ""
  score,matched=tag_score(f"{title} {desc} {org} {region}")
  if not title or score<15:continue
  rows.append({"title":title,"description":clean(str(desc))[:1200],"url":url,"source":"기업마당 지원사업 API","published":str(pub),"organization":org,"region":str(region),"category":classify(title,str(desc)),"score":score,"matched_keywords":matched,"collected_at":datetime.now(timezone.utc).isoformat()})
 return rows,{"name":"기업마당 지원사업 API","status":"ok","items":len(rows)}

def key_for(row):return row.get("url") or (row.get("source",""),row.get("title",""),row.get("published",""))

def main():
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try:existing=json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
 except Exception:existing=[]
 by_key={str(key_for(x)):x for x in existing if isinstance(x,dict)};errors=[];statuses=[];collected=0
 for source in SOURCES:
  checked=datetime.now(timezone.utc).isoformat()
  try:
   rows=parse_xml_items(fetch(source["url"]),source["name"],source["url"])
   for row in rows:by_key[str(key_for(row))]=row
   collected+=len(rows);statuses.append({"name":source["name"],"status":"ok","items":len(rows),"checked_at":checked})
  except Exception as e:
   errors.append({"source":source["name"],"error":str(e)});statuses.append({"name":source["name"],"status":"error","items":0,"error":str(e),"checked_at":checked})
  time.sleep(.35)
 try:
  rows,biz=fetch_bizinfo()
  for row in rows:by_key[str(key_for(row))]=row
  collected+=len(rows);statuses.append(biz|{"checked_at":datetime.now(timezone.utc).isoformat()})
 except Exception as e:
  errors.append({"source":"기업마당 지원사업 API","error":str(e)});statuses.append({"name":"기업마당 지원사업 API","status":"error","items":0,"error":str(e)})
 rows=list(by_key.values())
 rows.sort(key=lambda x:(x.get("score",0),x.get("published",""),x.get("collected_at","")),reverse=True)
 rows=rows[:MAX_ROWS]
 OUT.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
 STATUS.write_text(json.dumps({"status":"ok" if not errors else "partial","last_run":datetime.now(timezone.utc).isoformat(),"collector":"live-public-sources","schedule":"hourly","sources":len(statuses),"collected_this_run":collected,"stored_total":len(rows),"errors":errors,"source_status":statuses},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"collected":collected,"stored":len(rows),"errors":errors},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
