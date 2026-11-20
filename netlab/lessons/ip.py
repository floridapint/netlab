"""Урок 3. Протокол IP."""
from __future__ import annotations

from .. import theme as T
from ..core import tasks
from ..core.protocols import IPV4_HEADER
from ..i18n import N_, _
from ..ui.animation import Scenario, Step, later
from ..ui.explorer import HeaderExplorer
from ..ui.interactive import SubnetCalculator
from ..ui.scene import Chip, highlight, node_box, round_rect
from ..ui.trainers import TaskTrainer
from .base import LessonSpec

THEORY = r"""
# Протокол IP
IP (Internet Protocol) — протокол сетевого уровня. Его задача — доставить **пакет** от одного хоста до другого через множество промежуточных сетей. IP работает по принципу **best effort** («по возможности»): пакеты могут теряться, дублироваться и приходить не по порядку. Надёжность — забота TCP.

## IPv4-адрес
32 бита, записываются как 4 **октета** в десятичном виде:
```
192      .168      .1        .10
11000000 .10101000 .00000001 .00001010
```
Адрес делится на **сетевую часть** (номер сети) и **хостовую часть** (номер устройства в этой сети). Границу между ними задаёт **маска**.

## Маска и префикс (CIDR)
Маска — 32 бита, где сначала идут единицы (сеть), потом нули (хосты). Запись `/24` — это количество единиц.
|Префикс|Маска|Адресов|Хостов|
|---|---|---|---|
|/8|255.0.0.0|16 777 216|16 777 214|
|/16|255.255.0.0|65 536|65 534|
|/24|255.255.255.0|256|254|
|/25|255.255.255.128|128|126|
|/26|255.255.255.192|64|62|
|/27|255.255.255.224|32|30|
|/28|255.255.255.240|16|14|
|/30|255.255.255.252|4|2|
> Хостов = 2^(32 − префикс) − 2. Минус два, потому что **первый** адрес — адрес самой сети, а **последний** — широковещательный (broadcast).

## Как посчитать подсеть в уме
Пример: `192.168.10.77/26`.
1. Маска /26 = 255.255.255.**192**. «Интересный» октет — четвёртый.
2. Размер блока = 256 − 192 = **64**. Сети идут с шагом 64: .0, .64, .128, .192.
3. 77 попадает в блок 64…127 → сеть `192.168.10.64`, broadcast `192.168.10.127`.
4. Хосты: `.65` – `.126`, всего 62.
> Проверьте себя в «Интерактив → Калькулятор подсетей» и тренируйтесь в «Практике» — задачи генерируются бесконечно.

## Особые диапазоны
|Диапазон|Назначение|
|---|---|
|10.0.0.0/8|Частная сеть (RFC 1918)|
|172.16.0.0/12|Частная сеть (RFC 1918): 172.16 – 172.31|
|192.168.0.0/16|Частная сеть (RFC 1918)|
|127.0.0.0/8|Loopback — «сам себе» (127.0.0.1)|
|169.254.0.0/16|Link-local (APIPA) — DHCP не ответил|
|100.64.0.0/10|CGNAT провайдера|
|224.0.0.0/4|Multicast (групповая рассылка)|
|255.255.255.255|Широковещание в локальной сети|
Частные адреса не маршрутизируются в Интернете — для выхода наружу роутер делает **NAT**.

## Заголовок IPv4
Минимум **20 байт**. Самые важные поля:
- **TTL** — «время жизни»: каждый маршрутизатор уменьшает его на 1, при нуле пакет уничтожается. Защита от петель; на этом основан `tracert`.
- **Protocol** — что внутри: 6 = TCP, 17 = UDP, 1 = ICMP.
- **Source / Destination Address** — IP отправителя и получателя. **Не меняются** по пути (если нет NAT).
- **Identification, Flags, Fragment Offset** — для фрагментации, когда пакет больше **MTU** канала (обычно 1500 байт).
> Каждое поле можно «потрогать» во вкладке «Интерактив → Заголовок IPv4».

## Маршрутизация
Маршрутизатор смотрит на IP назначения и ищет в **таблице маршрутизации** запись с **самым длинным совпадающим префиксом** (longest prefix match). Если ничего не подошло — используется маршрут по умолчанию `0.0.0.0/0`.
- IP-адреса в пакете остаются прежними на всём пути.
- MAC-адреса меняются на **каждом** участке: для каждого «прыжка» собирается новый кадр.
- Компьютер отправляет пакеты в чужие сети через **шлюз по умолчанию** (default gateway).

## IPv6 коротко
128 бит в шестнадцатеричной записи: `2001:db8:85a3::8a2e:370:7334` (`::` — пропущенные нули). Адресов хватит всем, NAT не нужен, широковещания нет (вместо него multicast), заголовок фиксированный — 40 байт, вместо TTL — **Hop Limit**, вместо ARP — **NDP**.

## Полезные команды
```
ipconfig /all            свои адреса, маска, шлюз, DNS (Windows)
ping 8.8.8.8             доступность узла (ICMP Echo)
tracert example.com      путь пакета (traceroute в Linux/macOS)
route print              таблица маршрутизации
arp -a                   таблица ARP: IP → MAC
```
"""

# ---------------------------------------------------------------------- общая топология

DEV_Y = 100
NODES = [(N_("ПК"), "192.168.1.10", 70, T.ACCENT, 110), ("R1", N_("маршрутизатор"), 250, T.LAYER[3], 96),
         ("R2", N_("маршрутизатор"), 430, T.LAYER[3], 96), ("R3", N_("маршрутизатор"), 610, T.LAYER[3], 96),
         (N_("Сервер"), "93.184.216.34", 800, T.GOOD, 116)]
LINKS = ["192.168.1.0/24", "10.0.12.0/30", "10.0.23.0/30", "93.184.216.0/24"]


class _Topology(Scenario):
    def build(self, c):
        self.c = c
        for i in range(4):
            x1 = NODES[i][2] + NODES[i][4] / 2
            x2 = NODES[i + 1][2] - NODES[i + 1][4] / 2
            c.create_line(x1, DEV_Y, x2, DEV_Y, fill=T.BORDER, width=4)
            c.create_text((NODES[i][2] + NODES[i + 1][2]) / 2, 56, text=LINKS[i], fill=T.DIM, font=T.F(8, mono=True))
        self.boxes = [node_box(c, x, DEV_Y, w, 52, name, sub, col) for name, sub, x, col, w in NODES]
        self.build_panel(c)

    def build_panel(self, c):
        pass

    def light(self, idx):
        for i, r in enumerate(self.boxes):
            highlight(self.c, r, NODES[i][3], on=(i == idx))

    @staticmethod
    def right_edge(i):
        return NODES[i][2] + NODES[i][4] / 2 + 22

    @staticmethod
    def left_edge(i):
        return NODES[i][2] - NODES[i][4] / 2 - 22


# ---------------------------------------------------------------------- маршрутизация

CONNECTED0 = N_("подключена, eth0")
CONNECTED1 = N_("подключена, eth1")
TABLES = {
    1: ("R1", [("192.168.1.0/24", CONNECTED0), ("10.0.12.0/30", CONNECTED1), ("0.0.0.0/0", "→ 10.0.12.2 (R2)")], 2),
    2: ("R2", [("10.0.12.0/30", CONNECTED0), ("10.0.23.0/30", CONNECTED1), ("192.168.1.0/24", "→ 10.0.12.1 (R1)"),
               ("93.184.216.0/24", "→ 10.0.23.2 (R3)")], 3),
    3: ("R3", [("10.0.23.0/30", CONNECTED0), ("93.184.216.0/24", CONNECTED1), ("0.0.0.0/0", N_("→ провайдер"))], 1),
}
HOPS = [  # (MAC источника, кто, MAC назначения, кто, TTL)
    ("aa:aa:aa:00:00:10", N_("ПК"), "11:11:11:00:00:01", "R1", 64),
    ("11:11:11:00:00:02", "R1", "22:22:22:00:00:01", "R2", 63),
    ("22:22:22:00:00:02", "R2", "33:33:33:00:00:01", "R3", 62),
    ("33:33:33:00:00:02", "R3", "bb:bb:bb:00:00:34", N_("Сервер"), 61),
]


class RoutingScenario(_Topology):
    title = N_("Маршрутизация")
    intro = N_("Пакет идёт от ПК к серверу через три маршрутизатора. Следите за панелью заголовков: **жёлтым** "
               "подсвечено то, что изменилось на очередном участке.")

    def build_panel(self, c):
        round_rect(c, 16, 168, 436, 430, r=12, fill=T.CARD, outline=T.BORDER)
        c.create_text(32, 188, text=_("ЗАГОЛОВКИ НА ТЕКУЩЕМ УЧАСТКЕ"), fill=T.MUTED, font=T.F(9, "bold"), anchor="w")
        c.create_text(32, 216, text="Ethernet (L2)", fill=T.LAYER[2], font=T.F(10, "bold"), anchor="w")
        c.create_text(32, 316, text="IP (L3)", fill=T.LAYER[3], font=T.F(10, "bold"), anchor="w")
        self.vals = {}
        rows = [("mac_src", _("MAC источника"), 242), ("mac_dst", _("MAC назначения"), 268),
                ("ip_src", _("IP источника"), 342), ("ip_dst", _("IP назначения"), 368), ("ttl", "TTL", 394)]
        for key, name, y in rows:
            c.create_text(32, y, text=name, fill=T.MUTED, font=T.F(9), anchor="w")
            self.vals[key] = c.create_text(150, y, text="—", fill=T.TEXT, font=T.F(9, "bold", mono=True), anchor="w")
        round_rect(c, 452, 168, 864, 430, r=12, fill=T.CARD, outline=T.BORDER)
        self.rt_title = c.create_text(468, 188, text=_("ТАБЛИЦА МАРШРУТИЗАЦИИ"), fill=T.MUTED, font=T.F(9, "bold"),
                                      anchor="w")
        self.rt_hint = c.create_text(468, 410, text="", fill=T.DIM, font=T.F(8), anchor="w")
        self.chip = None

    def set_hop(self, hop, first=False):
        src, src_who, dst, dst_who, ttl = HOPS[hop]
        new = {"mac_src": f"{src}  ({_(src_who)})", "mac_dst": f"{dst}  ({_(dst_who)})", "ip_src": "192.168.1.10",
               "ip_dst": "93.184.216.34", "ttl": str(ttl)}
        for k, v in new.items():
            old = self.c.itemcget(self.vals[k], "text")
            changed = not first and old != v
            self.c.itemconfigure(self.vals[k], text=v, fill=T.WARN if changed else T.TEXT)

    def show_table(self, r):
        c = self.c
        c.delete("rt")
        name, rows, match = TABLES[r]
        c.itemconfigure(self.rt_title, text=_("ТАБЛИЦА МАРШРУТИЗАЦИИ {name}").format(name=name))
        c.create_text(468, 216, text=_("Сеть назначения"), fill=T.DIM, font=T.F(9, "bold"), anchor="w", tags=("rt",))
        c.create_text(640, 216, text=_("Куда отправить"), fill=T.DIM, font=T.F(9, "bold"), anchor="w", tags=("rt",))
        for i, (net, hop) in enumerate(rows):
            y = 244 + i * 30
            if i == match:
                round_rect(c, 460, y - 13, 856, y + 13, r=6, fill=T.tint(T.GOOD, 0.75), outline=T.GOOD, tags=("rt",))
            col = T.TEXT if i == match else T.MUTED
            c.create_text(468, y, text=net, fill=col, font=T.F(9, "bold", mono=True), anchor="w", tags=("rt",))
            c.create_text(640, y, text=_(hop), fill=col, font=T.F(9, "bold" if i == match else "normal"), anchor="w",
                          tags=("rt",))
        hints = {1: _("Подходит только маршрут по умолчанию /0"),
                 2: _("Совпадение 93.184.216.0/24 → следующий узел R3"),
                 3: _("Подходят /24 и /0 — побеждает более длинный префикс /24")}
        c.itemconfigure(self.rt_hint, text=hints[r])

    def _hop_step(self, r, text):
        def action():
            self.chip.set_pos(self.right_edge(r - 1), DEV_Y)
            return [self.chip.tween_to(self.left_edge(r), DEV_Y, 700),
                    later(750, lambda: (self.light(r), self.show_table(r), self.set_hop(r)))]
        return Step(text, action, TABLES[r][0])

    def steps(self):
        def start():
            self.light(0)
            self.chip = Chip(self.c, self.right_edge(0), DEV_Y, "IP", T.WARN, size=9, h=22)
            self.set_hop(0, first=True)
            return []

        def deliver():
            self.chip.set_pos(self.right_edge(3), DEV_Y)
            return [self.chip.tween_to(self.left_edge(4), DEV_Y, 700),
                    later(750, lambda: (self.light(4), self.c.itemconfigure(self.rt_hint, text="")))]

        return [
            Step(_("ПК хочет отправить пакет на **93.184.216.34**. Это не его сеть (192.168.1.0/24) → пакет надо отдать "
                   "**шлюзу по умолчанию** R1. MAC-адрес шлюза ПК узнал по ARP. Начальный **TTL = 64**."), start, _("ПК")),
            self._hop_step(1, _("R1 снимает кадр Ethernet и смотрит IP назначения. В таблице подходит только маршрут по "
                                "умолчанию **0.0.0.0/0** → следующий узел R2. TTL уменьшается: 64 → **63**. Для нового "
                                "участка собирается **новый кадр** — MAC-адреса другие!")),
            self._hop_step(2, _("R2 находит точное совпадение **93.184.216.0/24** → отправить на R3. TTL → **62**, "
                                "снова новые MAC-адреса.")),
            self._hop_step(3, _("У R3 подходят две записи: **/24** и **/0**. Работает правило **longest prefix match** — "
                                "выбирается более точная /24: сеть подключена напрямую. R3 узнаёт MAC сервера по ARP, "
                                "TTL → **61**.")),
            Step(_("Сервер получил кадр: MAC назначения — его, IP назначения — его. Поле Protocol = 6 → данные уходят "
                   "TCP."), deliver, _("Сервер")),
            Step(_("**Главное:** IP-адреса не изменились за весь путь, а **MAC-адреса менялись на каждом участке**. "
                   "По TTL = 61 сервер может догадаться, что пакет прошёл 3 маршрутизатора (стартовал с 64)."), None,
                 _("Итог")),
        ]


# ---------------------------------------------------------------------- traceroute

TRACE_IPS = ["192.168.1.1", "10.0.12.2", "10.0.23.2", "93.184.216.34"]
TRACE_MS = [1, 8, 15, 21]


class TracerouteScenario(_Topology):
    title = N_("Traceroute и TTL")
    intro = N_("Как `tracert` узнаёт путь? Он отправляет пакеты с **TTL = 1, 2, 3…** Маршрутизатор, на котором TTL "
               "обнулился, уничтожает пакет и сообщает об этом отправителю сообщением **ICMP Time Exceeded** — "
               "раскрывая свой адрес.")

    def build_panel(self, c):
        round_rect(c, 16, 186, 864, 430, r=12, fill=T.CODE_BG, outline=T.BORDER)
        c.create_text(34, 210, text="C:\\> tracert -d 93.184.216.34", fill=T.GOOD, font=T.F(10, "bold", mono=True),
                      anchor="w")
        c.create_text(34, 236, text=_("Трассировка маршрута к 93.184.216.34 с максимальным числом прыжков 30"),
                      fill=T.MUTED, font=T.F(9, mono=True), anchor="w")
        self.line_y = 266
        c.create_text(440, 172, text=_("↑ пакеты идут по верхней линии, ICMP-ответы возвращаются по нижней дорожке ↓"),
                      fill=T.DIM, font=T.F(8))

    def _probe(self, n):
        """Пакет с TTL = n."""
        delivered, dead, done_txt = _("доставлен ✔"), _("TTL=0 ✘"), _("Трассировка завершена.")

        def action():
            c = self.c
            chip = Chip(c, self.right_edge(0), DEV_Y, f"TTL={n}", T.WARN, size=8, h=20)
            tws, t = [], 0
            leg = 650
            for k in range(1, n + 1):
                tws.append(chip.tween_to(NODES[k][2], DEV_Y, leg, delay=t))
                t += leg
                remaining = n - k
                if k == 4:
                    tws.append(later(t, lambda: chip.set(text=delivered, color=T.GOOD)))
                elif remaining == 0:
                    tws.append(later(t, lambda k=k: (chip.set(text=dead, color=T.BAD), self.light(k))))
                else:
                    tws.append(later(t, lambda r=remaining: chip.set(text=f"TTL={r}")))
            reply = Chip(c, NODES[n][2], 150, "ICMP Time Exceeded" if n < 4 else "ICMP Echo Reply",
                         T.ORANGE if n < 4 else T.GOOD, size=8, h=20)
            c.itemconfigure(reply.tag, state="hidden")
            t += 250
            tws.append(later(t, lambda: (c.itemconfigure(reply.tag, state="normal"), chip.delete())))
            tws.append(reply.tween_to(NODES[0][2] + 40, 150, 300 * n + 400, delay=t))
            t += 300 * n + 400

            def finish():
                reply.delete()
                self.light(0)
                ms = TRACE_MS[n - 1]
                line = f"{n:>3}    {ms:>2} ms    {ms + 1:>2} ms    {ms:>2} ms    {TRACE_IPS[n - 1]}"
                c.create_text(34, self.line_y, text=line, fill=T.TEXT, font=T.F(10, mono=True), anchor="w")
                self.line_y += 24
                if n == 4:
                    c.create_text(34, self.line_y + 4, text=done_txt, fill=T.GOOD, font=T.F(10, mono=True), anchor="w")
            tws.append(later(t, finish))
            return tws
        return action

    def steps(self):
        return [
            Step(_("Пакет с **TTL = 1**. R1 уменьшает TTL до 0, уничтожает пакет и отвечает **ICMP Time Exceeded** "
                   "со своего адреса 192.168.1.1. Первый прыжок найден!"), self._probe(1), "TTL = 1"),
            Step(_("**TTL = 2**: R1 уменьшает до 1 и пропускает, на R2 TTL становится 0 → ответ от 10.0.12.2."),
                 self._probe(2), "TTL = 2"),
            Step(_("**TTL = 3**: пакет «умирает» на R3 → его адрес 10.0.23.2."), self._probe(3), "TTL = 3"),
            Step(_("**TTL = 4**: пакет доходит до сервера. Тот отвечает **Echo Reply** (в Linux traceroute — ICMP Port "
                   "Unreachable на UDP-пакет). Трассировка завершена."), self._probe(4), "TTL = 4"),
            Step(_("Каждый прыжок `tracert` повторяет 3 раза — отсюда три столбца времени. Звёздочки `* * *` значат, "
                   "что маршрутизатор не отвечает на ICMP (фильтр), но пакеты дальше всё равно пропускает."), None,
                 _("Итог")),
        ]


GENS = [(N_("Подсети"), tasks.subnet_task), (N_("Маски"), tasks.mask_task), (N_("Двоичный вид"), tasks.binary_task),
        (N_("Одна подсеть?"), tasks.same_net_task), (N_("Частный адрес?"), tasks.private_task)]

LESSON = LessonSpec(
    key="ip", number=3, title=N_("Протокол IP"), short=N_("IP и подсети"),
    subtitle=N_("Адреса, маски, подсети, маршрутизация, TTL и traceroute"),
    color=T.LAYER[3], theory=THEORY,
    scenarios=[RoutingScenario, TracerouteScenario],
    interactive=[(N_("Калькулятор подсетей"), lambda p: SubnetCalculator(p)),
                 (N_("Заголовок IPv4"), lambda p: HeaderExplorer(
                     p, _("Заголовок IPv4"), IPV4_HEADER,
                     _("Минимальный размер — 20 байт (5 строк по 32 бита). Опции встречаются редко.")))],
    practice=[(N_("Задачи по IP"), lambda p, solved: TaskTrainer(
        p, _("Тренажёр IPv4"), _("Бесконечные задачи: подсети, маски, двоичный вид, принадлежность к одной сети, "
                                 "частные адреса. Ответ проверяется сразу, есть пошаговое решение."),
        [(_(name), fn) for name, fn in GENS], solved))],
)
