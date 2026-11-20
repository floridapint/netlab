"""Чистая логика IPv4: подсети, маски, классы адресов (без tkinter)."""
from __future__ import annotations

import ipaddress

from ..i18n import _

RFC1918 = [
    ipaddress.IPv4Network("10.0.0.0/8"),
    ipaddress.IPv4Network("172.16.0.0/12"),
    ipaddress.IPv4Network("192.168.0.0/16"),
]
CGNAT = ipaddress.IPv4Network("100.64.0.0/10")


def prefix_to_mask(prefix: int) -> str:
    return str(ipaddress.IPv4Network(f"0.0.0.0/{int(prefix)}").netmask)


def mask_to_prefix(mask: str) -> int:
    """'255.255.255.0' -> 24. Бросает ValueError для «дырявых» масок."""
    return ipaddress.IPv4Network(f"0.0.0.0/{mask.strip()}").prefixlen


def to_bin(ip: str) -> str:
    return ".".join(f"{int(o):08b}" for o in str(ip).split("."))


def ip_class(ip: str) -> str:
    first = int(str(ip).split(".")[0])
    if first < 128:
        return "A"
    if first < 192:
        return "B"
    if first < 224:
        return "C"
    if first < 240:
        return "D (multicast)"
    return _("E (резерв)")


def is_rfc1918(ip: str) -> bool:
    a = ipaddress.IPv4Address(ip)
    return any(a in n for n in RFC1918)


def addr_kind(ip: str) -> str:
    a = ipaddress.IPv4Address(ip)
    if a.is_loopback:
        return _("loopback (127.0.0.0/8) — «сам себе»")
    if a.is_link_local:
        return _("link-local (169.254.0.0/16) — APIPA, DHCP не ответил")
    if a.is_multicast:
        return _("multicast (224.0.0.0/4) — групповая рассылка")
    if is_rfc1918(ip):
        return _("частный (RFC 1918) — не маршрутизируется в Интернете")
    if a in CGNAT:
        return _("CGNAT провайдера (100.64.0.0/10)")
    if a.is_unspecified:
        return _("неопределённый адрес 0.0.0.0")
    if int(a) == 0xFFFFFFFF:
        return _("ограниченный broadcast")
    if a.is_reserved or a.is_private:
        return _("зарезервированный / служебный")
    return _("публичный (глобально маршрутизируемый)")


def subnet_info(ip: str, prefix: int) -> dict:
    prefix = int(prefix)
    iface = ipaddress.IPv4Interface(f"{ip}/{prefix}")
    net = iface.network
    if prefix <= 30:
        first = net.network_address + 1
        last = net.broadcast_address - 1
        hosts = net.num_addresses - 2
    elif prefix == 31:  # RFC 3021, линк точка-точка
        first, last, hosts = net.network_address, net.broadcast_address, 2
    else:
        first = last = net.network_address
        hosts = 1
    return {
        "ip": str(iface.ip),
        "prefix": prefix,
        "mask": str(net.netmask),
        "wildcard": str(net.hostmask),
        "network": str(net.network_address),
        "broadcast": str(net.broadcast_address),
        "first": str(first),
        "last": str(last),
        "hosts": hosts,
        "total": net.num_addresses,
        "class": ip_class(str(iface.ip)),
        "kind": addr_kind(str(iface.ip)),
    }


def parse_cidr(text: str, default_prefix: int = 24) -> tuple[str, int]:
    """Понимает '10.0.0.5/8', '10.0.0.5 255.0.0.0', '10.0.0.5'."""
    t = text.strip().replace("\\", "/")
    if not t:
        raise ValueError(_("Введите адрес, например 192.168.1.10/24"))
    if "/" in t:
        ip, _sep, pfx = t.partition("/")
        pfx = pfx.strip()
        prefix = mask_to_prefix(pfx) if "." in pfx else int(pfx)
    elif " " in t:
        ip, mask = t.split(None, 1)
        prefix = mask_to_prefix(mask)
    else:
        ip, prefix = t, default_prefix
    ip = ip.strip()
    ipaddress.IPv4Address(ip)  # валидация
    if not 0 <= prefix <= 32:
        raise ValueError(_("Префикс должен быть от 0 до 32"))
    return ip, prefix


def block_explanation(ip: str, prefix: int) -> str:
    """Пошаговое объяснение расчёта подсети методом «размера блока» (markup)."""
    info = subnet_info(ip, prefix)
    mask_o = [int(x) for x in info["mask"].split(".")]
    ip_o = [int(x) for x in ip.split(".")]
    lines = [_("Маска /{p} = `{mask}`.").format(p=prefix, mask=info["mask"])]
    idx = next((i for i, m in enumerate(mask_o) if m != 255), None)
    if idx is not None:
        m = mask_o[idx]
        block = 256 - m
        start = ip_o[idx] // block * block
        lines.append(_("Первый «неполный» октет маски — {n}-й (= {m}). Размер блока = 256 − {m} = **{block}**.")
                     .format(n=idx + 1, m=m, block=block))
        lines.append(_("{n}-й октет адреса = {o}; {o} // {block} × {block} = **{start}** — начало блока.")
                     .format(n=idx + 1, o=ip_o[idx], block=block, start=start))
        lines.append(_("Октеты правее обнуляем → сеть `{net}`; ставим максимум (конец блока {end}, дальше 255) → "
                       "broadcast `{bc}`.").format(net=info["network"], end=start + block - 1, bc=info["broadcast"]))
    if prefix <= 30:
        lines.append(_("Хосты: от `{first}` до `{last}`, всего 2^{bits} − 2 = **{hosts}**.")
                     .format(first=info["first"], last=info["last"], bits=32 - prefix, hosts=info["hosts"]))
    return "\n".join(lines)
