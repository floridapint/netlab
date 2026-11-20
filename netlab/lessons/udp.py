"""Урок 4. Протокол UDP."""
from __future__ import annotations

from .. import theme as T
from ..core import tasks
from ..core.protocols import UDP_HEADER
from ..i18n import N_, _
from ..ui.animation import Scenario, Step, later
from ..ui.explorer import HeaderExplorer
from ..ui.interactive import UdpBuilder
from ..ui.labs import UdpLab
from ..ui.scene import Chip, SequenceScenario, node_box
from ..ui.trainers import TaskTrainer
from .base import LessonSpec

THEORY = r"""
# Протокол UDP
UDP (User Datagram Protocol, RFC 768, 1980) — самый простой транспортный протокол. Он берёт данные приложения, добавляет **8 байт заголовка** и отправляет. Всё.

## Свойства UDP
- **Без соединения** — никакого рукопожатия, данные можно слать сразу.
- **Без гарантий** — датаграмма может потеряться, прийти дважды или не по порядку. Никто не повторит отправку.
- **Сохраняет границы сообщений** — один `sendto()` = одна датаграмма = один `recvfrom()`.
- **Лёгкий и быстрый** — минимальная задержка, сервер не хранит состояние соединений.
- **Умеет broadcast и multicast** — одно сообщение многим получателям.

## Заголовок UDP (8 байт)
```
 0               15 16              31
+------------------+------------------+
|   Source Port    | Destination Port |
+------------------+------------------+
|      Length      |     Checksum     |
+------------------+------------------+
|              Данные ...             |
```
- **Source Port** — порт отправителя (куда отвечать). Может быть 0.
- **Destination Port** — порт получателя (какому приложению).
- **Length** — длина заголовка + данных в байтах (минимум 8).
- **Checksum** — контрольная сумма по псевдозаголовку (IP-адреса, протокол, длина), заголовку и данным. В IPv4 необязательна (0), в IPv6 обязательна.
> Соберите свою датаграмму во вкладке «Интерактив → Конструктор UDP» — длина и контрольная сумма посчитаются вживую.

## Где используется UDP
|Протокол|Порт|Почему UDP|
|---|---|---|
|DNS|53|Короткий запрос-ответ: проще повторить, чем устанавливать соединение|
|DHCP|67/68|У клиента ещё нет IP — нужен broadcast|
|NTP|123|Важна минимальная и стабильная задержка|
|VoIP, видеозвонки (RTP)|разные|Опоздавший пакет бесполезен — лучше пропустить|
|Онлайн-игры|разные|Важна свежесть данных, а не полнота|
|QUIC / HTTP/3|443|Надёжность реализована поверх UDP самим протоколом|
|SNMP, Syslog, TFTP|161, 514, 69|Простота|
> Если приложению на UDP нужна надёжность, оно делает её само: номера сообщений, подтверждения, таймауты и повторы. Так работают DNS-клиенты, TFTP и QUIC.

## UDP в Python
```
import socket

# сервер
srv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
srv.bind(("127.0.0.1", 9999))
data, addr = srv.recvfrom(65535)     # ждём одну датаграмму
srv.sendto(data, addr)               # эхо-ответ

# клиент
cli = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
cli.sendto("привет".encode(), ("127.0.0.1", 9999))
print(cli.recvfrom(65535))
```
Обратите внимание: нет `listen()`, `accept()`, `connect()` — просто отправляем. Попробуйте во вкладке «Практика → Живые сокеты».
!> Максимум данных в UDP — 65 507 байт (65 535 − 8 UDP − 20 IP). Но датаграммы больше MTU (~1472 байт данных) дробятся на IP-фрагменты, и потеря любого фрагмента губит всю датаграмму. Поэтому DNS и игры держат сообщения маленькими.

## UDP против TCP в одной фразе
UDP — это **открытка**: бросил в ящик и надеешься, что дойдёт. TCP — **заказное письмо с уведомлением**: дольше и дороже, зато точно знаешь, что доставлено.
"""

class DatagramScenario(Scenario):
    title = N_("Датаграммы без гарантий")
    intro = N_("Приложение отправляет **5 датаграмм** подряд через Интернет. Посмотрим, что UDP гарантирует (спойлер: "
               "ничего) и что увидит получатель.")

    CLOUD = [(380, 175), (440, 222), (500, 180), (372, 248), (520, 246)]

    def build(self, c):
        self.c = c
        node_box(c, 95, 200, 150, 70, N_("Клиент"), "192.168.1.10 : 51515", T.ACCENT, size=12)
        node_box(c, 785, 200, 150, 70, N_("Сервер"), "203.0.113.5 : 9999", T.GOOD, size=12)
        c.create_oval(300, 128, 580, 290, fill=T.tint(T.ACCENT2, 0.88), outline=T.tint(T.ACCENT2, 0.5), width=2,
                      dash=(6, 4))
        c.create_text(440, 146, text=_("Интернет"), fill=T.ACCENT2, font=T.F(11, "bold"))
        c.create_line(170, 200, 300, 200, fill=T.BORDER, width=3)
        c.create_line(580, 200, 710, 200, fill=T.BORDER, width=3)
        c.create_text(785, 262, text=_("Получено приложением:"), fill=T.MUTED, font=T.F(9, "bold"))
        c.create_text(95, 262, text=_("Отправлено:"), fill=T.MUTED, font=T.F(9, "bold"))
        for i in range(5):
            c.create_text(95, 286 + i * 26, text=f"#{i + 1}  sendto()", fill=T.DIM, font=T.F(9, mono=True))
        self.d = {}

    def steps(self):
        def send():
            tws = []
            for i in range(5):
                ch = Chip(self.c, 190, 200, f"#{i + 1}", T.ACCENT2, size=9, h=22)
                self.d[i + 1] = ch
                x, y = self.CLOUD[i]
                tws.append(ch.tween_to(x, y, 800, delay=i * 250))
            return tws

        def lose():
            ch = self.d[3]
            msg = _("✘ #3 отброшена: очередь маршрутизатора переполнена")
            return [ch.tween_to(500, 395, 900),
                    later(900, lambda: ch.set(color=T.DIM, fg=T.TEXT)),
                    later(950, lambda: self.c.create_text(500, 420, text=msg, fill=T.BAD, font=T.F(9, "bold")))]

        def arrive():
            return [self.d[n].tween_to(785, 290 + k * 28, 900, delay=k * 350) for k, n in enumerate((1, 2, 5, 4))]

        def summary():
            self.c.create_text(785, 410, text=_("порядок: 1, 2, 5, 4"), fill=T.WARN, font=T.F(10, "bold"))
            return []

        return [
            Step(_("Клиент вызывает `sendto()` пять раз. **Рукопожатия нет** — датаграммы сразу улетают в сеть. "
                   "Каждая — самостоятельное сообщение со своим заголовком."), send, _("Отправка")),
            Step(_("Где-то в сети датаграмма **#3 отброшена** (переполнен буфер маршрутизатора). UDP об этом **не "
                   "узнает**: подтверждений нет, повторной отправки не будет."), lose, _("Потеря")),
            Step(_("Остальные датаграммы идут разными путями с разной задержкой: **#5 обгоняет #4**. Получатель отдаёт "
                   "их приложению в том порядке, в каком они пришли."), arrive, _("Доставка")),
            Step(_("**Итог:** получено 4 из 5, порядок 1, 2, 5, 4. UDP не гарантирует ни доставку, ни порядок, ни "
                   "отсутствие дублей. Зато **границы сообщений сохранены**: каждая пришедшая датаграмма — целое "
                   "сообщение. Нужна надёжность — делайте её в приложении (как DNS или QUIC)."), summary, _("Итог")),
        ]


class DnsScenario(SequenceScenario):
    title = N_("DNS поверх UDP")
    intro = N_("DNS — самый известный пользователь UDP. Посмотрим, как клиент справляется с потерей запроса, "
               "если транспорт сам ничего не повторяет.")
    actors = [(N_("Клиент"), "192.168.1.10 : 53124", T.ACCENT), (N_("DNS-сервер"), "8.8.8.8 : 53", T.ACCENT2)]
    dy = 34
    gap = 24

    def steps(self):
        query, answer = _("запрос"), _("ответ")
        return [
            self.msg(0, 1, _("Запрос id=0x1a2b: A example.com ?"), _("Клиент отправляет DNS-запрос — одна "
                     "UDP-датаграмма ~40 байт. По пути она **теряется**…"), _("Запрос"), T.ACCENT2, lost=True, chip=query),
            self.note(0, _("⏱ 1 с тишины → таймаут"), _("UDP ничего не сообщает о потере. Библиотека DNS-клиента сама "
                      "ждёт ответ и по **таймауту** решает отправить запрос снова."), _("Таймаут"), advance=30),
            self.msg(0, 1, _("Повтор id=0x1a2b: A example.com ?"), _("Повторный запрос — **логика приложения**, а не "
                     "UDP. (Часто клиент спрашивает уже другой DNS-сервер из списка.)"), _("Повтор"), T.ACCENT2,
                     chip=query),
            self.msg(1, 0, _("Ответ id=0x1a2b: 93.184.215.14"), _("Сервер отвечает одной датаграммой."), _("Ответ"),
                     T.GOOD, chip=answer),
            self.note(0, _("✔ ID совпал → ответ принят"), _("Ответ сопоставляется с запросом по полю **ID** и порту. "
                      "Итого 2–3 датаграммы против минимум 7 TCP-сегментов (рукопожатие + запрос + ответ + закрытие). "
                      "Вот почему DNS выбрал UDP."), _("Итог"), color=T.GOOD),
        ]


LESSON = LessonSpec(
    key="udp", number=4, title=N_("Протокол UDP"), short="UDP",
    subtitle=N_("Датаграммы без соединения и гарантий, заголовок 8 байт, живые сокеты"),
    color=T.ACCENT2, theory=THEORY,
    scenarios=[DatagramScenario, DnsScenario],
    interactive=[(N_("Заголовок UDP"), lambda p: HeaderExplorer(
        p, _("Заголовок UDP"), UDP_HEADER, _("Всего 8 байт — 4 поля по 16 бит. Сравните с 20+ байтами TCP."))),
        (N_("Конструктор UDP"), lambda p: UdpBuilder(p))],
    practice=[(N_("Живые сокеты"), lambda p, solved: UdpLab(p, solved)),
              (N_("Длины полей"), lambda p, solved: TaskTrainer(
                  p, _("Тренажёр: длина UDP-датаграммы"), _("Считаем поле Length в UDP и Total Length в IPv4."),
                  [(_("Длины"), tasks.udp_len_task)], solved))],
)
