"""Реальное TLS-подключение к серверу и разбор того, что удалось узнать."""
from __future__ import annotations

import hashlib
import socket
import ssl
import time

from ..i18n import N_, _


def _name_dict(seq) -> dict:
    out = {}
    for rdn in seq or ():
        for key, value in rdn:
            out[key] = value
    return out


def _try_version(host: str, port: int, version, timeout: float) -> bool:
    ctx = ssl.create_default_context()
    try:
        ctx.minimum_version = version
        ctx.maximum_version = version
    except (ValueError, ssl.SSLError):
        return False
    try:
        with socket.create_connection((host, port), timeout=timeout) as raw:
            with ctx.wrap_socket(raw, server_hostname=host):
                return True
    except (OSError, ssl.SSLError):
        return False


def probe(host: str, port: int = 443, timeout: float = 6.0, check_versions: bool = True) -> dict:
    host = host.strip().removeprefix("https://").removeprefix("http://").split("/")[0]
    if ":" in host:
        host, _sep, p = host.partition(":")
        port = int(p)
    result = {"host": host, "port": port, "ok": False}

    t0 = time.perf_counter()
    try:
        raw = socket.create_connection((host, port), timeout=timeout)
    except socket.gaierror:
        result["error"] = "dns"
        result["message"] = _("Не удалось найти адрес для «{host}» (DNS). Проверьте имя и подключение к Интернету.").format(host=host)
        return result
    except OSError as e:
        result["error"] = "tcp"
        result["message"] = _("TCP-подключение не удалось: {e}").format(e=e)
        return result
    result["ip"] = raw.getpeername()[0]
    result["tcp_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    ctx = ssl.create_default_context()
    try:
        ctx.set_alpn_protocols(["h2", "http/1.1"])
    except NotImplementedError:
        pass
    t1 = time.perf_counter()
    try:
        with ctx.wrap_socket(raw, server_hostname=host) as s:
            result["tls_ms"] = round((time.perf_counter() - t1) * 1000, 1)
            result["version"] = s.version()
            name, _proto, bits = s.cipher()
            result["cipher"] = name
            result["cipher_bits"] = bits
            result["alpn"] = s.selected_alpn_protocol()
            cert = s.getpeercert()
            der = s.getpeercert(binary_form=True) or b""
    except ssl.SSLCertVerificationError as e:
        result["error"] = "cert"
        result["message"] = getattr(e, "verify_message", None) or str(e)
        result["verify_code"] = getattr(e, "verify_code", None)
        return result
    except ssl.SSLError as e:
        result["error"] = "tls"
        result["message"] = _("Ошибка TLS: {e}").format(e=e.reason or e)
        return result
    except OSError as e:
        result["error"] = "tcp"
        result["message"] = _("Соединение оборвалось: {e}").format(e=e)
        return result

    subject = _name_dict(cert.get("subject"))
    issuer = _name_dict(cert.get("issuer"))
    result.update(
        ok=True,
        subject_cn=subject.get("commonName", "—"),
        issuer_cn=issuer.get("commonName", "—"),
        issuer_org=issuer.get("organizationName", ""),
        not_before=cert.get("notBefore", "—"),
        not_after=cert.get("notAfter", "—"),
        san=[v for k, v in cert.get("subjectAltName", ()) if k == "DNS"],
        serial=cert.get("serialNumber", "—"),
        sha256=hashlib.sha256(der).hexdigest().upper() if der else "—",
    )
    try:
        result["days_left"] = int((ssl.cert_time_to_seconds(cert["notAfter"]) - time.time()) / 86400)
    except (KeyError, ValueError):
        result["days_left"] = None

    if check_versions:
        result["versions"] = {
            "TLS 1.3": _try_version(host, port, ssl.TLSVersion.TLSv1_3, timeout),
            "TLS 1.2": _try_version(host, port, ssl.TLSVersion.TLSv1_2, timeout),
        }
    return result


CERT_ERRORS = {
    10: N_("Срок действия сертификата **истёк**. Владелец сайта забыл его обновить — либо часы на вашем ПК идут неверно."),
    18: N_("Сертификат **самоподписанный**: его никто не заверял, браузер не может проверить, что это действительно тот сайт."),
    19: N_("В цепочке есть **самоподписанный корневой** сертификат, которого нет в хранилище доверенных."),
    20: N_("Не удаётся найти издателя: цепочка не доходит до доверенного корневого CA (неизвестный или частный CA)."),
    62: N_("**Имя не совпадает**: сертификат выдан на другой домен. Классический признак ошибки настройки или атаки MITM."),
}
