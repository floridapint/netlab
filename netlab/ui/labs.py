"""Живые лабораторные: настоящие сокеты UDP/TCP на 127.0.0.1, проверка TLS реального сайта,
Диффи–Хеллман на маленьких числах, лавинный эффект SHA-256."""
from __future__ import annotations

import queue
import random
import socket
import threading
import time
import tkinter as tk

from .. import theme as T
from ..core import crypto_toy, sockets_lab, tls_probe
from ..core.sockets_lab import HOST, ClientReader, TcpEchoServer, UdpEchoServer, hexdump
from ..i18n import _
from .richtext import RichText
from .widgets import FlatButton, LogView, checkbox, entry, label


def _stamp():
    return time.strftime("%H:%M:%S")


class _SocketLabBase(tk.Frame):
    def __init__(self, master, bg=None):
        bg = bg or T.BG
        super().__init__(master, bg=bg)
        self.bg = bg
        self.events: queue.Queue = queue.Queue()
        self._poll_job = None
        self.bind("<Destroy>", self._on_destroy)

    def _poll(self):
        try:
            while True:
                self.handle_event(self.events.get_nowait())
        except queue.Empty:
            pass
        try:
            self._poll_job = self.after(60, self._poll)
        except tk.TclError:
            pass

    def handle_event(self, ev):
        view = self.server_log if ev["src"] == "server" else self.client_log
        view.append(ev["text"], ev["kind"], _stamp())
        if ev.get("data") and ev["src"] == "server":
            self.hex.set(hexdump(ev["data"]), "plain")

    def _on_destroy(self, e):
        if e.widget is self:
            if self._poll_job:
                try:
                    self.after_cancel(self._poll_job)
                except tk.TclError:
                    pass
            self.shutdown()

    def shutdown(self):
        pass

    def _logs(self):
        logs = tk.Frame(self, bg=self.bg)
        logs.pack(fill="both", expand=True, pady=(10, 0))
        self.client_log = LogView(logs, _("КЛИЕНТ"), height=11, width=50)
        self.client_log.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.server_log = LogView(logs, _("СЕРВЕР"), height=11, width=50)
        self.server_log.pack(side="left", fill="both", expand=True, padx=(6, 0))
        self.hex = LogView(self, _("БАЙТЫ ПОСЛЕДНЕГО ПОЛУЧЕННОГО СЕРВЕРОМ СООБЩЕНИЯ (HEX)"), height=4)
        self.hex.pack(fill="x", pady=(10, 0))

    def clear(self):
        for v in (self.client_log, self.server_log, self.hex):
            v.clear()

    def _server_button(self, running, port=None, proto="udp"):
        if running:
            self.b_srv.set_text(_("■  Остановить сервер"))
            self.b_srv.set_colors(bg=T.BAD)
            state = "LISTEN " if proto == "tcp" else ""
            self.status.configure(text=_("{state}слушает {host}:{port}/{proto}").format(
                state=state, host=HOST, port=port, proto=proto), fg=T.GOOD)
        else:
            self.b_srv.set_text(_("▶  Запустить сервер"))
            self.b_srv.set_colors(bg=T.GOOD)
            self.status.configure(text=_("Сервер остановлен"), fg=T.MUTED)


class UdpLab(_SocketLabBase):
    def __init__(self, master, on_solved=None, bg=None):
        super().__init__(master, bg)
        self.on_solved = on_solved
        self.server: UdpEchoServer | None = None
        self.client: socket.socket | None = None
        self.reader: ClientReader | None = None
        self.seq = 0
        self.pending = {}
        self.solved = False

        label(self, _("Живые сокеты: UDP"), 15, "bold").pack(anchor="w")
        label(self, _("Настоящий UDP-эхо-сервер на вашем компьютере (127.0.0.1). Отправляйте датаграммы и смотрите, "
                      "что происходит на обеих сторонах. Включите имитацию потерь — UDP ничего не заметит и не повторит."),
              10, fg=T.MUTED, wraplength=980, justify="left").pack(anchor="w", pady=(2, 10))
        r1 = tk.Frame(self, bg=self.bg)
        r1.pack(fill="x")
        self.b_srv = FlatButton(r1, "", self.toggle_server, kind="good")
        self.b_srv.pack(side="left")
        self.status = label(r1, "", 10, fg=T.MUTED)
        self.status.pack(side="left", padx=12)
        self._server_button(False)
        self.v_loss = tk.BooleanVar(value=False)
        checkbox(r1, _("Имитировать потерю 30% датаграмм"), self.v_loss, self._loss_changed).pack(side="left", padx=12)

        r2 = tk.Frame(self, bg=self.bg)
        r2.pack(fill="x", pady=(10, 0))
        self.v_msg = tk.StringVar(value=_("Привет, UDP!"))
        e = entry(r2, width=34, textvariable=self.v_msg)
        e.pack(side="left", ipady=3)
        e.bind("<Return>", lambda _e: self.send_one())
        FlatButton(r2, _("Отправить датаграмму"), self.send_one, kind="primary").pack(side="left", padx=8)
        FlatButton(r2, _("3 датаграммы подряд"), self.send_three).pack(side="left")
        FlatButton(r2, _("Очистить"), self.clear, kind="ghost").pack(side="left", padx=8)
        self._logs()
        self.client_log.append(_("Совет: каждый sendto() на клиенте даст ровно один recvfrom() на сервере — "
                                 "границы сообщений сохраняются."), "info")
        self._poll()

    def _loss_changed(self):
        if self.server:
            self.server.loss = 0.3 if self.v_loss.get() else 0.0

    def toggle_server(self):
        if self.server and self.server.running:
            self.server.stop()
            self.server = None
            self._server_button(False)
            self.server_log.append(_("сервер остановлен (close)"), "info", _stamp())
            return
        self.server = UdpEchoServer(self.events, loss=0.3 if self.v_loss.get() else 0.0)
        self._server_button(True, self.server.start(), "udp")

    def _ensure_client(self):
        if self.client is None:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.client.bind((HOST, 0))
            self.client_log.append(_("socket(SOCK_DGRAM), ОС выдала порт :{port}").format(
                port=self.client.getsockname()[1]), "info", _stamp())
            self.reader = ClientReader(self.client, self.events, udp=True)

    def send_one(self, text=None):
        if not (self.server and self.server.running):
            self.client_log.append(_("Сначала запустите сервер. (Хотя UDP всё равно бы отправил — в пустоту!)"), "warn",
                                   _stamp())
            return
        self._ensure_client()
        self.seq += 1
        payload = f"#{self.seq} {text or self.v_msg.get()}".encode("utf-8")
        self.client.sendto(payload, (HOST, self.server.port))
        self.pending[self.seq] = time.time()
        self.client_log.append(_("sendto() → :{port}  {n} байт: «{text}»").format(
            port=self.server.port, n=len(payload), text=payload.decode()), "send", _stamp())

    def send_three(self):
        for word in (_("раз"), _("два"), _("три")):
            self.send_one(word)

    def handle_event(self, ev):
        super().handle_event(ev)
        if ev["src"] == "client" and ev["kind"] == "recv" and ev.get("data"):
            txt = ev["data"].decode("utf-8", "replace")
            if txt.startswith("#"):
                try:
                    self.pending.pop(int(txt[1:].split()[0]), None)
                except ValueError:
                    pass
            if not self.solved and self.on_solved:
                self.solved = True
                self.on_solved()

    def _poll(self):
        now = time.time()
        for n, t in list(self.pending.items()):
            if now - t > 1.2:
                self.pending.pop(n)
                self.client_log.append(_("✘ ответ на #{n} не пришёл за 1,2 с — датаграмма потеряна. UDP не повторяет "
                                         "отправку сам: это задача приложения.").format(n=n), "error", _stamp())
        super()._poll()

    def shutdown(self):
        if self.reader:
            self.reader.stop()
        if self.client:
            self.client.close()
        if self.server:
            self.server.stop()


class TcpLab(_SocketLabBase):
    def __init__(self, master, on_solved=None, bg=None):
        super().__init__(master, bg)
        self.on_solved = on_solved
        self.server: TcpEchoServer | None = None
        self.client: socket.socket | None = None
        self.reader: ClientReader | None = None
        self.solved = False

        label(self, _("Живые сокеты: TCP"), 15, "bold").pack(anchor="w")
        label(self, _("Настоящий TCP-эхо-сервер на 127.0.0.1. Рукопожатие делает ядро ОС внутри connect()/accept(). "
                      "Эксперимент: включите «задержку чтения» и нажмите «3 сообщения подряд» — сервер получит их ОДНИМ "
                      "recv(), потому что TCP — это поток байтов без границ сообщений."),
              10, fg=T.MUTED, wraplength=980, justify="left").pack(anchor="w", pady=(2, 10))
        r1 = tk.Frame(self, bg=self.bg)
        r1.pack(fill="x")
        self.b_srv = FlatButton(r1, "", self.toggle_server, kind="good")
        self.b_srv.pack(side="left")
        self.status = label(r1, "", 10, fg=T.MUTED)
        self.status.pack(side="left", padx=12)
        self._server_button(False)
        self.v_delay = tk.BooleanVar(value=False)
        checkbox(r1, _("Задержка чтения на сервере 0,7 с"), self.v_delay, self._delay_changed).pack(side="left", padx=12)

        r2 = tk.Frame(self, bg=self.bg)
        r2.pack(fill="x", pady=(10, 0))
        self.b_conn = FlatButton(r2, _("Подключиться (connect)"), self.toggle_connect, kind="primary")
        self.b_conn.pack(side="left")
        FlatButton(r2, _("Подключиться к закрытому порту"), self.connect_closed).pack(side="left", padx=8)
        self.cstatus = label(r2, _("Нет соединения"), 10, fg=T.MUTED)
        self.cstatus.pack(side="left", padx=8)

        r3 = tk.Frame(self, bg=self.bg)
        r3.pack(fill="x", pady=(10, 0))
        self.v_msg = tk.StringVar(value=_("Привет, TCP!"))
        e = entry(r3, width=34, textvariable=self.v_msg)
        e.pack(side="left", ipady=3)
        e.bind("<Return>", lambda _e: self.send())
        FlatButton(r3, _("Отправить (send)"), self.send, kind="primary").pack(side="left", padx=8)
        FlatButton(r3, _("3 сообщения подряд"), self.send_three).pack(side="left")
        FlatButton(r3, _("Очистить"), self.clear, kind="ghost").pack(side="left", padx=8)
        self._logs()
        self._poll()

    def _delay_changed(self):
        if self.server:
            self.server.read_delay = 0.7 if self.v_delay.get() else 0.0

    def toggle_server(self):
        if self.server and self.server.running:
            self._disconnect(quiet=True)
            self.server.stop()
            self.server = None
            self._server_button(False)
            self.server_log.append(_("сервер остановлен"), "info", _stamp())
            return
        self.server = TcpEchoServer(self.events, read_delay=0.7 if self.v_delay.get() else 0.0)
        self._server_button(True, self.server.start(), "tcp")

    def toggle_connect(self):
        if self.client:
            self._disconnect()
            return
        if not (self.server and self.server.running):
            self.client_log.append(_("Сначала запустите сервер (или попробуйте «закрытый порт», чтобы увидеть RST)."),
                                   "warn", _stamp())
            return
        try:
            self.client = socket.create_connection((HOST, self.server.port), timeout=3)
        except OSError as e:
            self.client_log.append(_("connect() не удался: {e}").format(e=e), "error", _stamp())
            return
        lport = self.client.getsockname()[1]
        self.client_log.append(_("connect() → SYN, SYN-ACK, ACK выполнены ядром. Локальный порт :{port} → ESTABLISHED")
                               .format(port=lport), "send", _stamp())
        self.reader = ClientReader(self.client, self.events, udp=False)
        self.b_conn.set_text(_("Закрыть (close → FIN)"))
        self.b_conn.set_colors(bg=T.WARN)
        self.cstatus.configure(text=f"ESTABLISHED  :{lport} → :{self.server.port}", fg=T.GOOD)

    def _disconnect(self, quiet=False):
        if not self.client:
            return
        if self.reader:
            self.reader.stop()
        try:
            self.client.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.client.close()
        self.client = None
        self.reader = None
        if not quiet:
            self.client_log.append(_("close() → отправлен FIN, сокет клиента уходит в FIN_WAIT → TIME_WAIT"), "send",
                                   _stamp())
        self.b_conn.set_text(_("Подключиться (connect)"))
        self.b_conn.set_colors(bg=T.ACCENT)
        self.cstatus.configure(text=_("Нет соединения"), fg=T.MUTED)

    def connect_closed(self):
        port = sockets_lab.free_closed_port()
        self.client_log.append(_("connect() к :{port}, где никто не слушает… (Windows делает пару повторов SYN — ждём)")
                               .format(port=port), "send", _stamp())
        refused = _("ConnectionRefusedError за {ms} мс: ОС ответила RST — «порт закрыт». Так сканеры портов "
                    "отличают закрытый порт от фильтруемого (тишина).")
        opened = _("Неожиданно: порт открыт")
        failed = _("Ошибка: {e}")

        def work():
            t0 = time.perf_counter()
            try:
                s = socket.create_connection((HOST, port), timeout=5)
                s.close()
                self.events.put({"src": "client", "kind": "warn", "text": opened, "data": None})
            except ConnectionRefusedError:
                ms = round((time.perf_counter() - t0) * 1000)
                self.events.put({"src": "client", "kind": "error", "text": refused.format(ms=ms), "data": None})
            except OSError as e:
                self.events.put({"src": "client", "kind": "error", "text": failed.format(e=e), "data": None})
        threading.Thread(target=work, daemon=True).start()

    def send(self, text=None):
        if not self.client:
            self.client_log.append(_("Нет соединения — сначала connect()."), "warn", _stamp())
            return
        data = (text or self.v_msg.get()).encode("utf-8")
        try:
            self.client.sendall(data)
        except OSError as e:
            self.client_log.append(f"send: {e}", "error", _stamp())
            return
        self.client_log.append(_("send() → {n} байт: «{text}»").format(n=len(data), text=data.decode()), "send", _stamp())

    def send_three(self):
        for word in (_("раз"), _("два"), _("три")):
            self.send(word + "|")

    def handle_event(self, ev):
        super().handle_event(ev)
        if ev["src"] == "client" and ev["kind"] == "recv" and not self.solved and self.on_solved:
            self.solved = True
            self.on_solved()
        if ev["src"] == "client" and ev["kind"] == "warn" and ev.get("data") == b"" and self.client:
            self._disconnect(quiet=True)

    def shutdown(self):
        if self.reader:
            self.reader.stop()
        if self.client:
            try:
                self.client.close()
            except OSError:
                pass
        if self.server:
            self.server.stop()


class TlsProbeLab(tk.Frame):
    EXAMPLES = ["example.com", "github.com", "wikipedia.org", "expired.badssl.com", "self-signed.badssl.com",
                "wrong.host.badssl.com", "untrusted-root.badssl.com"]

    def __init__(self, master, on_solved=None, bg=None):
        bg = bg or T.BG
        super().__init__(master, bg=bg)
        self.on_solved = on_solved
        self.results: queue.Queue = queue.Queue()
        self.busy = False
        self._job = None
        label(self, _("Проверка TLS настоящего сайта"), 15, "bold").pack(anchor="w")
        label(self, _("Приложение установит реальное TLS-соединение (модуль ssl из Python) и покажет версию протокола, "
                      "набор шифров и сертификат. Нужен Интернет. Сайты *.badssl.com специально сломаны — посмотрите, "
                      "как выглядят ошибки сертификатов (в некоторых сетях они недоступны — тогда будет таймаут)."),
              10, fg=T.MUTED, wraplength=980, justify="left").pack(anchor="w", pady=(2, 10))
        row = tk.Frame(self, bg=bg)
        row.pack(fill="x")
        self.var = tk.StringVar(value="example.com")
        e = entry(row, width=36, size=12, textvariable=self.var)
        e.pack(side="left", ipady=3)
        e.bind("<Return>", lambda _e: self.run())
        self.b_run = FlatButton(row, _("Подключиться"), self.run, kind="primary")
        self.b_run.pack(side="left", padx=8)
        self.status = label(row, "", 10, fg=T.MUTED)
        self.status.pack(side="left")
        ex = tk.Frame(self, bg=bg)
        ex.pack(fill="x", pady=(8, 6))
        for h in self.EXAMPLES:
            FlatButton(ex, h, size=9, padx=8, pady=3, command=lambda h=h: (self.var.set(h), self.run())).pack(side="left",
                                                                                                           padx=2)
        self.out = RichText(self, height=20, padx=0, pady=6, size=11, width=100)
        self.out.pack(fill="both", expand=True)
        self.out.render(_("Выберите сайт и нажмите **Подключиться**."))
        self.bind("<Destroy>", self._on_destroy)

    def _on_destroy(self, e):
        if e.widget is self and self._job:
            self.after_cancel(self._job)

    def run(self):
        if self.busy:
            return
        host = self.var.get().strip()
        if not host:
            return
        self.busy = True
        self.b_run.set_enabled(False)
        self.status.configure(text=_("Подключаюсь… (TCP → TLS-рукопожатие → проверка версий)"), fg=T.WARN)
        threading.Thread(target=lambda: self.results.put(tls_probe.probe(host)), daemon=True).start()
        self._wait()

    def _wait(self):
        try:
            res = self.results.get_nowait()
        except queue.Empty:
            self._job = self.after(100, self._wait)
            return
        self._job = None
        self.busy = False
        self.b_run.set_enabled(True)
        self.status.configure(text="")
        self.show(res)

    def show(self, r):
        host = f"{r['host']}:{r['port']}"
        if not r["ok"]:
            if r.get("error") == "cert":
                code = r.get("verify_code")
                hint = _(tls_probe.CERT_ERRORS.get(code, "")) or _("Браузер показал бы предупреждение «Подключение не защищено».")
                self.out.render(_("# ✘ {host}: сертификат не прошёл проверку").format(host=host) + "\n"
                                + _("**Ответ OpenSSL:** `{msg}` (код {code})").format(msg=r["message"], code=code)
                                + f"\n\n{hint}\n\n> "
                                + _("Рукопожатие было прервано **клиентом**: TLS отказывается продолжать, если не может "
                                    "убедиться, что говорит именно с этим сайтом. Это и есть защита от атаки «человек "
                                    "посередине»."))
            else:
                self.out.render(f"# ✘ {host}\n{r.get('message', '')}")
            if self.on_solved:
                self.on_solved()
            return
        san = r["san"]
        san_txt = ", ".join(san[:6]) + (" " + _("и ещё {n}").format(n=len(san) - 6) if len(san) > 6 else "")
        days = r.get("days_left")
        days_txt = _("осталось **{n}** дн.").format(n=days) if days is not None else ""
        tcp_tls = _("TCP-рукопожатие: **{a} мс** · TLS-рукопожатие: **{b} мс**").format(a=r["tcp_ms"], b=r["tls_ms"])
        if r["version"] == "TLSv1.3":
            tcp_tls += "  " + _("(TLS 1.3 = 1 RTT, поэтому ≈ времени TCP)")
        issuer = r["issuer_cn"] + (f" ({r['issuer_org']})" if r["issuer_org"] else "")
        lines = [
            _("# ✔ {host} — соединение защищено").format(host=host),
            "- " + _("IP сервера: `{ip}`").format(ip=r["ip"]),
            "- " + tcp_tls,
            "- " + _("Версия протокола: **{v}**").format(v=r["version"]),
            "- " + _("Набор шифров: `{c}` ({bits} бит)").format(c=r["cipher"], bits=r["cipher_bits"]),
            "- " + _("ALPN (протокол поверх TLS): `{a}`").format(a=r["alpn"] or "—") + ("  — HTTP/2" if r["alpn"] == "h2" else ""),
            _("## Сертификат"),
            "- " + _("Кому выдан (CN): **{cn}**").format(cn=r["subject_cn"]),
            "- " + _("Альтернативные имена (SAN): {san}").format(san=san_txt or "—"),
            "- " + _("Кем выдан: **{issuer}**").format(issuer=issuer),
            "- " + _("Действует: {a} → {b}").format(a=r["not_before"], b=r["not_after"]) + f"  {days_txt}",
            "- " + _("Отпечаток SHA-256: `{fp}…`").format(fp=r["sha256"][:47]),
        ]
        if r.get("versions"):
            lines.append(_("## Какие версии поддерживает сервер"))
            for v, ok in r["versions"].items():
                lines.append(f"- {v}: **{_('✔ да') if ok else _('✘ нет')}**")
            lines.append("> " + _("TLS 1.0/1.1 проверить нельзя: современный OpenSSL в Python отключает их как небезопасные."))
        try:
            p = crypto_toy.parse_cipher_suite(r["cipher"])
            lines.append(_("## Набор шифров по частям"))
            lines.append("- " + _("Обмен ключами: `{kx}` · аутентификация: `{auth}` · шифр: `{c}` · хэш: `{mac}`")
                         .format(kx=p["kx"], auth=p["auth"], c=p["cipher"], mac=p["mac"]))
            lines.append("- " + _("Прямая секретность: **{pfs}** · AEAD: **{aead}**")
                         .format(pfs="✔" if p["pfs"] else "✘", aead="✔" if p["aead"] else "✘"))
        except ValueError:
            pass
        self.out.render("\n".join(lines))
        if self.on_solved:
            self.on_solved()


class DhLab(tk.Frame):
    def __init__(self, master, on_solved=None, bg=None):
        bg = bg or T.BG
        super().__init__(master, bg=bg)
        self.on_solved = on_solved
        self.solved = False
        label(self, _("Обмен ключами Диффи–Хеллмана"), 15, "bold").pack(anchor="w")
        label(self, _("Алиса и Боб договариваются об общем секрете, передавая по сети только открытые числа. Ева видит "
                      "всё, что идёт по сети, но вычислить секрет не может. Меняйте числа — всё пересчитывается."),
              10, fg=T.MUTED, wraplength=980, justify="left").pack(anchor="w", pady=(2, 10))
        form = tk.Frame(self, bg=bg)
        form.pack(fill="x")
        self.vars = {k: tk.StringVar(value=v) for k, v in (("p", "23"), ("g", "5"), ("a", "6"), ("b", "15"))}
        hints = {"p": _("простое число (модуль)"), "g": _("основание (генератор)"), "a": _("секрет Алисы"),
                 "b": _("секрет Боба")}
        for i, k in enumerate(("p", "g", "a", "b")):
            label(form, f"{k} — {hints[k]}", 9, fg=T.MUTED).grid(row=0, column=i, sticky="w", padx=(0, 14))
            entry(form, width=22 if k in "pg" else 18, textvariable=self.vars[k]).grid(row=1, column=i, sticky="w",
                                                                                     padx=(0, 14), ipady=2)
            self.vars[k].trace_add("write", lambda *a: self.update_view())
        bt = tk.Frame(self, bg=bg)
        bt.pack(fill="x", pady=8)
        FlatButton(bt, _("Случайные секреты"), self.randomize).pack(side="left")
        FlatButton(bt, _("Большие числа (127 бит)"), self.big).pack(side="left", padx=8)
        FlatButton(bt, _("Ева: подобрать секрет перебором"), self.eve, kind="danger").pack(side="left")
        self.err = label(self, "", 10, fg=T.BAD)
        self.err.pack(anchor="w")

        cols = tk.Frame(self, bg=bg)
        cols.pack(fill="x", pady=(4, 0))
        self.panels = {}
        for key, title, col in (("alice", _("АЛИСА"), T.ACCENT), ("wire", _("ОТКРЫТЫЙ КАНАЛ — видит Ева"), T.BAD),
                                ("bob", _("БОБ"), T.GOOD)):
            cc = tk.Frame(cols, bg=T.tint(col, 0.85, T.BG), highlightthickness=1, highlightbackground=col)
            cc.pack(side="left", fill="both", expand=True, padx=4)
            tk.Label(cc, text=title, font=T.F(9, "bold"), fg=col, bg=cc["bg"]).pack(anchor="w", padx=14, pady=(10, 4))
            body = tk.Label(cc, text="", font=T.F(10, mono=True), fg=T.TEXT, bg=cc["bg"], justify="left", anchor="w",
                            wraplength=300)
            body.pack(anchor="w", padx=14, pady=(0, 12))
            self.panels[key] = body
        self.result = label(self, "", 13, "bold", wraplength=980, justify="left")
        self.result.pack(anchor="w", pady=(10, 2))
        self.expl = RichText(self, height=7, scroll=False, padx=0, pady=4, size=10, width=100)
        self.expl.pack(fill="x")
        self.expl.render(_("**Почему это работает:** (g^b)^a = (g^a)^b = g^(ab) mod p — оба получают одно число.\n"
                           "**Почему Ева бессильна:** зная g, p и A = g^a mod p, найти a — это задача **дискретного "
                           "логарифма**. Для p из 2048 бит её не решить за всё время существования Вселенной.\n"
                           "> В TLS 1.3 вместо чисел по модулю обычно используют эллиптическую кривую **X25519** — тот же "
                           "принцип, но ключи всего 32 байта. Секреты a и b — **эфемерные**: новые для каждого соединения "
                           "(прямая секретность)."))
        self.update_view()

    def _ints(self):
        return {k: int(v.get().strip()) for k, v in self.vars.items()}

    def update_view(self):
        try:
            n = self._ints()
            p, g, a, b = n["p"], n["g"], n["a"], n["b"]
            if p < 3 or not (1 < g < p) or a < 1 or b < 1:
                raise ValueError
        except ValueError:
            self.err.configure(text=_("Нужны целые числа: p ≥ 3, 1 < g < p, секреты ≥ 1"))
            return
        self.err.configure(text="" if crypto_toy.is_prime(p) else _("⚠ p не простое — так делать нельзя, но посчитать можно"))
        r = crypto_toy.dh_exchange(p, g, a, b)
        got, secret = _("получила B = {v}"), _("секрет a = {v}")
        self.panels["alice"].configure(
            text=secret.format(v=a) + f"\n\nA = g^a mod p\n  = {g}^{a} mod {p}\n  = {r['A']}\n\n" + got.format(v=r["B"])
            + f"\ns = B^a mod p = {r['s_alice']}")
        self.panels["wire"].configure(
            text=f"p = {p}\ng = {g}\nA = {r['A']}   " + _("(Алиса → Боб)") + f"\nB = {r['B']}   " + _("(Боб → Алиса)")
            + "\n\n" + _("a, b и s по сети НЕ передаются"))
        self.panels["bob"].configure(
            text=_("секрет b = {v}").format(v=b) + f"\n\nB = g^b mod p\n  = {g}^{b} mod {p}\n  = {r['B']}\n\n"
            + _("получил A = {v}").format(v=r["A"]) + f"\ns = A^b mod p = {r['s_bob']}")
        same = r["s_alice"] == r["s_bob"]
        text = _("Общий секрет: {s}").format(s=r["s_alice"]) + ("" if same else f" ≠ {r['s_bob']}")
        self.result.configure(text=("✔  " if same else "✘  ") + text, fg=T.GOOD if same else T.BAD)
        if same and not self.solved and self.on_solved and (a, b) != (6, 15):
            self.solved = True
            self.on_solved()

    def randomize(self):
        try:
            p = int(self.vars["p"].get())
        except ValueError:
            p = 23
        self.vars["a"].set(str(random.randint(2, max(3, min(p - 2, 10 ** 30)))))
        self.vars["b"].set(str(random.randint(2, max(3, min(p - 2, 10 ** 30)))))

    def big(self):
        self.vars["p"].set(str(2 ** 127 - 1))
        self.vars["g"].set("3")
        self.vars["a"].set(str(random.getrandbits(120)))
        self.vars["b"].set(str(random.getrandbits(120)))

    def eve(self):
        try:
            n = self._ints()
        except ValueError:
            return
        r = crypto_toy.dh_exchange(n["p"], n["g"], n["a"], n["b"])
        t0 = time.perf_counter()
        x, tries = crypto_toy.brute_force_dlog(n["g"], r["A"], n["p"], limit=300_000)
        ms = round((time.perf_counter() - t0) * 1000)
        if x is not None:
            self.result.configure(text=_("Ева нашла подходящий секрет a = {x} за {t} попыток ({ms} мс). Маленькое p — "
                                         "не защита!").format(x=x, t=tries, ms=ms), fg=T.BAD)
        else:
            self.result.configure(text=_("Ева перебрала {t} вариантов за {ms} мс и сдалась. Всего вариантов ≈ 2^{bits} — "
                                         "перебор невозможен.").format(t=tries, ms=ms, bits=n["p"].bit_length()), fg=T.GOOD)


class HashLab(tk.Frame):
    def __init__(self, master, on_solved=None, bg=None):
        bg = bg or T.BG
        super().__init__(master, bg=bg)
        label(self, _("SHA-256: лавинный эффект"), 15, "bold").pack(anchor="w")
        label(self, _("Хэш-функция превращает любые данные в «отпечаток» из 256 бит. Измените один символ во второй "
                      "строке — изменится примерно половина битов. TLS использует хэши для вывода ключей, проверки "
                      "рукопожатия (Finished) и в подписях сертификатов."), 10, fg=T.MUTED, wraplength=980,
              justify="left").pack(anchor="w", pady=(2, 10))
        self.v1 = tk.StringVar(value=_("Перевести 100 рублей Бобу"))
        self.v2 = tk.StringVar(value=_("Перевести 900 рублей Бобу"))
        self.texts = []
        for var, title in ((self.v1, _("Сообщение 1")), (self.v2, _("Сообщение 2"))):
            label(self, title, 10, "bold", fg=T.MUTED).pack(anchor="w", pady=(6, 2))
            entry(self, width=70, size=12, textvariable=var).pack(anchor="w", ipady=3)
            t = tk.Text(self, height=2, bg=T.CODE_BG, fg=T.TEXT, font=T.F(11, mono=True), relief="flat", padx=12,
                        pady=6, highlightthickness=0, insertwidth=0, cursor="arrow", width=70)
            t.pack(anchor="w", pady=(4, 0))
            t.tag_configure("diff", foreground=T.WARN, background=T.tint(T.WARN, 0.8, T.CODE_BG))
            self.texts.append(t)
            var.trace_add("write", lambda *a: self.update_view())
        self.result = label(self, "", 13, "bold")
        self.result.pack(anchor="w", pady=(12, 0))
        self.bar = tk.Canvas(self, width=640, height=18, bg=T.PANEL2, highlightthickness=0)
        self.bar.pack(anchor="w", pady=6)
        self.update_view()

    def update_view(self):
        h1 = crypto_toy.sha256_hex(self.v1.get())
        h2 = crypto_toy.sha256_hex(self.v2.get())
        for t, h, other in ((self.texts[0], h1, h2), (self.texts[1], h2, h1)):
            t.configure(state="normal")
            t.delete("1.0", "end")
            t.insert("end", h)
            for i, (a, b) in enumerate(zip(h, other)):
                if a != b:
                    t.tag_add("diff", f"1.{i}", f"1.{i + 1}")
            t.configure(state="disabled")
        d = crypto_toy.bit_diff(h1, h2)
        if h1 == h2:
            self.result.configure(text=_("Сообщения одинаковые → хэши совпадают полностью"), fg=T.GOOD)
        else:
            self.result.configure(text=_("Отличается {d} из 256 бит ({p}) — подделку сразу видно").format(
                d=d, p=f"{d / 256:.0%}"), fg=T.WARN)
        self.bar.delete("all")
        self.bar.create_rectangle(0, 0, 640 * d / 256, 18, fill=T.WARN, outline="")
        self.bar.create_line(320, 0, 320, 18, fill=T.TEXT, dash=(2, 2))
