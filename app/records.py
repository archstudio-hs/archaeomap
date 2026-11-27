"""Convert source records. Coordinates always retain their source and geometry meaning."""
from search_engine import unique, match_strength, positions_valid
from names import WD_COUNTRIES

SOURCE_NAMES = {
    "KHS": "국가유산청",
    "UNESCO": "UNESCO 세계유산센터",
    "WD": "Wikidata",
    "OSM": "OpenStreetMap · Photon",
    "PLEIADES": "Pleiades",
    "MASTER_CUSTOM": "통합 유적 DB · 사용자 추가",
    "MASTER_KHS": "통합 유적 DB · 국가유산청",
    "MASTER_JP": "통합 유적 DB · 일본 국토수치정보",
    "MASTER_CN": "통합 유적 DB · 중국 문물보호단위",
    "MASTER_CHGIS": "통합 유적 DB · CHGIS",
    "MASTER_UNESCO": "통합 유적 DB · UNESCO",
    "MASTER_PLEIADES": "통합 유적 DB · Pleiades",
    "MASTER_OSM": "통합 유적 DB · OpenStreetMap",
    "MASTER_WD": "통합 유적 DB · Wikidata",
    "MASTER": "통합 유적 DB",
}

MASTER_META = {
    "custom_add": ("MASTER_CUSTOM", "사용자 등록 정밀점"),
    "kr_khs_shp": ("MASTER_KHS", "국가유산 공간정보 대표점"),
    "kr_khs_api": ("MASTER_KHS", "국가유산청 등록 대표점"),
    "jp_mlit": ("MASTER_JP", "일본 국토수치정보 대표점"),
    "cn_ncha_bd09": ("MASTER_CN", "중국 문물보호단위 보정점"),
    "cn_chgis_v6": ("MASTER_CHGIS", "역사지명 대표점"),
    "unesco": ("MASTER_UNESCO", "세계유산 등재 대표점"),
    "pleiades": ("MASTER_PLEIADES", "Pleiades 지명록 대표점"),
    "osm": ("MASTER_OSM", "OSM 유적 추출점"),
    "wikidata": ("MASTER_WD", "Wikidata 유적 좌표"),
}


def record(provider, identity, name, coords, url, aliases, location, kind, historic=True):
    if positions_valid(coords[0], coords[1]):
        coords = [float(coords[0]), float(coords[1])]
    return {
        "provider": provider, "source": SOURCE_NAMES[provider], "sourceId": str(identity),
        "name": name, "lat": coords[0], "lon": coords[1], "url": url, "aliases": unique([name] + aliases),
        "location": location, "accuracy": kind, "historic": historic, "heritage": [], "lookup": [],
        "detail": "", "edition": "원자료 조회", "recordDate": "", "countries": [], "placeIds": [],
    }


# 일본 국토수치정보(문화재) 종류 번호. 2 무형문화재·3 민속문화재·7 선정보존기술은 기술·행사라 유적 검색에서 뺀다.
JP_MLIT_TYPES = {"1": "유형문화재", "4": "기념물", "5": "문화적 경관", "6": "전통적 건조물군 보존지구"}
JP_MLIT_SKIP = ("2", "3", "7")


def master_rows(data):
    out = []
    for raw in data:
        site_id, site_name, alt_name, cc, period, site_type, lat, lon, precision, source_org = raw[:10]
        if not positions_valid(lat, lon):
            continue
        if source_org == "jp_mlit":
            code = str(site_type).strip()
            if code in JP_MLIT_SKIP:
                continue
            site_type = JP_MLIT_TYPES.get(code, site_type)
        provider, acc_label = MASTER_META.get(source_org, ("MASTER", "통합 DB 등록점"))
        if precision == "approximate":
            acc_label = acc_label + " · 개략 좌표"
        alts = [a.strip() for a in str(alt_name or "").split("|") if a.strip()]
        url = ""
        if str(site_id).startswith("WD_Q"):
            url = "https://www.wikidata.org/wiki/" + str(site_id)[3:]
        elif str(site_id).startswith("OSM_N_"):
            url = "https://www.openstreetmap.org/node/" + str(site_id)[6:]
        elif str(site_id).startswith("OSM_W_"):
            url = "https://www.openstreetmap.org/way/" + str(site_id)[6:]
        elif str(site_id).startswith("OSM_R_"):
            url = "https://www.openstreetmap.org/relation/" + str(site_id)[6:]
        valid_cc = cc.upper() if isinstance(cc, str) and len(cc) == 2 and cc.isalpha() else ""
        loc_parts = [x for x in (valid_cc, site_type, period) if x and x not in ("nan", "None")]
        item = record(provider, site_id, site_name, [lat, lon], url, alts, " · ".join(loc_parts), acc_label, True)
        item["edition"] = "로컬 통합 유적 DB"
        item["countries"] = [valid_cc] if valid_cc else []
        item["lookup"] = unique([site_name] + alts)[:8]
        out.append(item)
    return out


def korean(row):
    cpno, name, hanja, region, lat, lon = row[:6]
    if not positions_valid(lat, lon) or not lat or not lon:
        return []
    url = "https://www.heritage.go.kr/heri/cul/culSelectDetail.do?ccbaCpno=" + cpno
    item = record("KHS", cpno, name, [lat, lon], url, [hanja], region, "공식 지정유산 대표점")
    item["countries"] = ["KR"]
    if len(row) > 9 and row[9]:
        item["location"] = region + " · " + row[9]
    return [item]


def statements(claims, prop):
    entries = [s for s in claims.get(prop, []) if s.get("rank") != "deprecated" and s.get("mainsnak", {}).get("snaktype") == "value"]
    return [s for s in entries if s.get("rank") == "preferred"] or entries


def value_of(statement):
    return statement.get("mainsnak", {}).get("datavalue", {}).get("value")


def wikidata(data):
    result = []
    for qid, item in data.get("entities", {}).items():
        claims, labels = item.get("claims", {}), item.get("labels", {})
        def value(lang):
            return labels.get(lang, {}).get("value", "")
        names = [v["value"] for v in labels.values()]
        if not names:
            continue
        name = next((value(lang) for lang in ["ko", "en", "ja", "zh"] if value(lang)), names[0])
        aliases = unique([value(lang) for lang in ["ko", "en", "ja", "zh"] if value(lang)] + list(names))
        for entries in item.get("aliases", {}).values():
            aliases.extend(v["value"] for v in entries[:15])
        desc = item.get("descriptions", {})
        description = desc.get("ko", desc.get("en", desc.get("ja", desc.get("zh", {})))).get("value", "")
        text = " ".join(d.get("value", "") for d in desc.values()).lower()
        instances = [(value_of(s) or {}).get("id", "") for s in statements(claims, "P31")]
        heritage = [str(value_of(s)) for s in statements(claims, "P757") if value_of(s)]
        place_ids = [str(value_of(s)) for s in statements(claims, "P1584") if value_of(s)]
        historic = bool(
            heritage or place_ids
            or any(t in instances for t in ("Q839954", "Q381885", "Q173387", "Q23413", "Q1521065"))
            or any(w in text for w in ("archaeolog", "burial", "ancient ", "ruins", "prehistoric", "고대", "고분", "유적", "遺跡", "古墳", "遗址", "古墓", "archéolog"))
        )
        facility = any(t in instances for t in ("Q33506", "Q55488", "Q27686", "Q1248784")) or any(
            w in text for w in ("museum in ", "archaeological museum", "museum of ", "railway station", "train station", "hotel in ", "restaurant", "공항", "박물관", "기차역", "ホテル", "鉄道駅", "博物馆", "火车站")
        )
        settlement = any(w in text for w in ("municipality", "city in ", "commune in ", "municipio", "코무네", "행정구역", "自治体", "市镇"))
        for statement in statements(claims, "P625"):
            coord = value_of(statement)
            if not coord or not str(coord.get("globe", "")).endswith("/Q2") or not positions_valid(coord.get("latitude"), coord.get("longitude")):
                continue
            row = record("WD", qid, name, [coord["latitude"], coord["longitude"]], "https://www.wikidata.org/wiki/" + qid, aliases, description, "항목에 등록된 좌표", historic)
            row["lookup"] = unique([value(l) for l in ("ko", "en", "ja", "zh", "fr", "es")] + names)[:10]
            row["placeIds"], row["heritage"] = place_ids, heritage
            row["countries"] = unique([WD_COUNTRIES.get((value_of(s) or {}).get("id", ""), "") for s in statements(claims, "P17")])
            row["contextOnly"] = facility or (settlement and not historic) or not historic
            p = coord.get("precision")
            if p and float(p) > 0:
                row["detail"] = "원자료 좌표 표기 단위 " + ("%.8f" % float(p)).rstrip("0").rstrip(".") + "°"
            qualifiers = statement.get("qualifiers", {})
            if qualifiers.get("P518") or qualifiers.get("P1480") or qualifiers.get("P585"):
                row["detail"] += " · 적용 부분·시점 등 한정 조건은 원문 참조"
                row["qualified"] = True
            row["recordDate"] = str(item.get("modified", ""))[:10]
            result.append(row)
    return result


def osm(data):
    result = []
    for feat in data.get("features", []):
        p, geom = feat.get("properties", {}), feat.get("geometry", {})
        typ = {"N": "node", "W": "way", "R": "relation"}.get(p.get("osm_type"))
        if not typ or not p.get("osm_id") or not p.get("name") or geom.get("type") != "Point":
            continue
        oid = typ + "/" + str(p["osm_id"])
        historic = p.get("osm_key") == "historic" and p.get("osm_value") in ("archaeological_site", "ruins", "tomb", "fort", "castle", "citywalls", "city_gate", "monastery", "cairn", "megalith", "roman_road")
        xy = geom["coordinates"]
        row = record(
            "OSM", oid, p["name"], [xy[1], xy[0]], "https://www.openstreetmap.org/" + oid, [],
            " · ".join(unique([p.get("country"), p.get("state"), p.get("city"), p.get("osm_value")])),
            "OSM에 등록된 지점" if typ == "node" else "OSM 선·구역의 검색 대표점", historic,
        )
        row["contextOnly"] = not historic
        row["countries"] = [str(p.get("countrycode", "")).upper()]
        result.append(row)
    return result


def unesco_rows(data, terms, ids):
    out = []
    for record_data in data:
        wid, en, zh, fr, country, components = record_data[:6]
        ko_names = record_data[6] if len(record_data) > 6 else []
        parent_names = unique([en, zh, fr] + ko_names)
        parent_match = match_strength(terms, parent_names) or wid in ids
        serial = len(components) > 1 or (len(record_data) > 7 and record_data[7] > 1)
        ordered = []
        for comp in components:
            ref, name, lat, lon = comp[:4]
            if not positions_valid(lat, lon):
                continue
            local_names = comp[4] if len(comp) > 4 else []
            if ref == "668-001":
                local_names = [n for n in local_names if n != "앙코르 와트"]
            score = match_strength(terms, [name] + local_names)
            if score or parent_match:
                ordered.append((score, ref, name, lat, lon, local_names))
        ordered.sort(key=lambda c: -c[0])
        for score, ref, name, lat, lon, local_names in ordered[:25]:
            aliases = ([name] + local_names) if serial else unique(parent_names + local_names)
            row = record("UNESCO", ref or wid, name or en, [lat, lon], "https://whc.unesco.org/en/list/" + wid + "/", aliases, country + " · " + en, "구성유산 등록점" if serial else "세계유산 등록 대표점")
            row["countries"] = country.replace(",", " ").split()
            row["heritage"] = [wid]
            row["serial"] = serial
            row["parentMatch"] = bool(parent_match)
            row["contextOnly"] = bool(serial and not score)
            row["lookup"] = [name or en]
            row["detail"] = ("구성유산 " + str(ref) + " · " if serial else "") + "세계유산 번호 " + wid
            if local_names:
                row["name"] = local_names[0] + " · " + (name or en)
            elif not serial:
                localized = next((s for s in ko_names if any("가" <= c <= "힣" for c in s)), "")
                if localized:
                    row["name"] = localized + " · " + (name or en)
            out.append(row)
    return out


REGIONAL_TYPES = ("region", "province", "people", "river", "sea", "mountain-range", "island", "ethnic-group", "territory", "water", "country")


def ancient_index(data):
    out = []
    for entry in data:
        keys, pid, title, lat, lon, precision, types, updated = entry[:8]
        country = entry[8] if len(entry) > 8 else ""
        if precision not in ("precise", "rough"):
            continue
        row = record("PLEIADES", pid, title, [lat, lon], "https://pleiades.stoa.org/places/" + pid, title.split("/"), types, "지명록의 계산 대표점")
        row["placeIds"] = [pid]
        row["edition"] = "지명록 색인"
        row["phonetic"] = keys
        row["countries"] = [country] if country else []
        if country:
            row["location"] = country + " · " + types
        row["detail"] = "Pleiades 위치 자료에서 산출한 대표점" + (" · 원자료 분류 ‘대략적’" if precision == "rough" else "")
        row["recordDate"] = updated
        row["contextOnly"] = bool(types) and all(t.strip() in REGIONAL_TYPES for t in types.split(","))
        out.append(row)
    return out


def pleiades(data):
    if not data.get("reprPoint") or not data.get("locations"):
        return []
    pid, title = str(data["id"]), data["title"]
    aliases = []
    for n in data.get("names", []):
        if n.get("associationCertainty") == "uncertain":
            continue
        aliases.extend([n.get("attested", ""), n.get("romanized", "")])
    types = data.get("placeTypes", [])
    located = [loc for loc in data["locations"] if loc.get("geometry") and loc.get("associationCertainty") == "certain"]
    if not located:
        return []
    representative = [loc for loc in located if loc["geometry"].get("type") == "Point" and "representative" in loc.get("locationType", [])]
    selected = representative[0] if len(representative) == 1 else None
    xy = selected["geometry"]["coordinates"] if selected else data["reprPoint"]
    if len(xy) < 2 or not positions_valid(xy[1], xy[0]):
        return []
    row = record("PLEIADES", pid, title, [xy[1], xy[0]], "https://pleiades.stoa.org/places/" + pid, aliases, ", ".join(types), "지명록에 기록된 대표점" if selected else "지명록의 계산 대표점")
    row["placeIds"] = [pid]
    row["lookup"] = [title]
    row["contextOnly"] = bool(types) and all(t in REGIONAL_TYPES for t in types)
    if selected and selected.get("accuracy_value") is not None:
        row["detail"] = "해당 위치 자료가 밝힌 수평 정밀도 " + str(selected["accuracy_value"]) + " m"
    elif not selected:
        row["detail"] = "Pleiades가 위치 도형에서 산출한 대표점"
    row["recordDate"] = str(data.get("modified", ""))[:10]
    return [row]


def parse_source(req, data):
    kind, term, lang = req
    if kind == "master":
        return master_rows(data)
    if kind == "catalog":
        rows = [r for raw in data.get("khs", []) for r in korean(raw)] + unesco_rows(data.get("unesco", []), term, lang)
        for row in rows:
            row["edition"] = "저장된 공식 목록"
            row["recordDate"] = data.get("khsDate" if row["provider"] == "KHS" else "unescoDate", "")
        return rows
    if kind in ("unesco_id", "unesco_name"):
        records = [{"kind": "property", "data": r} for r in data]
        if kind == "unesco_id":
            records.extend({"kind": "property_checked", "id": wid} for wid in term.split(","))
        return records
    if kind == "wd":
        return [{"kind": "id", "qid": h["id"], "written": unique([h.get("match", {}).get("text", ""), h.get("label", "")])} for h in data.get("search", []) if h.get("id")]
    if kind in ("title", "wiki"):
        out = []
        for p in data.get("query", {}).get("pages", {}).values():
            props = p.get("pageprops", {})
            if props.get("wikibase_item") and "disambiguation" not in props:
                out.append({"kind": "id", "qid": props["wikibase_item"], "written": unique(([term] if kind == "title" else []) + [p.get("title", "")])})
        return out
    if kind == "pleiades_find":
        return [{"kind": "place_hit", "pid": r[0], "title": r[1]} for r in data]
    if kind == "saved":
        saved = [r for r in wikidata(data) if match_strength(term, r["aliases"]) >= 45]
        for row in saved:
            row["edition"] = "저장된 항목"
        return saved
    if kind == "entity":
        return wikidata(data) + [{"kind": "entity_checked", "id": qid} for qid in data.get("entities", {})]
    if kind in ("osm", "historic"):
        return osm(data)
    if kind == "khs":
        return [r for x in data for r in korean(x)]
    if kind == "ancient":
        return ancient_index(data)
    if kind == "pleiades":
        return pleiades(data) + [{"kind": "place_checked", "id": term}]
    return []