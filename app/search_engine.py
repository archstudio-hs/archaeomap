"""Site search. The desktop server and the browser worker execute this Python."""
import math
from names import country_query, place_probes

# Alternate written forms only. All coordinates come from a named record.
READINGS = [
    ["마키무쿠 유적", "마키무쿠", "纒向遺跡", "Makimuku ruins"],
    ["요시노가리 유적", "요시노가리", "吉野ヶ里遺跡", "Yoshinogari site"],
    ["산나이마루야마 유적", "산나이마루야마", "三内丸山遺跡", "Sannai-Maruyama Site"],
    ["다이센 고분", "다이센료 고분", "大仙陵古墳", "Daisen Kofun"],
    ["모즈 고분군", "百舌鳥古墳群", "Mozu kofun group"],
    ["후루이치 고분군", "古市古墳群", "Furuichi kofun group"],
    ["가라코카기 유적", "唐古・鍵遺跡", "Karako-Kagi Site"],
    ["이케가미소네 유적", "池上曽根遺跡", "Ikegami-Sone Site"],
    ["반포 유적", "반포유적", "半坡遗址", "Banpo"],
    ["싼싱두이", "삼성퇴", "三星堆", "三星堆遗址", "Sanxingdui"],
    ["진시황릉", "秦始皇陵", "Mausoleum of the First Qin Emperor"],
    ["얼리터우", "얼리터우 유적", "이리두", "二里头", "二里头遗址", "Erlitou"],
    ["은허", "안양 은허", "殷墟", "Yinxu"],
    ["량주", "량주 고성", "양저 유적", "良渚", "良渚古城", "Liangzhu"],
    ["폼페이", "Pompeii"], ["마추픽추", "Machu Picchu"],
    ["페트라", "Petra"], ["앙코르와트", "Angkor Wat"],
    ["괴베클리 테페", "Göbekli Tepe"], ["스톤헨지", "Stonehenge"],
]

PUNCT_SKIP = "・ （）【】、。–—《》「」『』〈〉〔〕，：；！？～〜－·"

CJK_MAP = {
    "遗": "遺", "迹": "跡", "坟": "墳", "窑": "窯", "宫": "宮", "庙": "廟",
    "门": "門", "东": "東", "旧": "舊", "国": "國", "县": "縣", "镇": "鎮",
    "区": "區", "龙": "龍", "马": "馬", "汉": "漢", "齐": "齊", "鲁": "魯",
    "赵": "趙", "韩": "韓", "乐": "樂", "楽": "樂", "庆": "慶", "广": "廣",
    "広": "廣", "铁": "鐵", "鉄": "鐵", "铜": "銅", "岛": "島", "湾": "灣",
    "馆": "館", "园": "園", "头": "頭", "发": "發", "长": "長", "台": "臺",
    "蔵": "藏", "宝": "寶", "仏": "佛", "ヶ": "ケ", "ヵ": "カ", "泽": "澤",
    "沢": "澤", "阳": "陽", "阴": "陰", "郑": "鄭", "辽": "遼", "宁": "寧",
}

ZH_HINTS = "遗址遗迹墓群窑址古城东门马汉国县镇区头发长乐齐鲁赵韩铜铁岛湾馆园层期庙宫陵阳阴郑辽宁"


def key(text):
    return "".join(ch for ch in str(text or "").lower() if ch.isalnum() or ord(ch) >= 256 and ch not in PUNCT_SKIP)


def cjk_key(text):
    base = key(text)
    return "".join(CJK_MAP.get(ch, ch) for ch in base)


def language(text):
    for char in text:
        if "가" <= char <= "힣" or "ㄱ" <= char <= "ㅣ":
            return "ko"
        if "ぁ" <= char <= "ヿ":
            return "ja"
    if any("一" <= c <= "鿿" or "\u3400" <= c <= "\u4dbf" for c in text):
        if any(c in ZH_HINTS for c in text):
            return "zh"
        return "ja"
    for char in text:
        if "А" <= char <= "я": return "ru"
        if "؀" <= char <= "ۿ": return "ar"
        if "Ͱ" <= char <= "Ͽ": return "el"
        if "א" <= char <= "ת": return "he"
        if "ऀ" <= char <= "ॿ": return "hi"
        if "ก" <= char <= "๛": return "th"
    return "en"


def unique(items):
    found = []
    for item in items:
        if item and item not in found:
            found.append(item)
    return found


SUFFIXES = [
    " 고분군", " 유적지", " 유적", " 고분", " 패총", " 가마터", " 산성", " 토성", " 사지", " 절터",
    "고분군", "유적지", "유적", "고분",
    "古墳群", "官衙遺跡", "廃寺跡", "遺跡", "古墳", "貝塚", "城跡",
    "古墓群", "古城址", "遗址", "遺址", "遗迹", "墓群", "城址", "窑址", "窯址",
    " archaeological site", " ruins", " site", " tomb", " tumulus",
]


def expand(query):
    q = query.strip()
    words = [q]
    normalized = cjk_key(q)
    for names in READINGS:
        if normalized in [cjk_key(n) for n in names]:
            words.extend(names)
            break
    low = q.lower()
    for suffix in SUFFIXES:
        if low.endswith(suffix) and len(q[:-len(suffix)].strip()) >= 2:
            words.append(q[:-len(suffix)].strip())
            break
    return unique(words)


def match_strength(terms, names):
    best = 0
    for term in terms:
        a1, a2 = key(term), cjk_key(term)
        if not a1:
            continue
        for name in names:
            b1, b2 = key(name), cjk_key(name)
            if not b1:
                continue
            if a1 == b1 or a2 == b2:
                return 100
            if len(a1) >= 2 and a1 in b1:
                best = max(best, 45 + int(38 * len(a1) / len(b1)))
            elif len(a2) >= 2 and a2 in b2:
                best = max(best, 45 + int(38 * len(a2) / len(b2)))
    return best


def positions_valid(lat, lon):
    try:
        return (lat is not None and lon is not None and
                -90 <= float(lat) <= 90 and -180 <= float(lon) <= 180)
    except (TypeError, ValueError):
        return False


def distance_m(a, b):
    rad = math.pi / 180
    lat1, lat2 = a["lat"] * rad, b["lat"] * rad
    dlat = lat2 - lat1
    dlon = (b["lon"] - a["lon"]) * rad
    h = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    return round(12742017.6 * math.asin(math.sqrt(min(1, max(0, h)))))


OFFICIAL_PROVIDERS = ("KHS", "UNESCO", "MASTER_CUSTOM", "MASTER_KHS", "MASTER_JP", "MASTER_CN", "MASTER_UNESCO")


def search(query, fetch, local_only=False):
    """All network and index reads are explicit bounded batches. A place enters the map only on selection."""
    from records import unesco_rows
    query = query.strip()
    name, country = country_query(query)
    if not country:
        parts = query.split()
        if len(parts) >= 2:
            cjk_countries = {"한국": "KR", "대한민국": "KR", "韓国": "KR", "韩国": "KR", "korea": "KR", "일본": "JP", "日本": "JP", "중국": "CN", "中国": "CN", "中國": "CN"}
            p0, p1 = parts[0].lower(), parts[-1].lower()
            if p0 in cjk_countries:
                name, country = " ".join(parts[1:]), cjk_countries[p0]
            elif p1 in cjk_countries:
                name, country = " ".join(parts[:-1]), cjk_countries[p1]

    terms = expand(name)
    original = language(name)
    issues = []

    def batch(requests):
        rows = []
        for reply in fetch(requests) if requests else []:
            if reply.get("error"):
                issues.append(reply["error"])
            rows.extend(reply.get("rows", []))
        return rows

    def indexed(words):
        probes = place_probes(words)
        return batch([["ancient", probes, []]]) if probes else []

    local = batch([["master", terms, country], ["catalog", terms, []], ["saved", terms, []]])
    initial_places = indexed(terms)
    first = []
    if not local_only:
        requests = [["wd", name, original], ["title", name, original], ["historic", name, original], ["osm", query, original]]
        if original == "ko" and (not country or country == "KR"):
            requests.append(["khs", name, "ko"])
        if original in ("ko", "zh", "ja", "en"):
            requests.append(["wiki", name, original])
        if original in ("ja", "zh") and not any("ぁ" <= c <= "ヿ" for c in name):
            other_cjk = "zh" if original == "ja" else "ja"
            requests.append(["wd", name, other_cjk])
            requests.append(["title", name, other_cjk])
            requests.append(["wiki", name, other_cjk])
        for t in terms[1:]:
            if len(requests) >= 14:
                break
            requests.append(["wd", t, language(t)])
        latin = next((s for s in terms if language(s) == "en" and len(s) >= 3 and any("a" <= c.lower() <= "z" for c in s)), "")
        if latin:
            requests.append(["pleiades_find", latin, "en"])
        first = batch(requests)

    ids = unique([r["qid"] for r in first if r.get("kind") == "id"])
    reply = batch([["entity", ",".join(ids[:16]), original]]) if ids else []
    wiki = [r for r in reply if r.get("provider") == "WD"]
    fetched = set(r["id"] for r in reply if r.get("kind") == "entity_checked")
    wiki.extend([r for r in local if r["provider"] == "WD" and r["sourceId"] not in fetched])
    for row in wiki:
        for hit in first:
            if hit.get("qid") == row["sourceId"]:
                row["aliases"] = unique(row["aliases"] + hit.get("written", []))

    aliases = list(terms)
    heritage_ids = []
    linked_places = []
    place_hits = [r for r in first if r.get("kind") == "place_hit" and match_strength(terms, [r["title"]]) >= 55]
    place_hits.sort(key=lambda r: -match_strength(terms, [r["title"]]))
    for row in wiki:
        if not row.get("contextOnly") and match_strength(terms, row["aliases"]) >= 80:
            aliases.extend(row.get("lookup", [])[:6])
            heritage_ids.extend(row.get("heritage", []))
            linked_places.extend(row.get("placeIds", []))
    aliases = unique(aliases)[:26]
    if aliases != terms or heritage_ids:
        cached = batch([["master", aliases, country], ["catalog", aliases, unique(heritage_ids)]])
    else:
        cached = [r for r in local if r["provider"] != "WD"]

    by_place = {}
    for r in initial_places + (indexed(aliases) if aliases != terms else []):
        by_place[r["sourceId"]] = r
    probes = place_probes(aliases)
    places = list(by_place.values())
    places.sort(key=lambda r: -(match_strength(aliases, r["aliases"]) or (60 if any(p in r.get("phonetic", []) for p in probes) else 0)))
    eligible_props = [r for r in cached if r["provider"] == "UNESCO" and (not country or country in r.get("countries", []))]
    heritage_ids = unique(heritage_ids + [w for r in eligible_props for w in r["heritage"]])
    second = []
    if not local_only:
        latin = next((s for s in aliases if language(s) == "en" and len(s) >= 3 and any("a" <= c.lower() <= "z" for c in s)), "")
        if latin and key(latin) != key(name):
            second.extend([["historic", latin, "en"], ["osm", latin, "en"]])
        for pid in unique(linked_places + [r["sourceId"] for r in places] + [r["pid"] for r in place_hits])[:4]:
            second.append(["pleiades", pid, "en"])
        if heritage_ids:
            second.append(["unesco_id", ",".join(heritage_ids[:10]), "en"])
        source_term = latin or name
        second.append(["unesco_name", source_term[:100], language(source_term)])
    extra = batch(second)
    properties = [r["data"] for r in extra if r.get("kind") == "property"]
    current_ids = set(p[0] for p in properties).union(r["id"] for r in extra if r.get("kind") == "property_checked")
    translations = {}
    for r in cached:
        if r["provider"] == "UNESCO":
            translations[r["sourceId"]] = r
    for p in properties:
        for comp in p[5]:
            prev = translations.get(comp[0] or p[0])
            if prev and key(comp[1]) in [key(s) for s in prev["aliases"]]:
                comp.append([s for s in prev["aliases"] if language(s) == "ko"])
    current = unesco_rows(properties, aliases, heritage_ids)
    live_places = {r["sourceId"]: r for r in extra if r.get("provider") == "PLEIADES"}
    checked_places = set(r["id"] for r in extra if r.get("kind") == "place_checked")
    for old in places:
        latest = live_places.get(old["sourceId"])
        if latest:
            latest["phonetic"] = old.get("phonetic", [])
            if distance_m(latest, old) <= 1000:
                latest["countries"] = old["countries"]
                latest["location"] = old["location"]
    records = (
        [r for r in first + extra if "provider" in r] + wiki + current +
        [r for r in cached if r["provider"] != "UNESCO" or not any(w in current_ids for w in r["heritage"])] +
        [r for r in places if r["sourceId"] not in checked_places]
    )
    ranked = []
    seen = set()
    for r in records:
        if not positions_valid(r.get("lat"), r.get("lon")):
            continue
        if country and any(r.get("countries", [])) and country not in r["countries"]:
            continue
        identity = (r["provider"], r["sourceId"], r["lat"], r["lon"]) if r["provider"] == "WD" else (r["provider"], r["sourceId"])
        if identity in seen:
            continue
        direct = match_strength(terms, r["aliases"])
        score = max(direct, match_strength(aliases, r["aliases"]) - 10)
        sound = any(p in r.get("phonetic", []) for p in probes)
        if r["provider"] == "PLEIADES" and r["sourceId"] in linked_places:
            score = max(90, score)
        elif sound and score <= 0:
            score = 62
            r["detail"] = "발음이 비슷한 이름 후보 · " + r["detail"]
        if score <= 0 and r.get("parentMatch"):
            score = 24
        if score <= 0:
            continue
        seen.add(identity)
        bonus = 20 if r["provider"] == "MASTER_CUSTOM" else (17 if r["provider"] in OFFICIAL_PROVIDERS else (10 if r["provider"].startswith("MASTER") else 0))
        r["rank"] = score + bonus + (8 if r.get("historic") else 0) + (4 if country and country in r.get("countries", []) else 0)
        if r.get("contextOnly"):
            r["rank"] -= 45
        r["comparisons"] = []
        ranked.append(r)
    anchors = [r for r in ranked if r["provider"] in OFFICIAL_PROVIDERS and not r.get("contextOnly") and r["rank"] >= 105]
    for row in ranked:
        if country and not any(row.get("countries", [])):
            row["detail"] = (row["detail"] + " · " if row["detail"] else "") + "입력한 국가와의 일치 여부 미확인"
            row["rank"] -= 15
            if not any(distance_m(row, a) <= 2000 for a in anchors):
                row["contextOnly"] = True
        if anchors and row["provider"] in ("OSM", "WD", "PLEIADES") and not row.get("contextOnly") and all(distance_m(row, a) > 25000 for a in anchors):
            row["detail"] = (row["detail"] + " · " if row["detail"] else "") + "같은 이름의 공식 후보와 25 km 이상 떨어짐"
            row["contextOnly"] = True
            row["rank"] -= 35
    ranked.sort(key=lambda r: -r["rank"])
    for a in ranked[:30]:
        if a.get("contextOnly") or a.get("qualified"):
            continue
        names_a = set(cjk_key(s) for s in a["aliases"] if len(cjk_key(s)) >= 2)
        peers = []
        for b in ranked:
            if a["provider"] == b["provider"] or b.get("contextOnly") or b.get("qualified"):
                continue
            if any(a.get("countries", [])) and any(b.get("countries", [])) and not set(a["countries"]).intersection(b["countries"]):
                continue
            pid = set(a.get("placeIds", [])).intersection(b.get("placeIds", []))
            property_id = set(a.get("heritage", [])).intersection(b.get("heritage", []))
            same_name = any(cjk_key(s) in names_a for s in b["aliases"])
            meters = distance_m(a, b)
            basis = ""
            if pid and "PLEIADES" in (a["provider"], b["provider"]):
                basis = "같은 Pleiades 항목"
            elif property_id and not a.get("serial") and not b.get("serial") and meters <= 2000:
                basis = "같은 단일 등재유산"
            elif same_name and meters <= 2000:
                basis = "이름 일치 · 2 km 이내"
            if basis:
                peers.append({"name": b["name"], "source": b["source"], "url": b["url"], "lat": b["lat"], "lon": b["lon"], "meters": meters, "basis": basis})
        peers.sort(key=lambda b: b["meters"])
        a["comparisons"] = peers[:4]
    return {"rows": ranked[:30], "issues": unique(issues), "terms": aliases[:10], "total": len(ranked)}