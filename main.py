import requests
import os
import re
import socket
import time
import json
import base64
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, parse_qs

# =========================
# НАСТРОЙКИ
# =========================

GITHUB_USER = os.getenv("GH_USER24")
REPO_NAME = os.getenv("GH_REPO24")
TOKEN = os.getenv("GH_TOKEN24")

FILE_PATH = "config.json"

SOURCES = [
    "https://raw.githubusercontent.com/ShadowException/VPN/refs/heads/main/configs/VPN-cat"
]

BANNED_COUNTRIES = ['RU', 'CN', 'KP', 'IR']

HEADERS = {"User-Agent": "Mozilla/5.0"}

SELECTOR_TAG = "🇪🇺 АВТОВЫБОР | WI-FI"
MAX_SERVERS = 50  # сколько лучших серверов класть в urltest-группу

# =========================
# СТРАНЫ (для тегов отдельных outbound'ов)
# =========================

RU_COUNTRIES = {
    "AF": "Афганистан", "AL": "Албания", "DZ": "Алжир", "AS": "Американское Самоа",
    "AD": "Андорра", "AO": "Ангола", "AI": "Ангилья", "AQ": "Антарктида",
    "AG": "Антигуа и Барбуда", "AR": "Аргентина", "AM": "Армения", "AW": "Аруба",
    "AU": "Австралия", "AT": "Австрия", "AZ": "Азербайджан",
    "BS": "Багамы", "BH": "Бахрейн", "BD": "Бангладеш", "BB": "Барбадос",
    "BY": "Беларусь", "BE": "Бельгия", "BZ": "Белиз", "BJ": "Бенин",
    "BM": "Бермуды", "BT": "Бутан", "BO": "Боливия", "BA": "Босния и Герцеговина",
    "BW": "Ботсвана", "BR": "Бразилия", "BN": "Бруней", "BG": "Болгария",
    "BF": "Буркина-Фасо", "BI": "Бурунди",
    "KH": "Камбоджа", "CM": "Камерун", "CA": "Канада", "CV": "Кабо-Верде",
    "KY": "Каймановы острова", "CF": "ЦАР", "TD": "Чад", "CL": "Чили",
    "CN": "Китай", "CO": "Колумбия", "KM": "Коморы", "CG": "Конго",
    "CR": "Коста-Рика", "HR": "Хорватия", "CU": "Куба", "CY": "Кипр", "CZ": "Чехия",
    "DK": "Дания", "DJ": "Джибути", "DM": "Доминика", "DO": "Доминиканская Республика",
    "EC": "Эквадор", "EG": "Египет", "SV": "Сальвадор", "GQ": "Экваториальная Гвинея",
    "ER": "Эритрея", "EE": "Эстония", "ET": "Эфиопия",
    "FJ": "Фиджи", "FI": "Финляндия", "FR": "Франция",
    "GA": "Габон", "GM": "Гамбия", "GE": "Грузия", "DE": "Германия", "GH": "Гана",
    "GI": "Гибралтар", "GR": "Греция", "GL": "Гренландия", "GD": "Гренада",
    "GU": "Гуам", "GT": "Гватемала", "GN": "Гвинея", "GW": "Гвинея-Бисау", "GY": "Гайана",
    "HT": "Гаити", "HN": "Гондурас", "HK": "Гонконг", "HU": "Венгрия",
    "IS": "Исландия", "IN": "Индия", "ID": "Индонезия", "IR": "Иран", "IQ": "Ирак",
    "IE": "Ирландия", "IL": "Израиль", "IT": "Италия",
    "JM": "Ямайка", "JP": "Япония", "JO": "Иордания",
    "KZ": "Казахстан", "KE": "Кения", "KI": "Кирибати", "KP": "Северная Корея",
    "KR": "Южная Корея", "KW": "Кувейт", "KG": "Кыргызстан",
    "LA": "Лаос", "LV": "Латвия", "LB": "Ливан", "LS": "Лесото", "LR": "Либерия",
    "LY": "Ливия", "LI": "Лихтенштейн", "LT": "Литва", "LU": "Люксембург",
    "MO": "Макао", "MK": "Северная Македония", "MG": "Мадагаскар", "MW": "Малави",
    "MY": "Малайзия", "MV": "Мальдивы", "ML": "Мали", "MT": "Мальта",
    "MH": "Маршалловы острова", "MQ": "Мартиника", "MR": "Мавритания", "MU": "Маврикий",
    "MX": "Мексика", "FM": "Микронезия", "MD": "Молдова", "MC": "Монако",
    "MN": "Монголия", "ME": "Черногория", "MA": "Марокко", "MZ": "Мозамбик", "MM": "Мьянма",
    "NA": "Намибия", "NR": "Науру", "NP": "Непал", "NL": "Нидерланды",
    "NZ": "Новая Зеландия", "NI": "Никарагуа", "NE": "Нигер", "NG": "Нигерия", "NO": "Норвегия",
    "OM": "Оман",
    "PK": "Пакистан", "PW": "Палау", "PS": "Палестина", "PA": "Панама",
    "PG": "Папуа — Новая Гвинея", "PY": "Парагвай", "PE": "Перу", "PH": "Филиппины",
    "PL": "Польша", "PT": "Португалия", "PR": "Пуэрто-Рико",
    "QA": "Катар",
    "RO": "Румыния", "RU": "Россия", "RW": "Руанда",
    "KN": "Сент-Китс и Невис", "LC": "Сент-Люсия", "VC": "Сент-Винсент и Гренадины",
    "WS": "Самоа", "SM": "Сан-Марино", "ST": "Сан-Томе и Принсипи", "SA": "Саудовская Аравия",
    "SN": "Сенегал", "RS": "Сербия", "SC": "Сейшелы", "SL": "Сьерра-Леоне", "SG": "Сингапур",
    "SK": "Словакия", "SI": "Словения", "SB": "Соломоновы острова", "SO": "Сомали",
    "ZA": "ЮАР", "ES": "Испания", "LK": "Шри-Ланка", "SD": "Судан", "SR": "Суринам",
    "SZ": "Эсватини", "SE": "Швеция", "CH": "Швейцария", "SY": "Сирия",
    "TW": "Тайвань", "TJ": "Таджикистан", "TZ": "Танзания", "TH": "Таиланд",
    "TL": "Тимор-Лесте", "TG": "Того", "TO": "Тонга", "TT": "Тринидад и Тобаго",
    "TN": "Тунис", "TR": "Турция", "TM": "Туркменистан", "TV": "Тувалу",
    "UG": "Уганда", "UA": "Украина", "AE": "ОАЭ", "GB": "Великобритания", "US": "США",
    "UY": "Уругвай", "UZ": "Узбекистан",
    "VU": "Вануату", "VA": "Ватикан", "VE": "Венесуэла", "VN": "Вьетнам",
    "YE": "Йемен",
    "ZM": "Замбия", "ZW": "Зимбабве"
}

# =========================
# PING
# =========================

def get_ping(host, port):
    try:
        ip = socket.gethostbyname(host)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        start = time.time()
        result = sock.connect_ex((ip, port))
        ping = int((time.time() - start) * 1000)
        sock.close()
        if result == 0:
            return ping
    except:
        pass
    return None

# =========================
# COUNTRY
# =========================

def get_country_info(host):
    try:
        ip = socket.gethostbyname(host)
        r = requests.get(f"https://ipwho.is/{ip}", headers=HEADERS, timeout=10)
        data = r.json()
        if not data.get("success"):
            return "UN", "Server"
        code = data.get("country_code")
        if not code:
            return "UN", "Server"
        if code in BANNED_COUNTRIES:
            return None, None
        return code, RU_COUNTRIES.get(code, code)
    except:
        return "UN", "Server"

# =========================
# VLESS FILTER
# =========================

def is_valid_vless(main_part: str) -> bool:
    try:
        parsed = urlparse(main_part)
        qs = parse_qs(parsed.query)
        security = (qs.get("security", [""])[0] or "").lower()
        transport = (qs.get("type", [""])[0] or "").lower()
        allowed_transports = ["tcp"]
        allowed_security = ["tls", "reality"]
        if transport not in allowed_transports:
            return False
        if security not in allowed_security:
            return False
        return True
    except:
        return False

# =========================
# VLESS -> SING-BOX OUTBOUND
# =========================

def vless_to_outbound(main_part: str, tag: str):
    try:
        without_scheme = main_part[len("vless://"):]
        if '@' not in without_scheme:
            return None

        uuid, rest = without_scheme.split('@', 1)

        if '?' in rest:
            hostport, query = rest.split('?', 1)
        else:
            hostport, query = rest, ''

        if ':' in hostport:
            host, port_str = hostport.rsplit(':', 1)
            port = int(port_str)
        else:
            host, port = hostport, 443

        qs = parse_qs(query)

        def g(key, default=''):
            return qs.get(key, [default])[0]

        security = g('security', 'none').lower()
        flow = g('flow', '')
        sni = g('sni', host)
        fp = g('fp', 'chrome')
        pbk = g('pbk', '')
        sid = g('sid', '')

        outbound = {
            "type": "vless",
            "tag": tag,
            "server": host,
            "server_port": port,
            "uuid": uuid,
            "packet_encoding": "xudp",
        }

        if flow:
            outbound["flow"] = flow

        tls = {
            "enabled": True,
            "server_name": sni,
            "utls": {"enabled": True, "fingerprint": fp or "chrome"},
        }

        if security == "reality":
            tls["reality"] = {
                "enabled": True,
                "public_key": pbk,
                "short_id": sid,
            }

        outbound["tls"] = tls
        return outbound

    except:
        return None

# =========================
# PROCESS ONE KEY
# =========================

def process_key(key):
    try:
        key = key.strip()
        if not key:
            return None

        main_part = key.split('#')[0]

        if not main_part.startswith("vless://"):
            return None

        if not is_valid_vless(main_part):
            return None

        host_match = re.search(r'@([^:/?#\s]+):?(\d+)?', main_part)
        if not host_match:
            return None

        host = host_match.group(1)

        try:
            port = int(host_match.group(2))
        except:
            port = 443

        ping = get_ping(host, port)
        if ping is None:
            return None

        code, country = get_country_info(host)
        if not code:
            return None

        return {
            "main": main_part,
            "code": code,
            "country": country,
            "ping": ping,
        }

    except:
        return None

# =========================
# BUILD SING-BOX CONFIG
# =========================

def build_singbox_config(results):
    outbounds = []
    tags = []

    for idx, item in enumerate(results, 1):
        tag = f"{item['country']} #{idx}"
        outbound = vless_to_outbound(item["main"], tag)
        if outbound is None:
            continue
        outbounds.append(outbound)
        tags.append(tag)

    urltest = {
        "type": "urltest",
        "tag": SELECTOR_TAG,
        "outbounds": tags,
        "url": "https://www.gstatic.com/generate_204",
        "interval": "3m",
        "tolerance": 50,
    }

    config = {
        "log": {"level": "warning", "timestamp": True},
        "dns": {
            "servers": [
                {"tag": "remote", "address": "https://1.1.1.1/dns-query"},
                {"tag": "local", "address": "local", "detour": "direct"},
            ],
            "rules": [{"outbound": "any", "server": "local"}],
        },
        "inbounds": [
            {
                "type": "mixed",
                "tag": "mixed-in",
                "listen": "127.0.0.1",
                "listen_port": 2080,
            }
        ],
        "outbounds": outbounds + [
            urltest,
            {"type": "direct", "tag": "direct"},
            {"type": "block", "tag": "block"},
        ],
        "route": {
            "rules": [
                {"protocol": "dns", "outbound": "direct"},
            ],
            "final": SELECTOR_TAG,
            "auto_detect_interface": True,
        },
    }

    return config

# =========================
# GITHUB
# =========================

def update_repo(content: str):
    if not GITHUB_USER or not REPO_NAME or not TOKEN:
        raise RuntimeError(
            f"Не заданы секреты: GH_USER={bool(GITHUB_USER)}, "
            f"GH_REPO={bool(REPO_NAME)}, GH_TOKEN6={bool(TOKEN)}"
        )

    url = f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/contents/{FILE_PATH}"

    headers = {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

    sha = None
    r = requests.get(url, headers=headers)
    print(f"GET {url} -> {r.status_code}")
    if r.status_code == 200:
        sha = r.json().get("sha")
    elif r.status_code != 404:
        # 404 нормально при первом запуске (файла ещё нет), всё остальное — проблема
        print(r.text)

    encoded = base64.b64encode(content.encode()).decode()

    payload = {
        "message": f"Auto update {time.strftime('%H:%M:%S')}",
        "content": encoded,
        "branch": "main",
    }

    if sha:
        payload["sha"] = sha

    put_r = requests.put(url, headers=headers, json=payload)
    print(f"PUT {url} -> {put_r.status_code}")

    if put_r.status_code not in (200, 201):
        print(put_r.text)
        raise RuntimeError(
            f"Не удалось записать {FILE_PATH} в репозиторий: "
            f"{put_r.status_code} {put_r.text}"
        )

# =========================
# MAIN
# =========================

def run_once():
    all_keys = []

    for src in SOURCES:
        try:
            r = requests.get(src, headers=HEADERS, timeout=15)
            found = re.findall(r'vless://[^\s]+', r.text)
            all_keys.extend(found)
        except:
            continue

    unique_keys = list(set(all_keys))

    with ThreadPoolExecutor(max_workers=30) as ex:
        results = list(filter(None, ex.map(process_key, unique_keys)))

    results.sort(key=lambda x: x["ping"])
    results = results[:MAX_SERVERS]

    config = build_singbox_config(results)
    content = json.dumps(config, ensure_ascii=False, indent=2)

    update_repo(content)

    print(f"DONE: {len(results)} servers packed into {SELECTOR_TAG}")

if __name__ == "__main__":
    run_once()
