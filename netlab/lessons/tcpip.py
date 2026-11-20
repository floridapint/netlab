"""Урок 2. Модель TCP/IP."""
from __future__ import annotations

from .. import theme as T
from ..core import tasks
from ..i18n import N_, _
from ..ui.animation import Scenario, Step, Tween
from ..ui.interactive import ProtocolMap
from ..ui.scene import Chip, SequenceScenario, fade_in, grow_line, round_rect
from ..ui.trainers import TaskTrainer
from .base import LessonSpec

THEORY = r"""
# Модель TCP/IP
Стек TCP/IP — это то, на чём **реально работает Интернет**. Он появился раньше OSI (ARPANET, 1970-е; описан в RFC 1122) и состоит из **4 уровней**.

## Соответствие OSI
|TCP/IP|Уровни OSI|Протоколы|PDU|
|---|---|---|---|
|Прикладной (Application)|7, 6, 5|HTTP, DNS, TLS, SSH, SMTP|Данные|
|Транспортный (Transport)|4|TCP, UDP, QUIC|Сегмент / датаграмма|
|Межсетевой (Internet)|3|IP, ICMP, IPsec|Пакет|
|Сетевого доступа (Link)|2, 1|Ethernet, Wi-Fi, ARP|Кадр|
> Во многих учебниках используют «гибридную» 5-уровневую модель: физический, канальный, сетевой, транспортный, прикладной.

## Адресация на каждом уровне
- **Прикладной** — имена и URL: `https://example.com/page`.
- **Транспортный** — **порты** (0–65535): какой программе на хосте предназначены данные. 443 — HTTPS, 53 — DNS.
- **Межсетевой** — **IP-адреса**: какому хосту в Интернете.
- **Сетевого доступа** — **MAC-адреса**: какому устройству в локальном сегменте.
> Пара «IP-адрес + порт» называется **сокетом**. TCP-соединение однозначно задаётся четвёркой: IP и порт клиента + IP и порт сервера.

## Порты
- **0–1023** — общеизвестные (well-known): 22 SSH, 53 DNS, 80 HTTP, 443 HTTPS.
- **1024–49151** — зарегистрированные: 3306 MySQL, 5432 PostgreSQL, 3389 RDP.
- **49152–65535** — динамические (эфемерные): ОС выдаёт их клиентам для исходящих соединений.
> Полная таблица портов — в разделе «Справочник».

## Что происходит, когда вы открываете https://example.com
1. **DNS** (обычно UDP/53): браузер узнаёт IP-адрес по имени.
2. **ARP**: компьютер узнаёт MAC-адрес шлюза (роутера), если ещё не знает.
3. **TCP**: трёхстороннее рукопожатие с сервером на порт 443.
4. **TLS**: рукопожатие, проверка сертификата, выработка ключей.
5. **HTTP**: запрос `GET /` и ответ `200 OK` — уже внутри зашифрованного канала.
6. Браузер рисует страницу и делает новые запросы за картинками, стилями и скриптами.
> Все эти шаги показаны в анимации «Путь запроса к сайту».

## Вспомогательные протоколы
- **ARP** — по IP узнаёт MAC в локальной сети: «Кто 192.168.1.1? Ответьте 192.168.1.10».
- **ICMP** — служебные сообщения IP: `ping` (Echo Request/Reply), «узел недостижим», «TTL истёк».
- **DHCP** — автоматическая выдача IP-адреса, маски, шлюза и DNS (UDP 67/68), схема DORA.
- **DNS** — перевод имён в адреса (UDP/TCP 53).
- **NAT** — домашний роутер подменяет частные адреса (192.168.x.x) своим публичным, чтобы много устройств выходили в Интернет через один IP.

## Принцип «конец-в-конец»
Маршрутизаторы в середине сети обрабатывают только уровни 1–3. Транспорт и приложения работают **только на конечных узлах**. Поэтому сеть простая и быстрая, а вся «умная» логика (надёжность, шифрование) сосредоточена на краях.

## OSI или TCP/IP?
|Признак|OSI|TCP/IP|
|---|---|---|
|Уровней|7|4|
|Происхождение|Комитет ISO, «сначала теория»|ARPANET, «сначала работающий код»|
|Где используется|Как общий язык, обучение, диагностика|Реальные сети и Интернет|
|Сеанс и представление|Отдельные уровни|Внутри прикладного|
"""

# ---------------------------------------------------------------------- анимация: соответствие моделей

OSI_X1, OSI_X2 = 50, 290
TCP_X1, TCP_X2 = 420, 860


def osi_top(layer):
    return 40 + (7 - layer) * 50


GROUPS = [
    (N_("Прикладной"), N_("уровни 5–7 OSI"), 7, 5, T.LAYER[7], [["HTTP", "HTTPS", "DNS", "SSH"], ["SMTP", "DHCP", "TLS"]]),
    (N_("Транспортный"), N_("уровень 4"), 4, 4, T.LAYER[4], [["TCP", "UDP", "QUIC"]]),
    (N_("Межсетевой"), N_("уровень 3"), 3, 3, T.LAYER[3], [["IPv4", "IPv6", "ICMP"]]),
    (N_("Сетевого доступа"), N_("уровни 1–2"), 2, 1, T.LAYER[2], [["Ethernet", "Wi-Fi", "ARP"]]),
]


class MappingScenario(Scenario):
    title = N_("OSI ↔ TCP/IP")
    intro = N_("Слева — 7 уровней OSI. Посмотрим, как они «схлопываются» в 4 уровня TCP/IP и какие протоколы где живут.")

    def build(self, c):
        self.c = c
        c.create_text((OSI_X1 + OSI_X2) / 2, 20, text="OSI", fill=T.MUTED, font=T.F(11, "bold"))
        c.create_text((TCP_X1 + TCP_X2) / 2, 20, text="TCP/IP", fill=T.MUTED, font=T.F(11, "bold"))
        for layer in range(7, 0, -1):
            y = osi_top(layer)
            col = T.LAYER[layer]
            round_rect(c, OSI_X1, y, OSI_X2, y + 46, r=8, fill=T.tint(col, 0.82), outline=T.tint(col, 0.4), width=2)
            c.create_text(OSI_X1 + 14, y + 23, text=f"{layer}  {T.layer_name(layer)}", fill=T.TEXT,
                          font=T.F(10, "bold"), anchor="w")
        self.chips = {}
        self.group_geom = {}

    def _group(self, gi):
        name, sub, hi, lo, col, _rows = GROUPS[gi]
        y1, y2 = osi_top(hi), osi_top(lo) + 46
        c = self.c
        band = c.create_polygon(OSI_X2 + 4, y1, TCP_X1 - 4, y1, TCP_X1 - 4, y2, OSI_X2 + 4, y2, fill=T.tint(col, 0.88),
                                outline="")
        box = round_rect(c, TCP_X1, y1, TCP_X2, y2, r=10, fill=T.tint(col, 0.8), outline=col, width=2)
        t1 = c.create_text(TCP_X1 + 16, y1 + 16, text=_(name), fill=T.TEXT, font=T.F(12, "bold"), anchor="w")
        t2 = c.create_text(TCP_X1 + 16, y1 + 34, text=_(sub), fill=T.MUTED, font=T.F(9), anchor="w")
        c.tag_lower(band)
        self.group_geom[gi] = (y1, y2)
        return fade_in(c, [(band, "fill", T.tint(col, 0.88)), (box, "fill", T.tint(col, 0.8)), (box, "outline", col),
                           (t1, "fill", T.TEXT), (t2, "fill", T.MUTED)], 700)

    def steps(self):
        def protocols():
            tws = []
            delay = 0
            for gi, (_n, _s, _h, _l, col, rows) in enumerate(GROUPS):
                y1, y2 = self.group_geom[gi]
                for ri, row in enumerate(rows):
                    if len(rows) == 1:
                        y = (y1 + y2) / 2 + (8 if y2 - y1 > 60 else 0)
                    else:
                        y = y1 + 64 + ri * 40
                    for ci, name in enumerate(row):
                        ch = Chip(self.c, 640, 432, name, col, size=9, h=24)
                        self.chips[name] = ch
                        tws.append(ch.tween_to(590 + ci * 78, y, 700, delay=delay))
                        delay += 90
            return tws

        def path():
            pts = [self.chips[n] for n in ("HTTPS", "TCP", "IPv4", "Ethernet")]
            tws = []
            for k, (a, b) in enumerate(zip(pts, pts[1:])):
                line = self.c.create_line(a.x, a.y, a.x, a.y, fill=T.WARN, width=3, arrow="last")
                tws.append(Tween(500, grow_line(self.c, line, a.x, a.y + 12, b.x, b.y - 12), delay=k * 500))
            return tws

        return [
            Step(_("**Прикладной уровень** TCP/IP объединяет уровни 5, 6 и 7 OSI: приложения сами отвечают и за сеанс, "
                   "и за формат данных, и за шифрование."), lambda: self._group(0), _("Прикладной")),
            Step(_("**Транспортный уровень** совпадает с уровнем 4 OSI: порты, TCP и UDP."), lambda: self._group(1),
                 _("Транспортный")),
            Step(_("**Межсетевой уровень** (Internet) — это сетевой уровень OSI: IP-адреса и маршрутизация."),
                 lambda: self._group(2), _("Межсетевой")),
            Step(_("**Уровень сетевого доступа** объединяет канальный и физический: Ethernet, Wi-Fi и сами провода."),
                 lambda: self._group(3), _("Сетевого доступа")),
            Step(_("Протоколы занимают свои места. TLS в TCP/IP считается частью прикладного уровня — он работает "
                   "поверх TCP для конкретных приложений."), protocols, _("Протоколы")),
            Step(_("Пример стека при открытии сайта: **HTTPS → TCP → IPv4 → Ethernet**. Каждый нижний протокол "
                   "переносит верхний внутри себя."), path, _("Стек HTTPS")),
        ]


# ---------------------------------------------------------------------- анимация: запрос к сайту

class WebRequestScenario(SequenceScenario):
    title = N_("Путь запроса к сайту")
    intro = N_("Что происходит за доли секунды после ввода **https://example.com** и нажатия Enter? "
               "Три участника: браузер, DNS-резолвер и веб-сервер.")
    actors = [(N_("Браузер"), "192.168.1.10", T.ACCENT), (N_("DNS-резолвер"), "8.8.8.8 : 53", T.ACCENT2),
              (N_("Веб-сервер"), "93.184.215.14 : 443", T.GOOD)]
    dy = 14
    gap = 15
    start_y = 92

    def steps(self):
        A, D, S = 0, 1, 2
        return [
            self.msg(A, D, _("DNS-запрос: A example.com ?"), _("Сначала нужен IP-адрес. ОС отправляет DNS-резолверу "
                     "вопрос «какой IP у example.com?» в одной **UDP-датаграмме на порт 53**."), "DNS", T.ACCENT2,
                     chip="DNS ?"),
            self.msg(D, A, _("Ответ: 93.184.215.14"), _("Резолвер отвечает адресом (и сообщает, сколько секунд его можно "
                     "кэшировать — TTL записи)."), "DNS", T.ACCENT2, chip="DNS ✔"),
            self.msg(A, S, "SYN", _("Браузер открывает **TCP-соединение** с сервером на порт **443**: первый шаг "
                     "рукопожатия — SYN."), "TCP", T.ACCENT),
            self.msg(S, A, "SYN-ACK", _("Сервер соглашается: SYN-ACK."), "TCP", T.ACCENT),
            self.msg(A, S, "ACK", _("Браузер подтверждает — соединение установлено (1 RTT)."), "TCP", T.ACCENT),
            self.msg(A, S, "TLS ClientHello", _("Начинается **TLS-рукопожатие**: ClientHello со списком шифров, "
                     "случайным числом, именем сайта (SNI) и ключом обмена."), "TLS", T.WARN, chip="ClientHello"),
            self.msg(S, A, _("ServerHello + сертификат + Finished"), _("Сервер выбирает шифр, присылает свою часть "
                     "ключа и **сертификат**. Браузер проверяет сертификат и вычисляет ключи сессии."), "TLS", T.WARN,
                     chip="ServerHello"),
            self.msg(A, S, "TLS Finished", _("Браузер завершает рукопожатие (TLS 1.3 = 1 RTT). Дальше всё зашифровано."),
                     "TLS", T.WARN, chip="Finished"),
            self.msg(A, S, _("HTTP GET /  (зашифровано)"), _("Наконец сам **HTTP-запрос** `GET /` — внутри TLS-записи."),
                     "HTTP", T.GOOD, chip="GET /"),
            self.msg(S, A, _("HTTP 200 OK + HTML"), _("Сервер отвечает `200 OK` и HTML-кодом страницы. Браузер начинает "
                     "рисовать и запрашивать стили, скрипты и картинки — уже по готовому соединению."), "HTTP", T.GOOD,
                     chip="200 OK"),
            Step(_("**Итого до первого байта страницы:** DNS (1 RTT до резолвера) + TCP (1 RTT) + TLS 1.3 (1 RTT) + "
                   "HTTP (1 RTT). Поэтому браузеры кэшируют DNS, держат соединения открытыми, а HTTP/3 (QUIC) "
                   "совмещает транспортное и TLS-рукопожатие в одно."), None, _("Итог")),
        ]


LESSON = LessonSpec(
    key="tcpip", number=2, title=N_("Модель TCP/IP"), short=N_("Модель TCP/IP"),
    subtitle=N_("4 уровня реального Интернета, порты, путь запроса к сайту"),
    color=T.LAYER[5], theory=THEORY,
    scenarios=[MappingScenario, WebRequestScenario],
    interactive=[(N_("Карта протоколов"), lambda p: ProtocolMap(p))],
    practice=[(N_("Порты"), lambda p, solved: TaskTrainer(
        p, _("Тренажёр: порты сервисов"), _("Стандартные порты — то, что сетевой инженер знает наизусть. "
                                            "Полная таблица — в «Справочнике»."), [(_("Порты"), tasks.port_task)], solved))],
)
