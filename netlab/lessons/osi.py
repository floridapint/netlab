"""Урок 1. Модель OSI."""
from __future__ import annotations

from .. import theme as T
from ..core import osi_data
from ..i18n import N_, _
from ..ui.animation import Scenario, Step, later
from ..ui.interactive import OsiExplorer
from ..ui.scene import Chip, Packet, highlight, round_rect
from ..ui.trainers import ClassifyTrainer
from .base import LessonSpec

THEORY = r"""
# Модель OSI
Модель OSI (Open Systems Interconnection, ISO/IEC 7498) — эталонная модель, которая делит сетевое взаимодействие на **7 уровней**. Каждый уровень решает свою задачу и пользуется услугами уровня ниже, ничего не зная о его внутреннем устройстве.
> Зачем это нужно? Модель — общий язык инженеров. Фраза «проблема на втором уровне» сразу говорит: дело в коммутаторе, VLAN или MAC-адресах, а не в приложении.

## Семь уровней
|№|Уровень|PDU|Примеры|
|---|---|---|---|
|7|Прикладной (Application)|Данные|HTTP, DNS, SMTP, SSH|
|6|Представления (Presentation)|Данные|TLS*, UTF-8, JPEG|
|5|Сеансовый (Session)|Данные|RPC, NetBIOS|
|4|Транспортный (Transport)|Сегмент / датаграмма|TCP, UDP, QUIC|
|3|Сетевой (Network)|Пакет|IPv4, IPv6, ICMP|
|2|Канальный (Data Link)|Кадр|Ethernet, Wi-Fi, ARP*|
|1|Физический (Physical)|Биты|кабель, оптика, радио|
* TLS и ARP не ложатся в модель идеально: TLS часто ставят между 4 и 7 уровнями, ARP — между 2 и 3.
> Запоминалка снизу вверх (Ф-К-С-Т-С-П-П): «**Ф**ил **К**упил **С**лона, **Т**еперь **С**лон **П**ьёт **П**иво». Сверху вниз по-английски: **A**ll **P**eople **S**eem **T**o **N**eed **D**ata **P**rocessing.

## Инкапсуляция
Когда приложение отправляет данные, они проходят уровни **сверху вниз**, и каждый уровень добавляет свой **заголовок** (а канальный — ещё и концевик). Это **инкапсуляция**:
```
[ Данные ]                                  ← уровни 7–5
[ TCP | Данные ]                            ← 4: сегмент
[ IP | TCP | Данные ]                       ← 3: пакет
[ Ethernet | IP | TCP | Данные | FCS ]      ← 2: кадр
0101101001110010…                           ← 1: биты
```
У получателя всё идёт в обратном порядке — **деинкапсуляция**: каждый уровень читает «свой» заголовок, снимает его и передаёт содержимое выше.
> Уровень N «разговаривает» с уровнем N на другой стороне через свой заголовок (peer-to-peer), но физически данные всегда идут вниз → по проводу → вверх. Смотрите анимацию «Инкапсуляция».

## Какие устройства на каком уровне
- **Кабель, концентратор (hub), повторитель** — L1: просто повторяют сигнал.
- **Коммутатор (switch), точка доступа** — L2: пересылают кадры по MAC-адресам, ведут таблицу «MAC → порт».
- **Маршрутизатор (router)** — L3: выбирает путь по IP-адресам и соединяет разные сети.
- **Межсетевой экран, балансировщик** — L3–L4, а «умные» (NGFW, L7-балансировщики) — до L7.
- **Компьютер, сервер** — все 7 уровней.

## Уровни подробно
### 1. Физический
Передаёт отдельные биты: напряжения, частоты, свет, разъёмы, скорость. О смысле данных ничего не знает. Примеры: витая пара (1000BASE-T), оптоволокно, радиоканал Wi-Fi.
### 2. Канальный
Собирает биты в **кадры**, адресует устройства внутри одной локальной сети по **MAC-адресам** (48 бит, например `3c:52:82:1a:9f:04`), проверяет ошибки (FCS/CRC).
### 3. Сетевой
Доставка между **разными сетями**: логические **IP-адреса**, маршрутизация, TTL, фрагментация. Протоколы: IPv4, IPv6, ICMP.
### 4. Транспортный
Доставляет данные **конкретному приложению** по **номеру порта**. TCP — надёжно и по порядку, UDP — быстро и без гарантий.
### 5. Сеансовый
Устанавливает, поддерживает и завершает «диалог» между приложениями. В реальном стеке TCP/IP отдельного уровня нет — его функции выполняют приложения и TLS.
### 6. Представления
Отвечает за **формат** данных: кодировки, сериализацию, сжатие и **шифрование**.
### 7. Прикладной
Протоколы, которыми напрямую пользуются программы: HTTP, DNS, SMTP, SSH, FTP.
!> Сам браузер — не «уровень 7». Уровень 7 — это **протокол** HTTP, которым браузер пользуется.

## Диагностика «снизу вверх»
1. L1: горит ли индикатор порта, подключён ли кабель / Wi-Fi?
2. L2: есть ли MAC-адрес шлюза в таблице ARP (`arp -a`)?
3. L3: получен ли IP-адрес (`ipconfig`), отвечает ли шлюз (`ping 192.168.1.1`)?
4. L4: открыт ли порт (`Test-NetConnection example.com -Port 443`)?
5. L7: отвечает ли сам сервис (браузер, `curl`)?
> OSI — **эталонная** модель. Реальный Интернет работает на стеке **TCP/IP** (следующий урок), но уровни OSI используют как общий словарь.
"""

# ---------------------------------------------------------------------- анимация: инкапсуляция

LX1, LX2 = 16, 166      # стек отправителя
RX1, RX2 = 714, 864     # стек получателя
PDU_L, PDU_R = 290, 590
CABLE_Y = 416


def row_y(layer):
    return 56 + (7 - layer) * 48 + 22


C = T.LAYER
TCP = ("TCP", C[4], 40)
IP = ("IP", C[3], 40)
ETH = ("ETH", C[2], 40)
FCS = ("FCS", C[2], 36)


class EncapsulationScenario(Scenario):
    title = N_("Инкапсуляция")
    intro = N_("Браузер отправляет на веб-сервер запрос `GET /`. Посмотрим, как данные спускаются по 7 уровням "
               "отправителя, обрастая заголовками, летят по кабелю битами и поднимаются у получателя.\n"
               "> Управление: **▶ Играть** — автопроигрывание, **Шаг ▶** — по одному шагу, точки справа — переход к шагу.")

    def build(self, c):
        self.c = c
        c.create_text(200, 26, text=_("ОТПРАВИТЕЛЬ · браузер"), fill=T.MUTED, font=T.F(10, "bold"))
        c.create_text(680, 26, text=_("ПОЛУЧАТЕЛЬ · веб-сервер"), fill=T.MUTED, font=T.F(10, "bold"))
        self.rows = {}
        for side, (x1, x2) in (("L", (LX1, LX2)), ("R", (RX1, RX2))):
            for layer in range(7, 0, -1):
                yc = row_y(layer)
                col = C[layer]
                r = round_rect(c, x1, yc - 21, x2, yc + 21, r=8, fill=T.tint(col, 0.85), outline=T.tint(col, 0.45), width=2)
                c.create_text(x1 + 14, yc, text=str(layer), fill=col, font=T.F(13, "bold"), anchor="w")
                c.create_text(x1 + 34, yc, text=T.layer_name(layer), fill=T.TEXT, font=T.F(10, "bold"), anchor="w")
                self.rows[(side, layer)] = r
        mx_l, mx_r = (LX1 + LX2) / 2, (RX1 + RX2) / 2
        c.create_line(mx_l, row_y(1) + 21, mx_l, CABLE_Y, mx_r, CABLE_Y, mx_r, row_y(1) + 21, fill=T.tint(C[1], 0.4),
                      width=5, capstyle="round", joinstyle="round")
        c.create_text(440, CABLE_Y + 14, text=_("кабель / оптика / радио"), fill=T.DIM, font=T.F(8))
        self.pkt = None
        self.DATA = ("GET /", C[7], 70)
        self.ENC = ("a9f3c1…", C[6], 70)
        self.BITS = ("0110 1001 0111 0010 1100…", C[1], 226)

    def _hl(self, side, layer):
        for (s, l), r in self.rows.items():
            on = s == side and l == layer
            highlight(self.c, r, C[l], on=on)
            if not on:
                self.c.itemconfigure(r, fill=T.tint(C[l], 0.85))

    def _down(self, layer, segs, caption, text, title):
        def action():
            self._hl("L", layer)
            return [self.pkt.tween_to(PDU_L, row_y(layer), 650),
                    later(650, lambda: self.pkt.set(segs, caption)),
                    self.pkt.pulse(500, delay=660)]
        return Step(text, action, title)

    def _up(self, layer, segs, caption, text, title):
        def action():
            self._hl("R", layer)
            return [self.pkt.tween_to(PDU_R, row_y(layer), 650),
                    later(700, lambda: self.pkt.set(segs, caption)),
                    self.pkt.pulse(500, delay=710)]
        return Step(text, action, title)

    def steps(self):
        DATA, ENC, BITS = self.DATA, self.ENC, self.BITS

        def start():
            self._hl("L", 7)
            self.pkt = Packet(self.c, PDU_L, row_y(7), [DATA], _("Данные"))
            return self.pkt.pulse(700)

        def transmit():
            self._hl(None, None)
            return [self.pkt.tween_path([(PDU_L, CABLE_Y), (PDU_R, CABLE_Y), (PDU_R, row_y(1))], 2200),
                    later(2200, lambda: self._hl("R", 1))]

        def summary():
            self._hl("R", 7)
            labels = {6: _("шифрование ↔ расшифровка"), 4: _("заголовок TCP (порты, seq/ack)"),
                      3: _("заголовок IP (адреса, TTL)"), 2: _("кадр Ethernet (MAC-адреса)"), 1: _("биты")}
            for layer, txt in labels.items():
                y = row_y(layer)
                self.c.create_line(LX2 + 4, y, RX1 - 4, y, fill=T.tint(C[layer], 0.3), dash=(6, 4), width=2)
                self.c.create_text(440, y - 9, text=txt, fill=C[layer], font=T.F(8, "bold"))
            return []

        L = T.layer_name
        return [
            Step(_("Браузер формирует HTTP-запрос `GET /`. На **прикладном уровне** это просто **данные** — "
                   "заголовков нижних уровней ещё нет."), start, "L7 · " + L(7)),
            self._down(6, [ENC], _("Данные (зашифрованы)"),
                       _("**Уровень представления**: кодировка (UTF-8), сжатие и **шифрование** (TLS). "
                         "Запрос превращается в шифротекст — посторонний его не прочитает."), "L6 · " + L(6)),
            self._down(5, [ENC], _("Данные (сеанс)"),
                       _("**Сеансовый уровень** ведёт «диалог» между приложениями. В стеке TCP/IP его роль играют "
                         "само приложение и TLS-сессия. Новых заголовков не добавляется."), "L5 · " + L(5)),
            self._down(4, [TCP, ENC], _("Сегмент"),
                       _("**Транспортный уровень**: TCP добавляет заголовок — порты **51000 → 443**, номера seq/ack, "
                         "окно. Теперь это **сегмент**."), "L4 · " + L(4)),
            self._down(3, [IP, TCP, ENC], _("Пакет"),
                       _("**Сетевой уровень**: IP добавляет заголовок с IP-адресами **192.168.1.10 → 93.184.216.34** и "
                         "TTL. Получился **пакет**."), "L3 · " + L(3)),
            self._down(2, [ETH, IP, TCP, ENC, FCS], _("Кадр"),
                       _("**Канальный уровень**: Ethernet добавляет заголовок с **MAC-адресами** и концевик **FCS** "
                         "(контрольная сумма для поиска ошибок). Это **кадр**."), "L2 · " + L(2)),
            self._down(1, [BITS], _("Биты"),
                       _("**Физический уровень**: кадр превращается в поток **битов** — электрических импульсов, "
                         "вспышек света или радиоволн."), "L1 · " + L(1)),
            Step(_("Биты летят по среде передачи к получателю. (В реальности по пути есть коммутаторы и "
                   "маршрутизаторы — это следующая анимация.)"), transmit, _("Передача")),
            self._up(1, [ETH, IP, TCP, ENC, FCS], _("Кадр"),
                     _("Сетевая карта получателя принимает сигнал и собирает из битов **кадр**."), "L1 · " + L(1)),
            self._up(2, [IP, TCP, ENC], _("Пакет"),
                     _("**Канальный уровень** проверяет: MAC назначения — мой, FCS сходится → снимает заголовок и "
                       "концевик Ethernet. Наверх уходит **пакет**."), "L2 · " + L(2)),
            self._up(3, [TCP, ENC], _("Сегмент"),
                     _("**Сетевой уровень**: IP назначения — мой. Поле Protocol = 6 говорит «внутри TCP» → снимаем "
                       "IP-заголовок, отдаём **сегмент** TCP."), "L3 · " + L(3)),
            self._up(4, [ENC], _("Данные"),
                     _("**Транспортный уровень**: порт назначения **443** → данные для процесса веб-сервера. TCP "
                       "проверяет порядок, отправляет подтверждение и снимает свой заголовок."), "L4 · " + L(4)),
            self._up(5, [ENC], _("Данные (сеанс)"),
                     _("**Сеансовый уровень**: данные относятся к уже открытой TLS-сессии."), "L5 · " + L(5)),
            self._up(6, [DATA], _("Данные (расшифрованы)"),
                     _("**Уровень представления**: TLS расшифровывает данные ключом сессии и проверяет их "
                       "целостность."), "L6 · " + L(6)),
            self._up(7, [DATA], _("Запрос доставлен ✔"),
                     _("**Прикладной уровень**: веб-сервер получил ровно то, что отправил браузер: `GET /`."),
                     "L7 · " + L(7)),
            Step(_("**Итог.** Каждый уровень добавляет свой заголовок при отправке и снимает его при получении. "
                   "Пунктир показывает, что одноимённые уровни «понимают» друг друга через свои заголовки — это и есть "
                   "**инкапсуляция**."), summary, _("Итог")),
        ]


# ---------------------------------------------------------------------- анимация: устройства

DEV_X = [110, 330, 550, 770]
DEVS = [(N_("ПК"), N_("все 7 уровней"), 7, T.ACCENT), (N_("Коммутатор"), N_("уровни 1–2 · MAC"), 2, C[2]),
        (N_("Маршрутизатор"), N_("уровни 1–3 · IP"), 3, C[3]), (N_("Сервер"), N_("все 7 уровней"), 7, T.GOOD)]


def bar_y(layer):
    return 330 - (layer - 1) * 38 + 17


class DevicesScenario(Scenario):
    title = N_("Путь через устройства")
    intro = N_("Пакет идёт от компьютера к серверу через **коммутатор** и **маршрутизатор**. Каждое устройство "
               "поднимает данные только до своего уровня — дальше ему смотреть незачем.")

    def build(self, c):
        self.c = c
        self.bars = {}
        for i, (name, sub, top, col) in enumerate(DEVS):
            x = DEV_X[i]
            for layer in range(1, top + 1):
                y = bar_y(layer)
                r = round_rect(c, x - 62, y - 16, x + 62, y + 16, r=6, fill=T.tint(C[layer], 0.85),
                               outline=T.tint(C[layer], 0.45), width=1.5)
                c.create_text(x - 52, y, text=str(layer), fill=C[layer], font=T.F(10, "bold"), anchor="w")
                c.create_text(x - 36, y, text=T.layer_name(layer), fill=T.TEXT, font=T.F(9), anchor="w")
                self.bars[(i, layer)] = r
            c.create_text(x, 385, text=_(name), fill=col, font=T.F(12, "bold"))
            c.create_text(x, 404, text=_(sub), fill=T.MUTED, font=T.F(9))
        for i in range(3):
            c.create_line(DEV_X[i] + 62, bar_y(1), DEV_X[i + 1] - 62, bar_y(1), fill=T.tint(C[1], 0.4), width=4)
        self.tok = None

    def _lit(self, dev, layer, on=True):
        r = self.bars[(dev, layer)]
        highlight(self.c, r, C[layer], on)
        if not on:
            self.c.itemconfigure(r, fill=T.tint(C[layer], 0.85))

    def steps(self):
        data, bits, frame, packet, new_frame = _("данные"), _("биты"), _("кадр"), _("пакет"), _("новый кадр")

        def s1():
            self.tok = Chip(self.c, DEV_X[0], bar_y(7), data, T.TEXT, size=8, h=20)
            for l in range(1, 8):
                self._lit(0, l)
            return [self.tok.tween_to(DEV_X[0], bar_y(1), 1400), later(1400, lambda: self.tok.set(bits, C[1]))]

        def s2():
            return [self.tok.tween_path([(DEV_X[1], bar_y(1)), (DEV_X[1], bar_y(2))], 1300),
                    later(1300, lambda: (self.tok.set(frame, C[2]), self._lit(1, 1), self._lit(1, 2)))]

        def s3():
            return [self.tok.tween_path([(DEV_X[1], bar_y(1)), (DEV_X[2], bar_y(1)), (DEV_X[2], bar_y(3))], 1600),
                    later(1600, lambda: (self.tok.set(packet, C[3]), [self._lit(2, l) for l in (1, 2, 3)]))]

        def s4():
            return [later(0, lambda: self.tok.set(new_frame, C[2])),
                    self.tok.tween_to(DEV_X[2], bar_y(2), 600, delay=300),
                    later(900, lambda: self.tok.set(packet, C[3]))]

        def s5():
            return [self.tok.tween_path([(DEV_X[2], bar_y(1)), (DEV_X[3], bar_y(1)), (DEV_X[3], bar_y(7))], 2200),
                    later(2200, lambda: (self.tok.set(data, T.TEXT), [self._lit(3, l) for l in range(1, 8)]))]

        return [
            Step(_("Компьютер отправляет данные: они спускаются по **всем 7 уровням** и уходят в кабель битами."), s1,
                 _("ПК")),
            Step(_("**Коммутатор** принимает биты, собирает кадр и поднимается только до **уровня 2**: читает MAC-адрес "
                   "назначения и по своей таблице «MAC → порт» решает, в какой порт отправить кадр."), s2, _("Коммутатор")),
            Step(_("Кадр уходит к **маршрутизатору**. Тот поднимается до **уровня 3**: смотрит IP-адрес назначения, "
                   "уменьшает TTL и ищет маршрут в таблице маршрутизации."), s3, _("Маршрутизатор")),
            Step(_("Маршрутизатор упаковывает пакет в **новый кадр** — с MAC-адресами следующего участка сети. "
                   "IP-адреса при этом не меняются."), s4, _("Новый кадр")),
            Step(_("Пакет приходит на **сервер** и поднимается по **всем 7 уровням** до веб-приложения."), s5, _("Сервер")),
            Step(_("**Итог:** чем «умнее» устройство, тем выше по стеку оно заглядывает. Хаб — L1, коммутатор — L2, "
                   "маршрутизатор — L3, конечные узлы — все 7. Межсетевые экраны нового поколения и L7-балансировщики "
                   "смотрят вплоть до прикладного уровня."), None, _("Итог")),
        ]


LESSON = LessonSpec(
    key="osi", number=1, title=N_("Модель OSI"), short=N_("Модель OSI"),
    subtitle=N_("7 уровней, инкапсуляция, какие устройства где работают"),
    color=T.LAYER[7], theory=THEORY,
    scenarios=[EncapsulationScenario, DevicesScenario],
    interactive=[(N_("Уровни OSI"), lambda p: OsiExplorer(p))],
    practice=[(N_("Определи уровень"), lambda p, solved: ClassifyTrainer(p, osi_data.CLASSIFY_ITEMS, solved))],
)
