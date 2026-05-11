import json
import os
import re
from urllib import error, request


_PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")
_AT_TOKEN_RE = re.compile(r"@([A-Za-z_][A-Za-z0-9_]*)@")


def _default_api_url():
    return os.environ.get(
        "RAPOR_SQL_API_URL",
        "http://localhost:8053/RaporApi/raporSqlGetir?prmRaporSqlId=0",
    )


def _api_headers():
    headers = {"Content-Type": "application/json"}
    # API key'i doğrudan koda ekledik (çevresel değişken yoksa bunu kullanacak)
    api_key = os.environ.get("RAPOR_SQL_API_KEY", "6f9c2d1b8e4a2f6a9b3d0ehj8a1f4b7d").strip()
    if api_key:
        headers["X-API-KEY"] = api_key
    return headers


def _default_mapping_file():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "rapor_sql_kod_map.json")
    )


def _load_kod_map():
    """
    Kod eslestirmelerini su sirayla okur:
    1) RAPOR_SQL_KOD_MAP_JSON (ortam degiskeni, JSON string)
    2) RAPOR_SQL_KOD_MAP_FILE (ortam degiskeni, JSON dosya yolu)
    3) Varsayilan dosya: flask_app/rapor_sql_kod_map.json
    """
    map_json = os.environ.get("RAPOR_SQL_KOD_MAP_JSON", "").strip()
    if map_json:
        try:
            parsed = json.loads(map_json)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError as exc:
            print(f"Rapor SQL kod map JSON hatasi: {exc}")

    map_file = os.environ.get("RAPOR_SQL_KOD_MAP_FILE", "").strip() or _default_mapping_file()
    if os.path.exists(map_file):
        try:
            with open(map_file, "r", encoding="utf-8") as fh:
                parsed = json.load(fh)
                if isinstance(parsed, dict):
                    return parsed
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Rapor SQL kod map dosya hatasi ({map_file}): {exc}")

    return {}


def _resolve_kod_candidates(rapor_sql_kod):
    """
    Logical kod -> API kod aday listesi.
    Map'te:
    - string ise tek aday
    - list ise listedeki tum adaylar
    En sona her zaman orijinal kod eklenir.
    """
    candidates = []
    kod_map = _load_kod_map()
    mapped = kod_map.get(rapor_sql_kod)

    if isinstance(mapped, str) and mapped.strip():
        candidates.append(mapped.strip())
    elif isinstance(mapped, list):
        for item in mapped:
            if isinstance(item, str) and item.strip():
                candidates.append(item.strip())

    if rapor_sql_kod not in candidates:
        candidates.append(rapor_sql_kod)

    return candidates


def _extract_sql_text(payload):
    # Format-1: [{fieldName, fieldValue, ...}] benzeri liste cevap
    if isinstance(payload, list):
        candidate_values = []
        for item in payload:
            if isinstance(item, dict):
                value = item.get("fieldValue")
                if isinstance(value, str) and value.strip():
                    candidate_values.append(value.strip())

        for value in candidate_values:
            upper_val = value.upper()
            if any(
                token in upper_val
                for token in ("SELECT ", "WITH ", "EXEC ", "{CALL ", "INSERT ", "UPDATE ", "DELETE ")
            ):
                return value

        if candidate_values:
            return candidate_values[0]

    # Format-2: {"data": {"raporAnaSql": "...", "raporProjeSql": "..."}}
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, dict):
            for key in ("raporAnaSql", "raporProjeSql", "raporSql", "sql", "query"):
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

        # Bazı implementasyonlarda SQL üst seviyede olabilir
        for key in ("raporAnaSql", "raporProjeSql", "raporSql", "sql", "query"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return None


def _safe_format_sql(sql_text, params):
    if not params:
        return sql_text

    format_map = {key: str(value) for key, value in params.items()}

    def _replace(match):
        key = match.group(1)
        return format_map.get(key, match.group(0))

    formatted = _PLACEHOLDER_RE.sub(_replace, sql_text)

    # Rapor SQL tarafinda sik gecen alternatif placeholder adlari
    # Ornek: '@BASLANGIC_TRH', '@BITIS_TRH'
    alias_values = {
        "BASLANGIC_TRH": format_map.get("start_date", ""),
        "BITIS_TRH": format_map.get("end_date", ""),
    }

    for alias, value in alias_values.items():
        if not value:
            continue
        # Çift tırnaklı, sonu @ olan vs. her türlü varyasyonu temiz bir şekilde değiştirelim
        formatted = formatted.replace(f"'@{alias}@'", f"'{value}'")
        formatted = formatted.replace(f"@{alias}@", f"'{value}'")
        formatted = formatted.replace(f"'@{alias}'", f"'{value}'")
        formatted = formatted.replace(f"@{alias}", f"'{value}'")

    # @PARAM@ formatindaki token'lar (or: @KADRO_UNVAN_ID@, @Id@)
    # Parametre map'inde karsiligi varsa onu, yoksa NULL kullan.
    def _replace_at_token(match):
        token = match.group(1)
        value = (
            format_map.get(token)
            or format_map.get(token.lower())
            or format_map.get(token.upper())
        )
        if value is None or value == "":
            return "NULL"
        return f"'{value}'"

    formatted = _AT_TOKEN_RE.sub(_replace_at_token, formatted)

    return formatted


def _get_remote_sql_single_code(rapor_sql_kod, timeout=10):
    """
    Tek bir raporSqlKod icin API cagrisi yapar.
    """
    body = json.dumps(
        [
            {
                "fieldName": "raporSqlKod",
                "fieldValue": rapor_sql_kod,
                "operator": "EQUAL",
            }
        ]
    ).encode("utf-8")

    req = request.Request(
        _default_api_url(),
        data=body,
        headers=_api_headers(),
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            payload = json.loads(raw)
            # DEBUG: Payload'ı görelim
            with open(r"c:\Users\ENES\Desktop\KDS_enson\KDS\flask_app\api_payload_debug.txt", "w", encoding="utf-8") as f:
                f.write(json.dumps(payload, indent=2, ensure_ascii=False))
            return _extract_sql_text(payload)
    except (error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        print(f"Rapor SQL API hatasi ({rapor_sql_kod}): {exc}")
        return None


def get_remote_sql(rapor_sql_kod, params=None, timeout=10):
    """
    Rapor API'den SQL metni ceker.
    Kod eslestirmesi varsa adaylari sirasiyla dener.
    """
    for candidate in _resolve_kod_candidates(rapor_sql_kod):
        sql_text = _get_remote_sql_single_code(candidate, timeout=timeout)
        if sql_text:
            if candidate != rapor_sql_kod:
                print(f"Rapor SQL kod eslesmesi kullanildi: {rapor_sql_kod} -> {candidate}")
            return _safe_format_sql(sql_text, params or {})

    return None
