"""Локальные эхо-серверы UDP и TCP для живых экспериментов (только 127.0.0.1).

События отправляются в queue.Queue в виде словарей
{"src": "server"|"client", "kind": "info"|"recv"|"send"|"error"|"warn", "text": str, "data": bytes|None},
чтобы интерфейс мог безопасно забирать их из главного потока.
"""
from __future__ import annotations

import queue
import random
import socket
import threading
import time

from ..i18n import _

HOST = "127.0.0.1"


def hexdump(data: bytes, width: int = 16) -> str:
    lines = []
    for off in range(0, len(data), width):
        chunk = data[off:off + width]
        hexs = " ".join(f"{b:02x}" for b in chunk)
        text = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{off:04x}  {hexs:<{width * 3 - 1}}  {text}")
    return "\n".join(lines) if lines else _("(пусто)")


def preview(data: bytes, limit: int = 60) -> str:
    text = data.decode("utf-8", errors="replace")
    return text if len(text) <= limit else text[:limit] + "…"


def free_closed_port() -> int:
    """Порт, на котором точно никто не слушает (для демонстрации RST)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, 0))
    port = s.getsockname()[1]
    s.close()
    return port


class _Base:
    def __init__(self, events: queue.Queue):
        self.events = events
        self.sock: socket.socket | None = None
        self.port: int | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def emit(self, kind: str, text: str, data: bytes | None = None, src: str = "server"):
        self.events.put({"src": src, "kind": kind, "text": text, "data": data})

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def stop(self):
        self._stop.set()
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
        if self._thread:
            self._thread.join(timeout=1.0)
        self._thread = None
        self.sock = None


class UdpEchoServer(_Base):
    def __init__(self, events: queue.Queue, loss: float = 0.0):
        super().__init__(events)
        self.loss = loss

    def start(self) -> int:
        self._stop.clear()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((HOST, 0))
        self.sock.settimeout(0.2)
        self.port = self.sock.getsockname()[1]
        self.emit("info", _("socket(AF_INET, SOCK_DGRAM) — UDP-сокет создан"))
        self.emit("info", _("bind(('{host}', {port})) — ждём датаграммы. listen()/accept() не нужны!")
                  .format(host=HOST, port=self.port))
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self.port

    def _loop(self):
        while not self._stop.is_set():
            try:
                data, addr = self.sock.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError:
                break
            if self.loss and random.random() < self.loss:
                self.emit("warn", _("✘ датаграмма от :{port} «потерялась в сети» (имитация) — никто не узнает и не "
                                    "повторит").format(port=addr[1]), data)
                continue
            self.emit("recv", _("recvfrom() ← {ip}:{port}  {n} байт: «{text}»")
                      .format(ip=addr[0], port=addr[1], n=len(data), text=preview(data)), data)
            try:
                self.sock.sendto(data, addr)
                self.emit("send", _("sendto() → {ip}:{port}  эхо {n} байт").format(ip=addr[0], port=addr[1], n=len(data)))
            except OSError as e:
                self.emit("error", f"sendto: {e}")


class TcpEchoServer(_Base):
    def __init__(self, events: queue.Queue, read_delay: float = 0.0):
        super().__init__(events)
        self.read_delay = read_delay
        self._conns: list[socket.socket] = []

    def start(self) -> int:
        self._stop.clear()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((HOST, 0))
        self.sock.listen(5)
        self.sock.settimeout(0.2)
        self.port = self.sock.getsockname()[1]
        self.emit("info", _("socket(AF_INET, SOCK_STREAM) — TCP-сокет создан"))
        self.emit("info", _("bind(('{host}', {port})) + listen() — состояние LISTEN, ждём SYN")
                  .format(host=HOST, port=self.port))
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._thread.start()
        return self.port

    def _accept_loop(self):
        while not self._stop.is_set():
            try:
                conn, addr = self.sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            self._conns.append(conn)
            self.emit("info", _("accept() → рукопожатие завершено, клиент {ip}:{port} (ESTABLISHED)")
                      .format(ip=addr[0], port=addr[1]))
            threading.Thread(target=self._handle, args=(conn, addr), daemon=True).start()

    def _handle(self, conn: socket.socket, addr):
        conn.settimeout(0.3)
        while not self._stop.is_set():
            if self.read_delay:
                time.sleep(self.read_delay)
            try:
                data = conn.recv(4096)
            except socket.timeout:
                continue
            except OSError as e:
                self.emit("error", f"recv: {e}")
                break
            if not data:
                self.emit("warn", _("recv() вернул 0 байт → клиент :{port} прислал FIN. Закрываем и мы (close).")
                          .format(port=addr[1]))
                break
            self.emit("recv", _("recv() ← {n} байт за один вызов: «{text}»").format(n=len(data), text=preview(data)), data)
            try:
                conn.sendall(data)
                self.emit("send", _("sendall() → эхо {n} байт").format(n=len(data)))
            except OSError as e:
                self.emit("error", f"sendall: {e}")
                break
        try:
            conn.close()
        except OSError:
            pass

    def stop(self):
        for c in self._conns:
            try:
                c.close()
            except OSError:
                pass
        self._conns.clear()
        super().stop()


class ClientReader:
    """Фоновое чтение ответов для клиентского сокета (UDP или TCP)."""

    def __init__(self, sock: socket.socket, events: queue.Queue, udp: bool):
        self.sock, self.events, self.udp = sock, events, udp
        self._stop = threading.Event()
        sock.settimeout(0.2)
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _emit(self, kind, text, data=None):
        self.events.put({"src": "client", "kind": kind, "text": text, "data": data})

    def _loop(self):
        while not self._stop.is_set():
            try:
                if self.udp:
                    data, addr = self.sock.recvfrom(65535)
                    self._emit("recv", _("recvfrom() ← :{port}  {n} байт: «{text}»")
                               .format(port=addr[1], n=len(data), text=preview(data)), data)
                else:
                    data = self.sock.recv(4096)
                    if not data:
                        self._emit("warn", _("recv() вернул 0 байт — сервер закрыл соединение (FIN)"), b"")
                        break
                    self._emit("recv", _("recv() ← {n} байт: «{text}»").format(n=len(data), text=preview(data)), data)
            except socket.timeout:
                continue
            except OSError:
                break

    def stop(self):
        self._stop.set()
