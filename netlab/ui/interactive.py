"""Интерактивные инструменты: исследователь OSI, карта протоколов, калькулятор подсетей,
конструктор UDP, флаги TCP, версии TLS, разбор наборов шифров."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .. import theme as T
from ..core import crypto_toy, ipcalc, osi_data
from ..core.protocols import FLAG_COMBOS, TCP_FLAGS, build_udp, verify_udp
from ..core.sockets_lab import hexdump
from ..i18n import N_, _
from .richtext import RichText
from .widgets import FlatButton, card, entry, label


# ---------------------------------------------------------------------- OSI
class OsiExplorer(tk.Frame):
    def __init__(self, master, bg=None):
        bg = bg or T.BG
        super().__init__(master, bg=bg)
        label(self, _("Исследователь уровней OSI"), 15, "bold").pack(anchor="w")
        label(self, _("Нажмите на уровень, чтобы увидеть его задачи, протоколы, устройства и аналогию с обычной почтой."),
              10, fg=T.MUTED).pack(anchor="w", pady=(2, 12))
        body = tk.Frame(self, bg=bg)
        body.pack(fill="both", expand=True)
        left = tk.Frame(body, bg=bg)
        left.pack(side="left", fill="y")
        self.rows = {}
        for layer in range(7, 0, -1):
            d = osi_data.LAYERS[layer]
            col = T.LAYER[layer]
            row = tk.Frame(left, bg=T.tint(col, 0.75, T.BG), cursor="hand2", highlightthickness=2,
                           highlightbackground=T.tint(col, 0.5, T.BG))
            row.pack(fill="x", pady=3)
            num = tk.Label(row, text=str(layer), font=T.F(18, "bold"), fg=col, bg=row["bg"], width=2)
            num.pack(side="left", padx=(10, 6), pady=6)
            txt = tk.Frame(row, bg=row["bg"])
            txt.pack(side="left", padx=(0, 16))
            n1 = tk.Label(txt, text=_(d["name"]), font=T.F(12, "bold"), fg=T.TEXT, bg=row["bg"], anchor="w", width=18)
            n1.pack(anchor="w")
            n2 = tk.Label(txt, text=f"{d['en']} · {_(d['pdu'])}", font=T.F(9), fg=T.MUTED, bg=row["bg"], anchor="w")
            n2.pack(anchor="w")
            for w in (row, num, txt, n1, n2):
                w.bind("<Button-1>", lambda e, l=layer: self.select(l))
            self.rows[layer] = row
        right = card(body, bg=T.CARD)
        right.pack(side="left", fill="both", expand=True, padx=(16, 0))
        self.info = RichText(right, bg=T.CARD, height=20, padx=22, pady=16, size=11, width=50)
        self.info.pack(fill="both", expand=True)
        self.select(7)

    def select(self, layer):
        for l, row in self.rows.items():
            col = T.LAYER[l]
            row.configure(highlightbackground=col if l == layer else T.tint(col, 0.5, T.BG))
        d = osi_data.LAYERS[layer]
        self.info.render(
            _("# {n}. Уровень: {name}").format(n=layer, name=_(d["name"])) + "\n"
            + _("**{en} layer** · единица данных: **{pdu}**").format(en=d["en"], pdu=_(d["pdu"])) + "\n\n"
            + _("## Что делает") + f"\n{_(d['func'])}\n"
            + _("## Протоколы и стандарты") + f"\n{_(d['protocols'])}\n"
            + _("## Устройства") + f"\n{_(d['devices'])}\n"
            + _("## Адресация") + f"\n{_(d['addr'])}\n"
            + _("## Аналогия с почтой") + f"\n> {_(d['analogy'])}"
        )


# ---------------------------------------------------------------------- карта протоколов
class ProtocolMap(tk.Frame):
    def __init__(self, master, bg=None):
        bg = bg or T.BG
        super().__init__(master, bg=bg)
        label(self, _("Карта протоколов стека TCP/IP"), 15, "bold").pack(anchor="w")
        label(self, _("Каждая плашка — протокол. Нажмите, чтобы узнать, что он делает и где живёт."), 10,
              fg=T.MUTED).pack(anchor="w", pady=(2, 12))
        body = tk.Frame(self, bg=bg)
        body.pack(fill="both", expand=True)
        left = tk.Frame(body, bg=bg)
        left.pack(side="left", fill="y")
        for name, layer, protos in osi_data.PROTOCOL_MAP:
            col = T.LAYER[layer]
            box = tk.Frame(left, bg=T.tint(col, 0.82, T.BG), highlightthickness=1,
                           highlightbackground=T.tint(col, 0.4, T.BG))
            box.pack(fill="x", pady=4)
            tk.Label(box, text=_(name).upper(), font=T.F(9, "bold"), fg=col, bg=box["bg"]).pack(anchor="w", padx=12,
                                                                                               pady=(8, 4))
            grid = tk.Frame(box, bg=box["bg"])
            grid.pack(anchor="w", padx=10, pady=(0, 10))
            for k, (pname, port, desc) in enumerate(protos):
                b = FlatButton(grid, pname, bg=T.tint(col, 0.55, T.BG), fg=T.TEXT, size=10, padx=12, pady=5,
                               command=lambda p=(pname, port, desc, name): self.show(*p))
                b.grid(row=k // 4, column=k % 4, padx=3, pady=3, sticky="w")
        right = card(body, bg=T.CARD)
        right.pack(side="left", fill="both", expand=True, padx=(16, 0))
        self.info = RichText(right, bg=T.CARD, height=16, padx=22, pady=16, size=11, width=44)
        self.info.pack(fill="both", expand=True)
        self.info.render(_("## Выберите протокол\nСлева — четыре уровня модели TCP/IP сверху вниз.\n\n"
                           "> Данные приложения спускаются по стеку: например, **HTTP → TLS → TCP → IPv4 → Ethernet**."))

    def show(self, name, port, desc, layer):
        self.info.render(f"# {name}\n" + _("**Уровень TCP/IP:** {layer}").format(layer=_(layer)) + "\n"
                         + _("**Транспорт / номер:** `{port}`").format(port=_(port)) + f"\n\n{_(desc)}")


# ---------------------------------------------------------------------- калькулятор подсетей
class SubnetCalculator(tk.Frame):
    def __init__(self, master, bg=None):
        bg = bg or T.BG
        super().__init__(master, bg=bg)
        label(self, _("Калькулятор подсетей IPv4"), 15, "bold").pack(anchor="w")
        label(self, _("Введите адрес с префиксом или маской (например 192.168.10.77/26 или 10.0.0.5 255.255.0.0) "
                      "или двигайте ползунок префикса. Синие биты — сеть, жёлтые — хосты."), 10, fg=T.MUTED,
              wraplength=980, justify="left").pack(anchor="w", pady=(2, 10))
        row = tk.Frame(self, bg=bg)
        row.pack(fill="x")
        self.var = tk.StringVar(value="192.168.10.77/26")
        entry(row, width=28, size=13, textvariable=self.var).pack(side="left", ipady=3)
        self.prefix = tk.IntVar(value=26)
        label(row, _("Префикс:"), 10, fg=T.MUTED).pack(side="left", padx=(20, 6))
        self.scale = ttk.Scale(row, from_=0, to=32, orient="horizontal", length=320, command=self._on_scale)
        self.scale.set(26)
        self.scale.pack(side="left")
        self.pfx_lbl = label(row, "/26", 13, "bold", fg=T.PINK, mono=True)
        self.pfx_lbl.pack(side="left", padx=10)
        self.err = label(self, "", 10, fg=T.BAD)
        self.err.pack(anchor="w", pady=(4, 0))

        holder = tk.Frame(self, bg=T.BORDER, padx=1, pady=1)
        holder.pack(anchor="w", pady=(6, 10))
        self.c = tk.Canvas(holder, width=980, height=176, bg=T.CANVAS, highlightthickness=0)
        self.c.pack()
        self.out = tk.Frame(self, bg=bg)
        self.out.pack(fill="x")
        self.cells = {}
        keys = [("network", N_("Адрес сети")), ("broadcast", "Broadcast"), ("first", N_("Первый хост")),
                ("last", N_("Последний хост")), ("hosts", N_("Хостов")), ("mask", N_("Маска")), ("wildcard", "Wildcard"),
                ("class", N_("Класс (историч.)")), ("kind", N_("Тип адреса"))]
        for i, (k, name) in enumerate(keys):
            cc = card(self.out, bg=T.CARD)
            cc.grid(row=i // 3, column=i % 3, sticky="nsew", padx=(0, 8), pady=4)
            label(cc, _(name).upper(), 8, "bold", fg=T.MUTED, bg=T.CARD).pack(anchor="w", padx=12, pady=(8, 0))
            v = label(cc, "", 12, "bold", bg=T.CARD, mono=k != "kind", wraplength=300, justify="left")
            v.pack(anchor="w", padx=12, pady=(0, 8))
            self.cells[k] = v
        for i in range(3):
            self.out.columnconfigure(i, weight=1)
        self.expl = RichText(self, height=5, scroll=False, padx=0, pady=8, size=11, width=100)
        self.expl.pack(fill="x")
        self.var.trace_add("write", lambda *a: self._calc())
        self._calc()

    def _on_scale(self, value):
        new = round(float(value))
        try:
            ip, cur = ipcalc.parse_cidr(self.var.get())
        except (ValueError, IndexError):
            ip, cur = "192.168.1.1", None
        if cur != new:
            self.var.set(f"{ip}/{new}")

    def _calc(self):
        try:
            ip, prefix = ipcalc.parse_cidr(self.var.get())
            info = ipcalc.subnet_info(ip, prefix)
        except (ValueError, IndexError) as e:
            self.err.configure(text=_("Не понимаю адрес: {e}").format(e=e))
            return
        self.err.configure(text="")
        if self.prefix.get() != prefix:
            self.prefix.set(prefix)
            self.scale.set(prefix)
        self.pfx_lbl.configure(text=f"/{prefix}")
        for k, v in self.cells.items():
            v.configure(text=str(info[k]))
        self._draw_bits(info)
        self.expl.render(ipcalc.block_explanation(ip, prefix))

    def _draw_bits(self, info):
        c = self.c
        c.delete("all")
        p = info["prefix"]
        rows = [("IP", info["ip"]), (_("Маска"), info["mask"]), (_("Сеть"), info["network"]),
                ("Broadcast", info["broadcast"])]
        cw, gap = 22, 10
        x0 = 100
        for r, (name, addr) in enumerate(rows):
            y = 28 + r * 36
            c.create_text(10, y + 13, text=name, fill=T.MUTED, font=T.F(10, "bold"), anchor="w")
            bits = ipcalc.to_bin(addr).replace(".", "")
            for i, b in enumerate(bits):
                x = x0 + i * cw + (i // 8) * gap
                col = T.ACCENT if i < p else T.WARN
                fill = T.tint(col, 0.35 if b == "1" else 0.85)
                c.create_rectangle(x, y, x + cw - 3, y + 26, fill=fill, outline="")
                c.create_text(x + (cw - 3) / 2, y + 13, text=b, fill=T.ON_ACCENT if b == "1" else T.MUTED,
                              font=T.F(10, "bold", mono=True))
            c.create_text(x0 + 32 * cw + 3 * gap + 10, y + 13, text=addr, fill=T.TEXT, font=T.F(10, "bold", mono=True),
                          anchor="w")
        if 0 < p < 32:
            xb = x0 + p * cw + (p // 8) * gap - (gap / 2 if p % 8 == 0 else 1.5)
            c.create_line(xb, 20, xb, 172, fill=T.PINK, width=2, dash=(5, 3))
            c.create_text(xb, 4, text=_("/{p}  ← сеть | хосты →").format(p=p), fill=T.PINK, font=T.F(9, "bold"),
                          anchor="n")


# ---------------------------------------------------------------------- конструктор UDP
class UdpBuilder(tk.Frame):
    SRC, DST = "192.168.1.10", "8.8.8.8"

    def __init__(self, master, bg=None):
        bg = bg or T.BG
        super().__init__(master, bg=bg)
        label(self, _("Конструктор UDP-датаграммы"), 15, "bold").pack(anchor="w")
        label(self, _("Меняйте порты и данные — заголовок, длина и контрольная сумма пересчитываются сразу. "
                      "Контрольная сумма считается с псевдозаголовком: {src} → {dst}, протокол 17.")
              .format(src=self.SRC, dst=self.DST), 10, fg=T.MUTED, wraplength=980, justify="left").pack(anchor="w",
                                                                                                       pady=(2, 10))
        form = tk.Frame(self, bg=bg)
        form.pack(fill="x")
        self.v_sport = tk.StringVar(value="51515")
        self.v_dport = tk.StringVar(value="53")
        self.v_data = tk.StringVar(value=_("Привет, UDP!"))
        for i, (name, var, w) in enumerate(((_("Порт отправителя"), self.v_sport, 8),
                                            (_("Порт получателя"), self.v_dport, 8),
                                            (_("Данные (UTF-8)"), self.v_data, 40))):
            label(form, name, 10, fg=T.MUTED).grid(row=0, column=i, sticky="w", padx=(0, 12))
            entry(form, width=w, textvariable=var).grid(row=1, column=i, sticky="w", padx=(0, 12), ipady=2)
            var.trace_add("write", lambda *a: self._update())
        self.err = label(self, "", 10, fg=T.BAD)
        self.err.pack(anchor="w", pady=(4, 4))

        self.fields = tk.Frame(self, bg=bg)
        self.fields.pack(fill="x", pady=(4, 8))
        self.boxes = {}
        names = [("Source Port", T.PALETTE[0]), ("Destination Port", T.PALETTE[1]), ("Length", T.PALETTE[2]),
                 ("Checksum", T.PALETTE[3])]
        for i, (n, col) in enumerate(names):
            cc = tk.Frame(self.fields, bg=T.tint(col, 0.8, T.BG), highlightthickness=1, highlightbackground=col)
            cc.grid(row=0, column=i, sticky="nsew", padx=(0, 8))
            tk.Label(cc, text=n.upper(), font=T.F(8, "bold"), fg=col, bg=cc["bg"]).pack(anchor="w", padx=12, pady=(8, 0))
            v = tk.Label(cc, text="", font=T.F(14, "bold", mono=True), fg=T.TEXT, bg=cc["bg"])
            v.pack(anchor="w", padx=12)
            h = tk.Label(cc, text="", font=T.F(9, mono=True), fg=T.MUTED, bg=cc["bg"])
            h.pack(anchor="w", padx=12, pady=(0, 8))
            self.boxes[n] = (v, h)
            self.fields.columnconfigure(i, weight=1)

        label(self, _("Байты датаграммы (hex)"), 10, "bold", fg=T.MUTED).pack(anchor="w", pady=(6, 2))
        self.hex = tk.Text(self, height=6, bg=T.CODE_BG, fg=T.TEXT, font=T.F(10, mono=True), relief="flat",
                           padx=12, pady=8, highlightthickness=0, insertwidth=0, cursor="arrow")
        self.hex.pack(fill="x")
        for i in range(4):
            self.hex.tag_configure(f"f{i}", foreground=T.PALETTE[i])
        self.expl = RichText(self, height=5, scroll=False, padx=0, pady=8, size=10, width=100)
        self.expl.pack(fill="x")
        self._update()

    def _update(self):
        try:
            sport, dport = int(self.v_sport.get()), int(self.v_dport.get())
            if not (0 <= sport <= 65535 and 0 <= dport <= 65535):
                raise ValueError
        except ValueError:
            self.err.configure(text=_("Порты — целые числа от 0 до 65535"))
            return
        payload = self.v_data.get().encode("utf-8")
        try:
            dg = build_udp(self.SRC, self.DST, sport, dport, payload)
        except ValueError as e:
            self.err.configure(text=str(e))
            return
        self.err.configure(text="")
        length = len(dg)
        csum = int.from_bytes(dg[6:8], "big")
        for name, val in (("Source Port", sport), ("Destination Port", dport), ("Length", length), ("Checksum", csum)):
            v, h = self.boxes[name]
            v.configure(text=str(val) if name != "Checksum" else f"0x{val:04X}")
            h.configure(text=f"0x{val:04X} · {val:016b}")
        self.hex.configure(state="normal")
        self.hex.delete("1.0", "end")
        self.hex.insert("end", hexdump(dg))
        for i in range(8):  # раскраска 8 байт заголовка в первой строке дампа
            col0 = 6 + i * 3
            self.hex.tag_add(f"f{i // 2}", f"1.{col0}", f"1.{col0 + 2}")
        self.hex.configure(state="disabled")
        ok = verify_udp(self.SRC, self.DST, dg)
        self.expl.render(
            _("**Length** = 8 (заголовок) + {n} (данные) = **{l}** байт. Кириллица в UTF-8 занимает 2 байта на букву.")
            .format(n=len(payload), l=length) + "\n"
            + _("**Checksum**: сумма 16-битных слов псевдозаголовка, заголовка и данных с переносом, затем инверсия → "
                "`0x{c}`.").format(c=f"{csum:04X}") + "\n"
            + _("Проверка получателем: сумма всего вместе с полем Checksum = 0xFFFF → инверсия = 0 → ")
            + (_("**✔ датаграмма цела**.") if ok else _("**✘ ошибка**.")))


# ---------------------------------------------------------------------- флаги TCP
class TcpFlagsCalc(tk.Frame):
    def __init__(self, master, bg=None):
        bg = bg or T.BG
        super().__init__(master, bg=bg)
        label(self, _("Флаги TCP"), 15, "bold").pack(anchor="w")
        label(self, _("Включайте и выключайте флаги — смотрите значение байта флагов и что означает комбинация. "
                      "Именно это вы увидите в Wireshark в поле «Flags»."), 10, fg=T.MUTED).pack(anchor="w", pady=(2, 12))
        row = tk.Frame(self, bg=bg)
        row.pack(anchor="w")
        self.state = {n: False for n, _v, _d in TCP_FLAGS}
        self.btns = {}
        for n, v, _d in TCP_FLAGS:
            col = tk.Frame(row, bg=bg)
            col.pack(side="left", padx=4)
            b = FlatButton(col, n, command=lambda n=n: self.toggle(n), size=12, padx=16, pady=12, width=4)
            b.pack()
            label(col, f"{v:#04x}", 8, fg=T.DIM, mono=True).pack(pady=(3, 0))
            self.btns[n] = b
        quick = tk.Frame(self, bg=bg)
        quick.pack(anchor="w", pady=(14, 6))
        label(quick, _("Быстрый выбор:"), 10, fg=T.MUTED).pack(side="left", padx=(0, 8))
        for name, flags in (("SYN", ["SYN"]), ("SYN-ACK", ["SYN", "ACK"]), ("ACK", ["ACK"]), ("PSH-ACK", ["PSH", "ACK"]),
                            ("FIN-ACK", ["FIN", "ACK"]), ("RST-ACK", ["RST", "ACK"]), ("Xmas", ["FIN", "PSH", "URG"])):
            FlatButton(quick, name, command=lambda f=flags: self.set_flags(f), size=9, padx=10, pady=4).pack(side="left", padx=2)
        out = card(self, bg=T.CARD)
        out.pack(fill="x", pady=(10, 0))
        self.value = label(out, "", 22, "bold", bg=T.CARD, mono=True)
        self.value.pack(anchor="w", padx=20, pady=(14, 0))
        self.meaning = label(out, "", 12, bg=T.CARD, wraplength=900, justify="left")
        self.meaning.pack(anchor="w", padx=20, pady=(4, 4))
        self.details = RichText(out, bg=T.CARD, height=8, scroll=False, padx=20, pady=6, size=10, width=100)
        self.details.pack(fill="x", pady=(0, 10))
        self.set_flags(["SYN"])

    def toggle(self, n):
        self.state[n] = not self.state[n]
        self._update()

    def set_flags(self, flags):
        for n in self.state:
            self.state[n] = n in flags
        self._update()

    def _update(self):
        value = 0
        for n, v, _d in TCP_FLAGS:
            on = self.state[n]
            value |= v if on else 0
            self.btns[n].set_colors(bg=T.ACCENT if on else T.PANEL2, fg=T.ON_ACCENT if on else T.MUTED)
        self.value.configure(text=f"{value:08b}   =   {value}   =   0x{value:02X}")
        self.meaning.configure(text=_(FLAG_COMBOS.get(value, N_("Необычная комбинация флагов."))), fg=T.TEXT)
        lines = [f"- **{n}** — {_(d)}" for n, v, d in TCP_FLAGS if self.state[n]]
        self.details.render("\n".join(lines) or _("Флаги не установлены."))


# ---------------------------------------------------------------------- версии TLS
class TlsVersions(tk.Frame):
    COLORS = {"bad": T.BAD, "old": T.ORANGE, "ok": T.WARN, "good": T.GOOD}
    STATUS = {"bad": N_("запрещён"), "old": N_("устарел"), "ok": N_("допустим"), "good": N_("рекомендован")}

    def __init__(self, master, bg=None):
        bg = bg or T.BG
        super().__init__(master, bg=bg)
        label(self, _("История SSL/TLS"), 15, "bold").pack(anchor="w")
        label(self, _("Нажмите на версию на шкале времени."), 10, fg=T.MUTED).pack(anchor="w", pady=(2, 10))
        holder = tk.Frame(self, bg=T.BORDER, padx=1, pady=1)
        holder.pack(anchor="w")
        self.c = tk.Canvas(holder, width=980, height=150, bg=T.CANVAS, highlightthickness=0)
        self.c.pack()
        self.info = RichText(self, height=9, scroll=False, padx=0, pady=10, size=11, width=100)
        self.info.pack(fill="x")
        self._draw()
        self.select(5)

    def _draw(self):
        c = self.c
        y = 78
        c.create_line(40, y, 940, y, fill=T.BORDER, width=4)
        self.nodes = []
        xs = [80, 230, 380, 530, 680, 860]
        for i, (v, x) in enumerate(zip(crypto_toy.TLS_VERSIONS, xs)):
            col = self.COLORS[v["status"]]
            tag = f"v{i}"
            ring = c.create_oval(x - 16, y - 16, x + 16, y + 16, fill=T.tint(col, 0.6), outline=col, width=3, tags=(tag,))
            c.create_text(x, y - 34, text=v["name"], fill=T.TEXT, font=T.F(12, "bold"), tags=(tag,))
            c.create_text(x, y + 32, text=str(v["year"]), fill=T.MUTED, font=T.F(10, "bold"), tags=(tag,))
            c.create_text(x, y + 50, text=_(self.STATUS[v["status"]]), fill=col, font=T.F(9, "bold"), tags=(tag,))
            c.tag_bind(tag, "<Button-1>", lambda e, i=i: self.select(i))
            c.tag_bind(tag, "<Enter>", lambda e: c.configure(cursor="hand2"))
            c.tag_bind(tag, "<Leave>", lambda e: c.configure(cursor=""))
            self.nodes.append(ring)

    def select(self, i):
        for k, ring in enumerate(self.nodes):
            col = self.COLORS[crypto_toy.TLS_VERSIONS[k]["status"]]
            self.c.itemconfigure(ring, fill=col if k == i else T.tint(col, 0.6), width=5 if k == i else 3)
        v = crypto_toy.TLS_VERSIONS[i]
        self.info.render(f"## {v['name']} · {v['year']}\n"
                         + _("**{rfc}** — статус: **{status}**").format(rfc=_(v["rfc"]), status=_(self.STATUS[v["status"]]))
                         + f"\n\n{_(v['text'])}")


# ---------------------------------------------------------------------- наборы шифров
class CipherDecoder(tk.Frame):
    EXAMPLES = ["TLS_AES_128_GCM_SHA256", "TLS_CHACHA20_POLY1305_SHA256", "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
                "ECDHE-ECDSA-AES256-GCM-SHA384", "TLS_RSA_WITH_AES_128_CBC_SHA", "TLS_RSA_WITH_RC4_128_MD5",
                "DHE-RSA-AES256-SHA"]

    def __init__(self, master, bg=None):
        bg = bg or T.BG
        super().__init__(master, bg=bg)
        label(self, _("Разбор набора шифров (cipher suite)"), 15, "bold").pack(anchor="w")
        label(self, _("Вставьте имя набора в формате IANA (TLS_..._WITH_...) или OpenSSL (ECDHE-RSA-...). "
                      "Можно взять из вкладки «Практика → Проверка сайта»."), 10, fg=T.MUTED).pack(anchor="w", pady=(2, 10))
        row = tk.Frame(self, bg=bg)
        row.pack(fill="x")
        self.var = tk.StringVar(value=self.EXAMPLES[2])
        e = entry(row, width=48, size=12, textvariable=self.var)
        e.pack(side="left", ipady=3)
        e.bind("<Return>", lambda _e: self.parse())
        FlatButton(row, _("Разобрать"), self.parse, kind="primary").pack(side="left", padx=8)
        ex = tk.Frame(self, bg=bg)
        ex.pack(fill="x", pady=(8, 8))
        label(ex, _("Примеры:"), 9, fg=T.MUTED).pack(side="left")
        for s in self.EXAMPLES:
            FlatButton(ex, s.replace("TLS_", "").replace("_WITH_", " / ")[:26], size=8, padx=6, pady=3,
                       command=lambda s=s: (self.var.set(s), self.parse())).pack(side="left", padx=2)
        self.out = RichText(self, height=16, padx=0, pady=6, size=11, width=100)
        self.out.pack(fill="both", expand=True)
        self.parse()

    def parse(self):
        try:
            r = crypto_toy.parse_cipher_suite(self.var.get())
        except ValueError as e:
            self.out.render(f"!> {e}")
            return
        ex = crypto_toy.explain_component
        kx = r["kx"] + (" " + _("(в TLS 1.3 — всегда эфемерный (EC)DHE)") if r["tls13"] else "")
        yes, no = _("✔ да"), _("✘ нет")
        lines = [
            f"## {r['name']}",
            _("**Версия:** {v}").format(v="TLS 1.3" if r["tls13"] else _("TLS 1.2 и ниже")),
            "",
            "- " + _("**Обмен ключами:**") + f" `{kx}` — {ex('kx', r['kx'])}",
            "- " + _("**Аутентификация:**") + f" `{r['auth']}` — {ex('auth', r['auth'])}",
            "- " + _("**Шифр:**") + f" `{r['cipher']}` — {ex('cipher', r['cipher'])}",
            "- " + _("**Хэш / MAC:**") + f" `{r['mac']}` — {ex('mac', r['mac'])}",
            "",
            _("Прямая секретность: **{pfs}**   ·   AEAD: **{aead}**").format(pfs=yes if r["pfs"] else no,
                                                                          aead=yes if r["aead"] else no),
        ]
        if r["warnings"]:
            lines.append("")
            lines += [f"!> {w}" for w in r["warnings"]]
        else:
            lines.append("> " + _("✔ Современный и безопасный набор."))
        self.out.render("\n".join(lines))
