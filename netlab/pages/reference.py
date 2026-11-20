"""Справочник: порты, команды, сравнения, глоссарий."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .. import theme as T
from ..core.protocols import PORTS
from ..i18n import N_, _, content
from ..ui.richtext import RichText
from ..ui.widgets import Tabs, entry, label

ALL = N_("все")
COMMANDS = [
    ("ipconfig /all", "Windows", N_("Свои IP-адреса, маска, шлюз, DNS, MAC")),
    ("ip a  /  ip r", "Linux", N_("Адреса интерфейсов / таблица маршрутизации")),
    ("ping 8.8.8.8", ALL, N_("Доступность узла и задержка (ICMP Echo)")),
    ("tracert example.com", "Windows", N_("Путь пакета через маршрутизаторы (traceroute в Linux/macOS)")),
    ("pathping example.com", "Windows", N_("traceroute + статистика потерь на каждом прыжке")),
    ("nslookup example.com", ALL, N_("DNS-запрос: какой IP у имени")),
    ("Resolve-DnsName example.com", "PowerShell", N_("То же, с подробностями (TTL, тип записи)")),
    ("arp -a", ALL, N_("Таблица ARP: соответствие IP → MAC")),
    ("route print", "Windows", N_("Таблица маршрутизации")),
    ("netstat -an", ALL, N_("Все соединения и слушающие порты с состояниями TCP")),
    ("Get-NetTCPConnection", "PowerShell", N_("Соединения TCP с владельцем-процессом")),
    ("Test-NetConnection host -Port 443", "PowerShell", N_("Открыт ли TCP-порт на удалённом узле")),
    ("curl -v https://example.com", ALL, N_("HTTP-запрос с подробным выводом TLS и заголовков")),
    ("openssl s_client -connect host:443", ALL, N_("Ручное TLS-подключение: сертификат, версия, шифр")),
    ("nmap -sS host", ALL, N_("Сканирование портов (только своих сетей!)")),
    ("Wireshark: tcp.flags.syn==1", "Wireshark", N_("Фильтр: только сегменты с SYN")),
    ("Wireshark: tls.handshake", "Wireshark", N_("Фильтр: сообщения TLS-рукопожатия")),
    ("Wireshark: udp.port==53", "Wireshark", N_("Фильтр: DNS-трафик")),
]

COMPARE = r"""
# Шпаргалка
## OSI — кратко
|№|Уровень|PDU|Адрес|Устройство|Протоколы|
|---|---|---|---|---|---|
|7|Прикладной|Данные|URL, имя|—|HTTP, DNS, SMTP|
|6|Представления|Данные|—|—|TLS, UTF-8, JPEG|
|5|Сеансовый|Данные|—|—|RPC, NetBIOS|
|4|Транспортный|Сегмент|Порт|Firewall L4|TCP, UDP|
|3|Сетевой|Пакет|IP|Маршрутизатор|IP, ICMP|
|2|Канальный|Кадр|MAC|Коммутатор|Ethernet, ARP|
|1|Физический|Биты|—|Хаб, кабель|1000BASE-T|

## TCP против UDP
|Критерий|TCP|UDP|
|---|---|---|
|Соединение|Рукопожатие SYN/SYN-ACK/ACK|Нет|
|Надёжность|Подтверждения и повторы|Нет|
|Порядок|Гарантирован|Нет|
|Границы сообщений|Нет (поток)|Да|
|Управление потоком|Окно|Нет|
|Заголовок|20–60 байт|8 байт|
|Применение|Веб, почта, SSH, БД|DNS, VoIP, игры, QUIC|

## TLS 1.2 против TLS 1.3
|Критерий|TLS 1.2|TLS 1.3|
|---|---|---|
|Рукопожатие|2 RTT|1 RTT (0-RTT при возобновлении)|
|Обмен ключами|RSA, DHE, ECDHE|Только (EC)DHE|
|Прямая секретность|Опционально|Всегда|
|Шифры|Десятки, вкл. CBC|5, только AEAD|
|Сертификат|Открытым текстом|Зашифрован|

## Числа, которые стоит помнить
- Заголовки: Ethernet **14** + FCS **4**, IPv4 **20**, IPv6 **40**, TCP **20**, UDP **8**, TLS-запись **5** байт.
- MTU Ethernet — **1500** байт → TCP MSS обычно **1460**, максимум данных UDP без фрагментации — **1472**.
- TTL по умолчанию: **64** (Linux, macOS), **128** (Windows), **255** (сетевое оборудование).
- Порты: эфемерные **49152–65535**, общеизвестные **0–1023**.
- Protocol в IPv4: ICMP **1**, TCP **6**, UDP **17**.

## Глоссарий
- **RTT** (Round-Trip Time) — время «туда-обратно» между двумя узлами.
- **MTU** — максимальный размер пакета, который пролезает через канал без фрагментации.
- **MSS** — максимальный размер данных в одном TCP-сегменте.
- **ISN** — начальный номер последовательности TCP.
- **NAT** — подмена адресов (обычно частных на публичный) на роутере.
- **CIDR** — бесклассовая адресация с префиксом: `10.0.0.0/8`.
- **CA** — центр сертификации, подписывающий сертификаты.
- **SNI** — имя сайта в ClientHello, по нему сервер выбирает сертификат.
- **ALPN** — согласование протокола поверх TLS (h2 = HTTP/2).
- **AEAD** — шифрование с проверкой целостности (AES-GCM, ChaCha20-Poly1305).
- **PFS** — прямая секретность: старые сеансы не расшифровать даже с украденным ключом сервера.
- **MITM** — атака «человек посередине».
"""




class ReferencePage(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=T.BG)
        head = tk.Frame(self, bg=T.BG)
        head.pack(fill="x", padx=28, pady=(18, 10))
        label(head, _("СПРАВОЧНИК"), 9, "bold", fg=T.ACCENT2).pack(anchor="w")
        label(head, _("Всё под рукой"), 20, "bold").pack(anchor="w")
        nb = Tabs(self, accent=T.ACCENT2)
        nb.pack(fill="both", expand=True, padx=28, pady=(0, 16))

        self._ports(nb.add(_("Порты")))

        cmds = nb.add(_("Команды"))
        tv = self._table(cmds, (_("Команда"), _("Где"), _("Что делает")), (300, 110, 560))
        for i, (cmd, where, what) in enumerate(COMMANDS):
            tv.insert("", "end", values=(cmd, _(where), _(what)), tags=("odd",) if i % 2 else ())

        rt = RichText(nb.add(_("Шпаргалка")), height=20, padx=24, pady=16, size=11)
        rt.pack(fill="both", expand=True)
        rt.render(content("CHEAT", None, COMPARE))

    def _table(self, parent, headers, widths):
        frame = tk.Frame(parent, bg=T.BG)
        frame.pack(fill="both", expand=True, pady=10)
        cols = [f"c{i}" for i in range(len(headers))]
        tv = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse")
        for c, text, w in zip(cols, headers, widths):
            tv.heading(c, text=text, anchor="w")
            tv.column(c, width=w, anchor="w", stretch=c == cols[-1])
        sb = ttk.Scrollbar(frame, orient="vertical", command=tv.yview)
        tv.configure(yscrollcommand=sb.set)
        tv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        tv.tag_configure("odd", background=T.PANEL)
        return tv

    def _ports(self, parent):
        top = tk.Frame(parent, bg=T.BG)
        top.pack(fill="x", pady=(12, 0))
        label(top, _("Поиск:"), 10, fg=T.MUTED).pack(side="left")
        self.q = tk.StringVar()
        entry(top, width=30, textvariable=self.q).pack(side="left", padx=8, ipady=2)
        label(top, _("по номеру, названию или описанию"), 9, fg=T.DIM).pack(side="left")
        self.tv = self._table(parent, (_("Порт"), _("Транспорт"), _("Сервис"), _("Назначение")), (80, 110, 170, 600))
        self.q.trace_add("write", lambda *a: self._fill())
        self._fill()

    def _fill(self):
        q = self.q.get().strip().lower()
        self.tv.delete(*self.tv.get_children())
        i = 0
        for port, proto, name, desc in PORTS:
            name, desc = _(name), _(desc)
            if q and q not in f"{port} {proto} {name} {desc}".lower():
                continue
            self.tv.insert("", "end", values=(port, proto, name, desc), tags=("odd",) if i % 2 else ())
            i += 1