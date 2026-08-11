
import os
import re
import json
import time
import socket
import requests
import base64

from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, parse_qs


# =========================
# НАСТРОЙКИ
# =========================

GH_USER = os.getenv("GH_USER")
GH_REPO = os.getenv("GH_REPO")
TOKEN = os.getenv("GH_TOKEN6")

FILE_PATH = "server.json"

SOURCES = [
    "https://raw.githubusercontent.com/ShadowException/VPN/refs/heads/main/configs/VPN-cat"
]

BANNED_COUNTRIES = ["RU", "CN", "KP", "IR"]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

MAX_SERVERS = 200


# =========================
# СТРАНЫ
# =========================

RU_COUNTRIES = {
    "US": "США",
    "DE": "Германия",
    "NL": "Нидерланды",
    "FI": "Финляндия",
    "SE": "Швеция",
    "PL": "Польша",
    "EE": "Эстония",
    "LV": "Латвия",
    "LT": "Литва",
    "FR": "Франция",
    "GB": "Великобритания",
    "CH": "Швейцария",
    "NO": "Норвегия",
    "IT": "Италия",
    "ES": "Испания",
    "CZ": "Чехия",
    "AT": "Австрия",
    "BE": "Бельгия",
    "DK": "Дания",
    "RO": "Румыния",
    "BG": "Болгария",
    "TR": "Турция",
    "GE": "Грузия",
    "KZ": "Казахстан",
    "UA": "Украина",
    "CA": "Канада",
    "JP": "Япония",
    "SG": "Сингапур",
    "AU": "Австралия",
    "IN": "Индия",
    "IL": "Израиль",
    "KR": "Южная Корея",
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

    except Exception:
        pass

    return None


# =========================
# COUNTRY
# =========================

def get_country_info(host):
    try:
        ip = socket.gethostbyname(host)

        r = requests.get(
            f"https://ipwho.is/{ip}",
            headers=HEADERS,
            timeout=10
        )

        data = r.json()

        if not data.get("success"):
            return None, None

        code = data.get("country_code")

        if not code:
            return None, None

        if code in BANNED_COUNTRIES:
            return None, None

        return code, RU_COUNTRIES.get(code, code)

    except Exception:
        return None, None


# =========================
# VLESS FILTER
# =========================

def is_valid_vless(url):
    try:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)

        transport = qs.get("type", [""])[0].lower()
        security = qs.get("security", [""])[0].lower()

        if transport != "tcp":
            return False

        if security not in ["tls", "reality"]:
            return False

        return True

    except Exception:
        return False


# =========================
# PROCESS
# =========================

def process_key(key):
    try:
        key = key.strip()

        if not key:
            return None

        main_part = key.split("#")[0]

        if not main_part.startswith("vless://"):
            return None

        if not is_valid_vless(main_part):
            return None

        parsed = urlparse(main_part)

        host = parsed.hostname
        port = parsed.port or 443

        if not host:
            return None

        ping = get_ping(host, port)

        if ping is None:
            return None

        code, country = get_country_info(host)

        if not code:
            return None

        emoji = "".join(
            chr(127397 + ord(c))
            for c in code
        )

        return {
            "config": main_part,
            "country_code": code,
            "country": country,
            "flag": emoji,
            "ping": ping
        }

    except Exception:
        return None


# =========================
# GITHUB
# =========================

def update_repo(content):
    url = (
        f"https://api.github.com/repos/"
        f"{GH_USER}/{GH_REPO}/contents/{FILE_PATH}"
    )

    headers = {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    sha = None

    try:
        r = requests.get(url, headers=headers, timeout=15)

        if r.status_code == 200:
            sha = r.json().get("sha")

    except Exception:
        pass

    encoded = base64.b64encode(
        content.encode("utf-8")
    ).decode()

    payload = {
        "message": "Auto JSON VPN Update",
        "content": encoded,
        "branch": "main"
    }

    if sha:
        payload["sha"] = sha

    r = requests.put(
        url,
        headers=headers,
        json=payload,
        timeout=30
    )

    if r.status_code not in [200, 201]:
        raise Exception(
            f"GitHub error {r.status_code}: {r.text}"
        )


# =========================
# MAIN
# =========================

def run_once():

    all_keys = []

    # Получаем источники
    for src in SOURCES:
        try:
            r = requests.get(
                src,
                headers=HEADERS,
                timeout=20
            )

            found = re.findall(
                r"vless://[^\s]+",
                r.text
            )

            all_keys.extend(found)

        except Exception:
            continue

    # Убираем дубликаты
    unique_keys = list(set(all_keys))

    print(f"Found: {len(unique_keys)} VLESS configs")

    # Проверяем сервера
    with ThreadPoolExecutor(max_workers=30) as executor:
        results = list(
            filter(
                None,
                executor.map(
                    process_key,
                    unique_keys
                )
            )
        )

    # Сначала самые быстрые
    results.sort(
        key=lambda x: x["ping"]
    )

    # Лимит
    results = results[:MAX_SERVERS]

    # =========================
    # ОДИН JSON-СЕРВЕР
    # =========================

    server = {
        "name": "Халява ВПН | Auto 📡",
        "type": "auto",
        "updated": int(time.time()),
        "servers": results
    }

    content = json.dumps(
        server,
        ensure_ascii=False,
        indent=2
    )

    update_repo(content)

    print(
        f"DONE: {len(results)} configs"
    )


if __name__ == "__main__":
    run_once()
