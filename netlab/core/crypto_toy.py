"""Учебная криптография: Диффи–Хеллман на маленьких числах, лавинный эффект SHA-256,
разбор наборов шифров TLS. Не используйте это для настоящей защиты!"""
from __future__ import annotations

import hashlib

from ..i18n import N_, _


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    small = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for p in small:
        if n % p == 0:
            return n == p
    # Миллер–Рабин с фиксированными основаниями
    d, r = n - 1, 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for a in small:
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _i in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def dh_exchange(p: int, g: int, a: int, b: int) -> dict:
    A = pow(g, a, p)
    B = pow(g, b, p)
    return {"A": A, "B": B, "s_alice": pow(B, a, p), "s_bob": pow(A, b, p)}


def brute_force_dlog(g: int, target: int, p: int, limit: int = 2_000_000):
    """Ева ищет x: g^x mod p = target. Возвращает (x, попыток) или (None, попыток)."""
    value = 1
    for x in range(0, min(p, limit)):
        if value == target:
            return x, x + 1
        value = value * g % p
    return None, min(p, limit)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def bit_diff(hex1: str, hex2: str) -> int:
    return bin(int(hex1, 16) ^ int(hex2, 16)).count("1")


# ---------------------------------------------------------------- наборы шифров

GLOSSARY = {
    "ECDHE": N_("Эфемерный Диффи–Хеллман на эллиптических кривых: для каждого сеанса новый ключ → есть прямая секретность (PFS)."),
    "DHE": N_("Эфемерный «классический» Диффи–Хеллман: есть PFS, но медленнее ECDHE."),
    "ECDH": N_("Статический ECDH: ключ не меняется между сеансами → нет прямой секретности."),
    "DH": N_("Статический Диффи–Хеллман → нет прямой секретности."),
    "RSA_KX": N_("Клиент шифрует секрет открытым RSA-ключом сервера. Нет PFS: утечка ключа сервера раскрывает весь записанный трафик. Удалено в TLS 1.3."),
    "PSK": N_("Заранее согласованный общий ключ (Pre-Shared Key)."),
    "RSA": N_("Сервер подтверждает подлинность RSA-подписью (в сертификате RSA-ключ)."),
    "ECDSA": N_("Сервер подтверждает подлинность подписью ECDSA (ключ на эллиптической кривой — короче и быстрее RSA)."),
    "DSS": N_("Подпись DSA — устарела."),
    "ANON": N_("Без аутентификации! Уязвимо к атаке «человек посередине»."),
    "AES_128_GCM": N_("AES с 128-битным ключом в режиме GCM — AEAD: шифрование + проверка целостности за один проход."),
    "AES_256_GCM": N_("AES с 256-битным ключом в режиме GCM (AEAD)."),
    "AES_128_CCM": N_("AES-128 в режиме CCM (AEAD), популярен во встраиваемых устройствах."),
    "CHACHA20_POLY1305": N_("Потоковый шифр ChaCha20 + аутентификатор Poly1305 (AEAD). Быстр на телефонах без аппаратного AES."),
    "AES_128_CBC": N_("AES-128 в режиме CBC + отдельный HMAC. Исторически уязвим к padding-oracle (Lucky13, POODLE-TLS)."),
    "AES_256_CBC": N_("AES-256 в режиме CBC + отдельный HMAC. Не AEAD, удалён из TLS 1.3."),
    "3DES_EDE_CBC": N_("Тройной DES — блок 64 бита, атака Sweet32. Небезопасен."),
    "RC4_128": N_("Потоковый шифр RC4 — сломан, запрещён (RFC 7465)."),
    "NULL": N_("Без шифрования вообще!"),
    "SHA256": N_("SHA-256: используется в PRF/HKDF для вывода ключей (и в HMAC для не-AEAD шифров)."),
    "SHA384": N_("SHA-384: для вывода ключей (обычно в паре с AES-256)."),
    "SHA": N_("HMAC-SHA1 — устаревающий хэш для целостности."),
    "MD5": N_("MD5 — сломанная хэш-функция. Небезопасно."),
    "AEAD": N_("MAC встроен в AEAD-шифр, отдельный HMAC не нужен."),
}

_KX = {"ECDHE", "DHE", "EDH", "ECDH", "DH", "RSA", "PSK", "SRP", "AECDH", "ADH"}
_AUTH = {"RSA", "ECDSA", "DSS", "PSK", "ANON", "AECDH", "ADH"}
_MACS = {"SHA", "SHA256", "SHA384", "MD5"}


def _norm_cipher(c: str) -> str:
    """OpenSSL 'AES128-GCM' -> IANA-подобное 'AES_128_GCM'."""
    c = c.replace("-", "_")
    repl = {
        "AES128_GCM": "AES_128_GCM", "AES256_GCM": "AES_256_GCM",
        "AES128": "AES_128_CBC", "AES256": "AES_256_CBC",
        "DES_CBC3": "3DES_EDE_CBC", "RC4": "RC4_128",
    }
    return repl.get(c, c)


def parse_cipher_suite(name: str) -> dict:
    s = name.strip().upper().replace(" ", "")
    res = {"name": s, "tls13": False, "kx": None, "auth": None, "cipher": None, "mac": None,
           "pfs": False, "aead": False, "warnings": []}
    if not s:
        raise ValueError(_("Введите название набора шифров"))

    if s.startswith("TLS_") and "_WITH_" not in s:
        cipher, _sep, mac = s[4:].rpartition("_")
        if not cipher:
            raise ValueError(_("Не похоже на набор шифров TLS 1.3 (пример: TLS_AES_128_GCM_SHA256)"))
        res.update(tls13=True, kx="ECDHE", auth="CERT", cipher=cipher, mac=mac)
    elif "_WITH_" in s:
        left, right = s.split("_WITH_", 1)
        left = left.split("_", 1)[1] if "_" in left else ""
        parts = [p for p in left.split("_") if p and p != "EXPORT"]
        if "EXPORT" in left:
            res["warnings"].append(_("EXPORT — намеренно ослабленная «экспортная» криптография 90-х (атаки FREAK, Logjam)."))
        if not parts:
            raise ValueError(_("Не удалось разобрать обмен ключами"))
        kx = parts[0]
        auth = parts[1] if len(parts) > 1 else ("RSA" if kx == "RSA" else kx)
        cipher, _sep, mac = right.rpartition("_")
        if right.endswith("CHACHA20_POLY1305_SHA256"):
            cipher, mac = "CHACHA20_POLY1305", "SHA256"
        res.update(kx=kx, auth=auth, cipher=cipher or right, mac=mac)
    else:
        tokens = [t for t in s.split("-") if t]
        if len(tokens) < 2:
            raise ValueError(_("Формат не распознан. Примеры: ECDHE-RSA-AES128-GCM-SHA256 или TLS_AES_256_GCM_SHA384"))
        kx, auth = "RSA", "RSA"
        if tokens[0] in _KX and tokens[0] != "RSA":
            kx = tokens.pop(0)
            if tokens and tokens[0] in _AUTH:
                auth = tokens.pop(0)
            elif kx in ("PSK", "SRP"):
                auth = kx
        mac = "AEAD"
        if tokens and tokens[-1] in _MACS:
            mac = tokens.pop()
        res.update(kx=kx, auth=auth, cipher=_norm_cipher("-".join(tokens)), mac=mac)

    if res["kx"] == "EDH":
        res["kx"] = "DHE"
    if res["kx"] == "ADH":
        res["kx"], res["auth"] = "DH", "ANON"
    if res["kx"] == "AECDH":
        res["kx"], res["auth"] = "ECDH", "ANON"

    c = res["cipher"] or ""
    res["aead"] = any(x in c for x in ("GCM", "CCM", "POLY1305"))
    res["pfs"] = res["tls13"] or res["kx"] in ("ECDHE", "DHE")

    w = res["warnings"]
    if "RC4" in c:
        w.append(_("RC4 сломан — запрещён в TLS (RFC 7465)."))
    if "DES" in c:
        w.append(_("DES/3DES — блок 64 бита, атака Sweet32. Небезопасно."))
    if c.startswith("NULL"):
        w.append(_("NULL-шифр — данные идут открытым текстом!"))
    if res["mac"] == "MD5":
        w.append(_("MD5 — сломанная хэш-функция."))
    if res["auth"] == "ANON":
        w.append(_("Анонимный обмен — нет проверки сервера, возможна MITM-атака."))
    if not res["pfs"]:
        w.append(_("Нет прямой секретности (PFS): кража ключа сервера раскроет записанный трафик."))
    if not res["aead"] and "NULL" not in c:
        w.append(_("Не AEAD (CBC + HMAC): допустимо, но устарело; в TLS 1.3 таких шифров нет."))
    return res


def explain_component(kind: str, value: str) -> str:
    v = (value or "").upper()
    if kind == "kx":
        if v == "RSA":
            return _(GLOSSARY["RSA_KX"])
        return _(GLOSSARY.get(v, N_("Механизм обмена ключами.")))
    if kind == "auth":
        if v == "CERT":
            return _("В TLS 1.3 алгоритм подписи согласуется отдельно (расширение signature_algorithms) — в имени набора его нет.")
        return _(GLOSSARY.get(v, N_("Способ аутентификации сервера.")))
    if kind == "cipher":
        return _(GLOSSARY.get(v, N_("Симметричный шифр для данных.")))
    if kind == "mac":
        return _(GLOSSARY.get(v, N_("Хэш-функция для целостности/вывода ключей.")))
    return ""


TLS_VERSIONS = [
    {"name": "SSL 2.0", "year": 1995, "status": "bad", "rfc": N_("запрещён RFC 6176"),
     "text": N_("Первая публичная версия от Netscape. Фундаментальные дефекты: одинаковые ключи для MAC и шифрования, "
                "нет защиты рукопожатия от подмены (downgrade), слабые экспортные шифры. Запрещён с 2011 года.")},
    {"name": "SSL 3.0", "year": 1996, "status": "bad", "rfc": N_("запрещён RFC 7568"),
     "text": N_("Переработанный протокол — основа всего последующего TLS. Сломан атакой **POODLE** (2014) "
                "из-за способа дополнения блоков в CBC. Запрещён в 2015 году.")},
    {"name": "TLS 1.0", "year": 1999, "status": "old", "rfc": N_("RFC 2246, устарел RFC 8996"),
     "text": N_("Стандарт IETF, по сути SSL 3.1. Уязвимости **BEAST** (предсказуемый IV в CBC), устаревшие MD5/SHA-1 в PRF. "
                "Браузеры отключили в 2020 году.")},
    {"name": "TLS 1.1", "year": 2006, "status": "old", "rfc": N_("RFC 4346, устарел RFC 8996"),
     "text": N_("Исправлен BEAST (явный IV), но остались старые хэши и нет AEAD-шифров. Официально устарел в 2021 году.")},
    {"name": "TLS 1.2", "year": 2008, "status": "ok", "rfc": "RFC 5246",
     "text": N_("Добавлены AEAD-шифры (**AES-GCM**), SHA-256 в PRF, гибкий выбор алгоритмов подписи. "
                "Безопасен, если отключены RSA-обмен ключами, CBC и старые шифры. Рукопожатие — **2 RTT**.")},
    {"name": "TLS 1.3", "year": 2018, "status": "good", "rfc": "RFC 8446",
     "text": N_("Радикально упрощён: только 5 наборов шифров, все — AEAD; обязательная прямая секретность (ECDHE/DHE); "
                "рукопожатие **1 RTT** (и 0-RTT при возобновлении); сертификат сервера передаётся зашифрованным; "
                "удалены RSA-обмен, CBC, RC4, SHA-1, сжатие, пересогласование.")},
]
