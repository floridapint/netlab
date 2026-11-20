"""Справочные данные о протоколах: поля заголовков, флаги TCP, порты, контрольная сумма UDP.
Тексты помечены N_() и переводятся при показе через _()."""
from __future__ import annotations

import ipaddress
import struct
from dataclasses import dataclass

from ..i18n import N_, _


@dataclass(frozen=True)
class HeaderField:
    name: str
    bits: int
    desc: str
    example: str = ""
    optional: bool = False


IPV4_HEADER = [
    HeaderField("Version", 4, N_("Версия протокола. Для IPv4 всегда **4** (для IPv6 — 6)."), "4"),
    HeaderField("IHL", 4, N_("Internet Header Length — длина заголовка в 32-битных словах. "
                             "Минимум **5** (= 20 байт), максимум 15 (= 60 байт, если есть опции)."), "5"),
    HeaderField("DSCP", 6, N_("Differentiated Services — класс обслуживания (QoS). Позволяет маршрутизаторам "
                              "пропускать голос и видео вперёд остального трафика."), N_("46 (EF — голос)")),
    HeaderField("ECN", 2, N_("Explicit Congestion Notification — маршрутизатор может пометить пакет "
                             "«сеть перегружена» вместо того, чтобы его отбросить."), "0"),
    HeaderField("Total Length", 16, N_("Длина **всего** пакета (заголовок + данные) в байтах. Максимум 65 535."), "60"),
    HeaderField("Identification", 16, N_("Номер пакета. Все фрагменты одного пакета имеют одинаковый ID — "
                                         "по нему получатель собирает их обратно."), "0x1c46"),
    HeaderField("Flags", 3, N_("Три бита: резерв (0), **DF** (Don't Fragment — запрет фрагментации) и "
                               "**MF** (More Fragments — дальше будут ещё фрагменты)."), "DF = 1"),
    HeaderField("Fragment Offset", 13, N_("Смещение фрагмента от начала исходных данных в блоках по 8 байт."), "0"),
    HeaderField("TTL", 8, N_("Time To Live — каждый маршрутизатор уменьшает на 1. При 0 пакет уничтожается, "
                             "а отправителю уходит ICMP Time Exceeded. Защищает от бесконечных петель. "
                             "Начальное значение: 64 (Linux, macOS), 128 (Windows)."), "64"),
    HeaderField("Protocol", 8, N_("Что лежит внутри пакета: **1** — ICMP, **6** — TCP, **17** — UDP, 50 — ESP (IPsec)."), "6"),
    HeaderField("Header Checksum", 16, N_("Контрольная сумма **только заголовка**. Пересчитывается на каждом "
                                          "маршрутизаторе, потому что меняется TTL. (В IPv6 её убрали.)"), "0xb1e6"),
    HeaderField("Source Address", 32, N_("IP-адрес отправителя. Не меняется по пути (кроме NAT)."), "192.168.1.10"),
    HeaderField("Destination Address", 32, N_("IP-адрес получателя. Именно по нему маршрутизаторы выбирают путь."),
                "93.184.216.34"),
    HeaderField("Options", 32, N_("Необязательные опции (Record Route, Timestamp…). Почти не используются; "
                                  "есть, только если IHL > 5."), "—", optional=True),
]

TCP_HEADER = [
    HeaderField("Source Port", 16, N_("Порт отправителя. У клиента обычно эфемерный (49152–65535)."), "51000"),
    HeaderField("Destination Port", 16, N_("Порт получателя — по нему ОС понимает, какому приложению отдать данные."),
                "443"),
    HeaderField("Sequence Number", 32, N_("Номер **первого байта данных** в этом сегменте. В SYN — случайный "
                                          "начальный номер (ISN). SYN и FIN «занимают» по одному номеру."), "1001"),
    HeaderField("Acknowledgment Number", 32, N_("Номер **следующего** байта, который получатель ожидает. "
                                                "Значит, всё до него получено (кумулятивное подтверждение). "
                                                "Действует при флаге ACK."), "5001"),
    HeaderField("Data Offset", 4, N_("Длина TCP-заголовка в 32-битных словах: 5 = 20 байт (без опций), "
                                     "максимум 15 = 60 байт."), "5"),
    HeaderField("Reserved", 4, N_("Зарезервировано, должно быть 0 (один бит раньше был флагом NS)."), "0"),
    HeaderField("Flags", 8, N_("Управляющие флаги: CWR, ECE, URG, **ACK**, PSH, **RST**, **SYN**, **FIN**. "
                               "Поиграйте с ними во вкладке «Флаги»."), "0x12 (SYN+ACK)"),
    HeaderField("Window", 16, N_("Размер окна приёма — сколько байт получатель готов принять прямо сейчас "
                                 "(управление потоком). С опцией Window Scale может достигать ~1 ГБ."), "64240"),
    HeaderField("Checksum", 16, N_("Контрольная сумма по псевдозаголовку (IP-адреса, протокол, длина), заголовку "
                                   "и данным."), "0x3f2a"),
    HeaderField("Urgent Pointer", 16, N_("Смещение срочных данных при флаге URG. На практике почти не используется."), "0"),
    HeaderField("Options", 32, N_("Опции: **MSS** (макс. размер сегмента), **Window Scale**, **SACK** "
                                  "(выборочные подтверждения), **Timestamps**. Согласуются в SYN."), "MSS=1460",
                optional=True),
]

UDP_HEADER = [
    HeaderField("Source Port", 16, N_("Порт отправителя — куда слать ответ. Может быть 0, если ответ не нужен."), "51515"),
    HeaderField("Destination Port", 16, N_("Порт получателя — какому приложению (53 — DNS, 123 — NTP…)."), "53"),
    HeaderField("Length", 16, N_("Длина заголовка **и** данных в байтах. Минимум 8 (пустая датаграмма)."), "41"),
    HeaderField("Checksum", 16, N_("Контрольная сумма по псевдозаголовку, заголовку и данным. В IPv4 необязательна "
                                   "(0 = не считали), в IPv6 обязательна."), "0x8a4c"),
    HeaderField("Data", 32, N_("Полезная нагрузка — данные приложения. Граница сообщения сохраняется: "
                               "один sendto() = одна датаграмма."), N_("DNS-запрос"), optional=True),
]

# Флаги TCP в порядке от старшего бита к младшему
TCP_FLAGS = [
    ("CWR", 0x80, N_("Congestion Window Reduced — отправитель снизил скорость в ответ на ECE.")),
    ("ECE", 0x40, N_("ECN-Echo — «сеть сообщила о перегрузке» (или поддержка ECN в SYN).")),
    ("URG", 0x20, N_("Urgent — поле Urgent Pointer действительно. Почти не используется.")),
    ("ACK", 0x10, N_("Acknowledgment — поле ack действительно. Есть почти во всех сегментах после первого SYN.")),
    ("PSH", 0x08, N_("Push — передать данные приложению сразу, не копить в буфере.")),
    ("RST", 0x04, N_("Reset — немедленно оборвать соединение (порт закрыт, ошибка, отказ).")),
    ("SYN", 0x02, N_("Synchronize — синхронизация номеров последовательности, начало соединения.")),
    ("FIN", 0x01, N_("Finish — отправитель закончил передавать данные (закрывает своё направление).")),
]
FLAG_VALUE = {n: v for n, v, _d in TCP_FLAGS}

FLAG_COMBOS = {
    0x02: N_("SYN — 1-й шаг рукопожатия: клиент просит открыть соединение."),
    0x12: N_("SYN+ACK — 2-й шаг рукопожатия: сервер согласен и подтверждает SYN клиента."),
    0x10: N_("ACK — обычное подтверждение (и 3-й шаг рукопожатия)."),
    0x18: N_("PSH+ACK — сегмент с данными приложения, «отдай сразу»."),
    0x11: N_("FIN+ACK — вежливое завершение своей стороны соединения."),
    0x04: N_("RST — резкий обрыв соединения."),
    0x14: N_("RST+ACK — типичный ответ закрытого порта на SYN."),
    0x00: N_("Нет флагов — так выглядит NULL-сканирование (nmap -sN)."),
    0x29: N_("FIN+PSH+URG — «Xmas-сканирование» (nmap -sX): все «лампочки» горят."),
    0x03: N_("SYN+FIN — недопустимая комбинация, признак сканирования или атаки."),
}


def flags_value(names) -> int:
    return sum(FLAG_VALUE[n] for n in names)


def flags_names(value: int) -> list[str]:
    return [n for n, v, _d in TCP_FLAGS if value & v]


# (порт, транспорт, сервис, описание)
PORTS = [
    (20, "TCP", N_("FTP (данные)"), N_("Передача файлов: канал данных")),
    (21, "TCP", "FTP", N_("Передача файлов: управляющий канал")),
    (22, "TCP", "SSH", N_("Защищённый удалённый доступ, SFTP и SCP")),
    (23, "TCP", "Telnet", N_("Удалённый терминал без шифрования (устарел)")),
    (25, "TCP", "SMTP", N_("Пересылка почты между серверами")),
    (53, "UDP/TCP", "DNS", N_("Разрешение имён; TCP — для больших ответов и передачи зон")),
    (67, "UDP", N_("DHCP (сервер)"), N_("Выдача IP-адресов")),
    (68, "UDP", N_("DHCP (клиент)"), N_("Клиент получает адрес")),
    (69, "UDP", "TFTP", N_("Простая передача файлов (загрузка прошивок, PXE)")),
    (80, "TCP", "HTTP", N_("Веб без шифрования")),
    (110, "TCP", "POP3", N_("Получение почты")),
    (123, "UDP", "NTP", N_("Синхронизация времени")),
    (143, "TCP", "IMAP", N_("Доступ к почтовому ящику")),
    (161, "UDP", "SNMP", N_("Мониторинг сетевых устройств")),
    (389, "TCP", "LDAP", N_("Каталоги пользователей (Active Directory)")),
    (443, "TCP/UDP", "HTTPS", N_("HTTP поверх TLS; по UDP — HTTP/3 (QUIC)")),
    (445, "TCP", "SMB", N_("Общие папки Windows")),
    (465, "TCP", "SMTPS", N_("SMTP поверх TLS")),
    (514, "UDP", "Syslog", N_("Сбор журналов")),
    (587, "TCP", "SMTP Submission", N_("Отправка почты клиентом (с STARTTLS)")),
    (993, "TCP", "IMAPS", N_("IMAP поверх TLS")),
    (995, "TCP", "POP3S", N_("POP3 поверх TLS")),
    (1433, "TCP", "MS SQL Server", N_("База данных Microsoft")),
    (3306, "TCP", "MySQL", N_("База данных MySQL / MariaDB")),
    (3389, "TCP", "RDP", N_("Удалённый рабочий стол Windows")),
    (5432, "TCP", "PostgreSQL", N_("База данных PostgreSQL")),
    (6379, "TCP", "Redis", N_("Хранилище ключ-значение")),
    (8080, "TCP", "HTTP-alt", N_("Альтернативный HTTP (прокси, dev-серверы)")),
]

# Порты для тренажёра — однозначные и самые важные
QUIZ_PORTS = [21, 22, 23, 25, 53, 67, 80, 110, 123, 143, 443, 3306, 3389, 5432]


def internet_checksum(data: bytes) -> int:
    """Контрольная сумма Интернета (RFC 1071): дополнение до единицы суммы 16-битных слов."""
    if len(data) % 2:
        data += b"\x00"
    total = 0
    for i in range(0, len(data), 2):
        total += (data[i] << 8) | data[i + 1]
        total = (total & 0xFFFF) + (total >> 16)
    return (~total) & 0xFFFF


def udp_pseudo_header(src_ip: str, dst_ip: str, length: int) -> bytes:
    return (ipaddress.IPv4Address(src_ip).packed + ipaddress.IPv4Address(dst_ip).packed
            + struct.pack("!BBH", 0, 17, length))


def build_udp(src_ip: str, dst_ip: str, sport: int, dport: int, payload: bytes) -> bytes:
    """Собирает UDP-датаграмму (заголовок + данные) с корректной контрольной суммой."""
    length = 8 + len(payload)
    if length > 0xFFFF:
        raise ValueError(_("Слишком большая датаграмма"))
    header = struct.pack("!HHHH", sport, dport, length, 0)
    csum = internet_checksum(udp_pseudo_header(src_ip, dst_ip, length) + header + payload)
    if csum == 0:
        csum = 0xFFFF  # 0 зарезервирован под «сумма не считалась»
    return struct.pack("!HHHH", sport, dport, length, csum) + payload


def verify_udp(src_ip: str, dst_ip: str, datagram: bytes) -> bool:
    """Получатель суммирует всё вместе с полем Checksum — должно получиться 0."""
    return internet_checksum(udp_pseudo_header(src_ip, dst_ip, len(datagram)) + datagram) == 0
