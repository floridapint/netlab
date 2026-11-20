"""Генераторы практических задач. Каждая функция принимает random.Random и возвращает Task."""
from __future__ import annotations

import ipaddress
import random
from dataclasses import dataclass, field

from ..i18n import _
from . import ipcalc
from .protocols import FLAG_COMBOS, PORTS, QUIZ_PORTS, TCP_FLAGS, flags_names

YES = ("да", "д", "так", "yes", "y", "+", "true", "1")
NO = ("нет", "н", "ні", "no", "n", "-", "false", "0")


def norm(value) -> str:
    return str(value).strip().lower().replace(" ", "").replace(",", ".").replace("ё", "е")


@dataclass
class Field:
    label: str
    answer: str
    accept: tuple = ()
    placeholder: str = ""

    def check(self, value: str) -> bool:
        v = norm(value)
        if not v:
            return False
        return v in {norm(self.answer), *(norm(a) for a in self.accept)}


@dataclass
class Task:
    text: str
    fields: list = field(default_factory=list)
    explain: str = ""


def _yes_no(flag: bool) -> Field:
    return Field(_("Ответ (да / нет)"), _("да") if flag else _("нет"), YES if flag else NO, _("да / нет"))


def _random_ip(rng: random.Random) -> str:
    kind = rng.random()
    if kind < 0.3:
        return f"192.168.{rng.randint(0, 255)}.{rng.randint(1, 254)}"
    if kind < 0.55:
        return f"10.{rng.randint(0, 255)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}"
    if kind < 0.75:
        return f"172.{rng.randint(16, 31)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}"
    return f"{rng.randint(1, 223)}.{rng.randint(0, 255)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}"


# ------------------------------------------------------------------ IP

def subnet_task(rng: random.Random) -> Task:
    prefix = rng.choice([8, 12, 16, 19, 20, 22, 23, 24, 25, 26, 26, 27, 27, 28, 28, 29, 30])
    ip = _random_ip(rng)
    info = ipcalc.subnet_info(ip, prefix)
    return Task(
        text=_("Дан адрес **`{ip}`**. Найдите параметры подсети.").format(ip=f"{ip}/{prefix}"),
        fields=[
            Field(_("Адрес сети"), info["network"]),
            Field(_("Широковещательный адрес"), info["broadcast"]),
            Field(_("Первый хост"), info["first"]),
            Field(_("Последний хост"), info["last"]),
            Field(_("Количество хостов"), str(info["hosts"])),
        ],
        explain=ipcalc.block_explanation(ip, prefix),
    )


def mask_task(rng: random.Random) -> Task:
    prefix = rng.randint(8, 30)
    mask = ipcalc.prefix_to_mask(prefix)
    bits = ipcalc.to_bin(mask)
    if rng.random() < 0.5:
        return Task(
            text=_("Запишите маску для префикса **/{p}** в десятичном виде.").format(p=prefix),
            fields=[Field(_("Маска"), mask, placeholder="255.255.x.x")],
            explain=_("/{p} — это {p} единиц слева:\n`{bits}`\nПереводим каждый октет в десятичный → `{mask}`.")
            .format(p=prefix, bits=bits, mask=mask),
        )
    return Task(
        text=_("Какой префикс соответствует маске **`{mask}`**?").format(mask=mask),
        fields=[Field(_("Префикс"), str(prefix), (f"/{prefix}",), _("например 24"))],
        explain=_("В двоичном виде:\n`{bits}`\nСчитаем единицы: **{p}** → /{p}.").format(bits=bits, p=prefix),
    )


def binary_task(rng: random.Random) -> Task:
    n = rng.randint(0, 255)
    b = f"{n:08b}"
    weights = [128, 64, 32, 16, 8, 4, 2, 1]
    parts = [str(w) for w, bit in zip(weights, b) if bit == "1"] or ["0"]
    table = "|" + "|".join(str(w) for w in weights) + "|\n|" + "|".join("---" for _w in weights) + "|\n|" + "|".join(b) + "|"
    expl = f"{table}\n{' + '.join(parts)} = **{n}**"
    if rng.random() < 0.5:
        return Task(
            text=_("Переведите октет **{n}** в двоичный вид (8 бит).").format(n=n),
            fields=[Field(_("Двоичное значение"), b, (f"{n:b}",), _("8 цифр"))],
            explain=expl,
        )
    return Task(
        text=_("Переведите октет **`{b}`** в десятичное число.").format(b=b),
        fields=[Field(_("Десятичное значение"), str(n))],
        explain=expl,
    )


def same_net_task(rng: random.Random) -> Task:
    prefix = rng.choice([22, 23, 24, 25, 26, 27, 28])
    base = ipaddress.IPv4Network(f"{_random_ip(rng)}/{prefix}", strict=False)
    size = base.num_addresses
    hosts = list(range(1, size - 1))
    ip1 = base.network_address + rng.choice(hosts)
    if rng.random() < 0.5:
        ip2 = base.network_address + rng.choice(hosts)
    else:
        up = rng.random() < 0.5 or int(base.network_address) < size
        neighbor = base.network_address + size if up else base.network_address - size
        ip2 = neighbor + rng.choice(hosts)
    n1 = ipcalc.subnet_info(str(ip1), prefix)["network"]
    n2 = ipcalc.subnet_info(str(ip2), prefix)["network"]
    verdict = (_("Совпадают → **да**, общаются напрямую, без маршрутизатора.") if n1 == n2
               else _("Различаются → **нет**, пакеты пойдут через маршрутизатор (шлюз)."))
    return Task(
        text=_("Находятся ли адреса **`{ip1}`** и **`{ip2}`** в одной подсети при маске **/{p}** (`{mask}`)?")
        .format(ip1=ip1, ip2=ip2, p=prefix, mask=ipcalc.prefix_to_mask(prefix)),
        fields=[_yes_no(n1 == n2)],
        explain=_("Сеть первого адреса: `{n1}`\nСеть второго адреса: `{n2}`").format(n1=n1, n2=n2) + "\n" + verdict,
    )


def private_task(rng: random.Random) -> Task:
    pool = [
        f"10.{rng.randint(0, 255)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}",
        f"172.{rng.choice([16, 20, 24, 31])}.{rng.randint(0, 255)}.{rng.randint(1, 254)}",
        f"172.{rng.choice([15, 32, 40])}.{rng.randint(0, 255)}.{rng.randint(1, 254)}",
        f"192.168.{rng.randint(0, 255)}.{rng.randint(1, 254)}",
        f"192.169.{rng.randint(0, 255)}.{rng.randint(1, 254)}",
        f"{rng.choice([8, 31, 77, 93, 142, 185, 213])}.{rng.randint(0, 255)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}",
        f"100.{rng.randint(64, 127)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}",
    ]
    ip = rng.choice(pool)
    return Task(
        text=_("Является ли адрес **`{ip}`** частным (RFC 1918)?").format(ip=ip),
        fields=[_yes_no(ipcalc.is_rfc1918(ip))],
        explain=_("Частные диапазоны: `10.0.0.0/8`, `172.16.0.0/12` (172.16–172.31), `192.168.0.0/16`.\n"
                  "`{ip}` — {kind}.").format(ip=ip, kind=ipcalc.addr_kind(ip)),
    )


# ------------------------------------------------------------------ TCP / UDP

def tcp_seq_task(rng: random.Random) -> Task:
    x = rng.randrange(1000, 90000, 100)
    y = rng.randrange(1000, 90000, 100)
    variant = rng.randrange(6)
    if variant == 0:
        return Task(
            text=_("Клиент отправляет **SYN** с `seq={x}`. Какое значение **ack** будет в ответном SYN-ACK?").format(x=x),
            fields=[Field("ack", str(x + 1))],
            explain=_("Флаг SYN «занимает» один номер последовательности. Сервер подтверждает его: "
                      "ack = {x} + 1 = **{r}**.").format(x=x, r=x + 1),
        )
    if variant == 1:
        return Task(
            text=_("Клиент: SYN `seq={x}`. Сервер: SYN-ACK `seq={y}, ack={x1}`. Какие **seq** и **ack** будут "
                   "в третьем сегменте (ACK клиента)?").format(x=x, y=y, x1=x + 1),
            fields=[Field("seq", str(x + 1)), Field("ack", str(y + 1))],
            explain=_("seq клиента = его ISN + 1 = **{x1}** (SYN израсходовал номер).\n"
                      "ack = ISN сервера + 1 = **{y1}** — подтверждаем SYN сервера.").format(x1=x + 1, y1=y + 1),
        )
    if variant == 2:
        n = rng.choice([1, 10, 100, 200, 512, 536, 1000, 1460])
        return Task(
            text=_("Соединение установлено. Клиент отправляет сегмент `seq={x}` с **{n}** байт данных. "
                   "Какой **ack** вернёт сервер?").format(x=x, n=n),
            fields=[Field("ack", str(x + n))],
            explain=_("Сегмент содержит байты {x}…{last}. Следующий ожидаемый: {x} + {n} = **{r}**.")
            .format(x=x, last=x + n - 1, n=n, r=x + n),
        )
    if variant == 3:
        n1, n2 = rng.choice([100, 200, 500, 1000]), rng.choice([100, 300, 400, 1460])
        r = x + n1 + n2
        return Task(
            text=_("Клиент отправил два сегмента: `seq={x}` ({n1} байт) и `seq={x2}` ({n2} байт). Сервер подтверждает "
                   "оба **одним** ACK. Чему равен ack и какой seq будет у следующего сегмента клиента?")
            .format(x=x, n1=n1, x2=x + n1, n2=n2),
            fields=[Field(_("ack сервера"), str(r)), Field(_("seq следующего сегмента"), str(r))],
            explain=_("Подтверждения кумулятивные: ack = {x} + {n1} + {n2} = **{r}**. Следующий сегмент клиента "
                      "начнётся с этого же номера.").format(x=x, n1=n1, n2=n2, r=r),
        )
    if variant == 4:
        return Task(
            text=_("Клиент закрывает соединение и отправляет **FIN** с `seq={x}`. Какой **ack** будет в ответе "
                   "сервера?").format(x=x),
            fields=[Field("ack", str(x + 1))],
            explain=_("FIN, как и SYN, занимает один номер последовательности: ack = **{r}**.").format(r=x + 1),
        )
    n = 100
    return Task(
        text=_("Клиент отправил `seq={a}`, `seq={b}`, `seq={c}` (по {n} байт). Сегмент `seq={b}` **потерян**. "
               "Какой **ack** отправит сервер после получения третьего сегмента?").format(a=x, b=x + n, c=x + 2 * n, n=n),
        fields=[Field("ack", str(x + n))],
        explain=_("Сервер получил байты до {last}, а дальше «дыра». Он повторяет **дублирующий ACK = {b}** — "
                  "«жду вот этот байт». После трёх дубликатов отправитель сделает быструю повторную передачу "
                  "(fast retransmit).").format(last=x + n - 1, b=x + n),
    )


def udp_len_task(rng: random.Random) -> Task:
    n = rng.randint(1, 1472)
    if rng.random() < 0.6:
        return Task(
            text=_("Приложение отправляет по UDP **{n}** байт данных по IPv4 (без опций). Чему равны поля длины?")
            .format(n=n),
            fields=[Field("UDP Length", str(n + 8)), Field("IPv4 Total Length", str(n + 28))],
            explain=_("UDP Length = 8 (заголовок UDP) + {n} = **{a}**.\nIPv4 Total Length = 20 (заголовок IP) + 8 + "
                      "{n} = **{b}**.").format(n=n, a=n + 8, b=n + 28),
        )
    return Task(
        text=_("В заголовке UDP поле **Length = {l}**. Сколько байт полезных данных в датаграмме?").format(l=n + 8),
        fields=[Field(_("Байт данных"), str(n))],
        explain=_("Length включает 8 байт заголовка: {l} − 8 = **{n}**.").format(l=n + 8, n=n),
    )


def tcp_flags_task(rng: random.Random) -> Task:
    value = rng.choice([0x02, 0x12, 0x10, 0x18, 0x11, 0x04, 0x14])
    names = flags_names(value)
    rows = "|" + "|".join(n for n, _v, _d in TCP_FLAGS) + "|\n|" + "|".join("---" for _f in TCP_FLAGS) + "|\n|" \
           + "|".join("1" if value & v else "0" for _n, v, _d in TCP_FLAGS) + "|"
    sum_txt = " + ".join(str(v) for _n, v, _d in TCP_FLAGS if value & v)
    return Task(
        text=_("Сегмент несёт флаги **{flags}**. Чему равен байт флагов (в десятичном виде)?").format(flags=" + ".join(names)),
        fields=[Field(_("Значение"), str(value), (hex(value), f"0x{value:02X}"), _("число или 0x.."))],
        explain=f"{rows}\n`{value:08b}` = {sum_txt} = **{value}** (0x{value:02X}).\n" + _(FLAG_COMBOS.get(value, "")),
    )


def port_task(rng: random.Random) -> Task:
    port = rng.choice(QUIZ_PORTS)
    entry = next(p for p in PORTS if p[0] == port)
    service = _(entry[2])
    return Task(
        text=_("Какой стандартный порт у **{s}**?").format(s=service),
        fields=[Field(_("Порт"), str(port))],
        explain=f"{service} — **{port}/{entry[1]}**: {_(entry[3])}.",
    )
