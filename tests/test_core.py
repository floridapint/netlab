"""Тесты чистой логики (без GUI). Запуск: python -m unittest -v"""
import queue
import random
import socket
import time
import unittest

from netlab.core import crypto_toy, ipcalc, tasks
from netlab.core.protocols import (IPV4_HEADER, TCP_HEADER, UDP_HEADER, build_udp, flags_names, flags_value,
                                   internet_checksum, verify_udp)
from netlab.core.questions import QUESTIONS, all_questions
from netlab.core.sockets_lab import ClientReader, TcpEchoServer, UdpEchoServer, hexdump


class TestIpCalc(unittest.TestCase):
    def test_subnet_26(self):
        i = ipcalc.subnet_info("192.168.10.77", 26)
        self.assertEqual(i["network"], "192.168.10.64")
        self.assertEqual(i["broadcast"], "192.168.10.127")
        self.assertEqual(i["first"], "192.168.10.65")
        self.assertEqual(i["last"], "192.168.10.126")
        self.assertEqual(i["hosts"], 62)
        self.assertEqual(i["mask"], "255.255.255.192")

    def test_edge_prefixes(self):
        self.assertEqual(ipcalc.subnet_info("10.0.0.1", 31)["hosts"], 2)
        self.assertEqual(ipcalc.subnet_info("10.0.0.1", 32)["hosts"], 1)
        self.assertEqual(ipcalc.subnet_info("10.20.30.40", 8)["network"], "10.0.0.0")

    def test_masks(self):
        self.assertEqual(ipcalc.prefix_to_mask(20), "255.255.240.0")
        self.assertEqual(ipcalc.mask_to_prefix("255.255.255.224"), 27)
        with self.assertRaises(ValueError):
            ipcalc.mask_to_prefix("255.0.255.0")

    def test_parse_cidr(self):
        self.assertEqual(ipcalc.parse_cidr("10.0.0.5/8"), ("10.0.0.5", 8))
        self.assertEqual(ipcalc.parse_cidr("10.0.0.5 255.255.0.0"), ("10.0.0.5", 16))
        self.assertEqual(ipcalc.parse_cidr("10.0.0.5/255.255.255.0"), ("10.0.0.5", 24))
        with self.assertRaises(ValueError):
            ipcalc.parse_cidr("300.1.1.1/24")

    def test_kinds(self):
        self.assertTrue(ipcalc.is_rfc1918("172.31.255.1"))
        self.assertFalse(ipcalc.is_rfc1918("172.32.0.1"))
        self.assertIn("loopback", ipcalc.addr_kind("127.0.0.1"))
        self.assertIn("публичный", ipcalc.addr_kind("8.8.8.8"))
        self.assertEqual(ipcalc.to_bin("192.168.1.10"), "11000000.10101000.00000001.00001010")


class TestTasks(unittest.TestCase):
    GENS = [tasks.subnet_task, tasks.mask_task, tasks.binary_task, tasks.same_net_task, tasks.private_task,
            tasks.tcp_seq_task, tasks.udp_len_task, tasks.tcp_flags_task, tasks.port_task]

    def test_generators_self_consistent(self):
        rng = random.Random(42)
        for gen in self.GENS:
            for _ in range(200):
                t = gen(rng)
                self.assertTrue(t.text and t.fields and t.explain, gen.__name__)
                for f in t.fields:
                    self.assertTrue(f.check(f.answer), f"{gen.__name__}: {f.label}={f.answer}")
                    self.assertFalse(f.check(""), gen.__name__)

    def test_field_normalization(self):
        f = tasks.Field("x", "да", tasks.YES)
        self.assertTrue(f.check(" Да "))
        self.assertTrue(f.check("yes"))
        self.assertFalse(f.check("нет"))


class TestProtocols(unittest.TestCase):
    def test_header_sizes(self):
        self.assertEqual(sum(f.bits for f in IPV4_HEADER if not f.optional), 160)
        self.assertEqual(sum(f.bits for f in TCP_HEADER if not f.optional), 160)
        self.assertEqual(sum(f.bits for f in UDP_HEADER if not f.optional), 64)

    def test_flags(self):
        self.assertEqual(flags_value(["SYN", "ACK"]), 0x12)
        self.assertEqual(flags_names(0x11), ["ACK", "FIN"])

    def test_checksum_rfc1071_example(self):
        # пример из RFC 1071: 00 01 f2 03 f4 f5 f6 f7 → сумма 0xddf2, дополнение 0x220d
        self.assertEqual(internet_checksum(bytes.fromhex("0001f203f4f5f6f7")), 0x220D)

    def test_udp_roundtrip(self):
        for payload in (b"", b"a", "Привет, UDP!".encode(), bytes(range(256))):
            dg = build_udp("192.168.1.10", "8.8.8.8", 51515, 53, payload)
            self.assertEqual(len(dg), 8 + len(payload))
            self.assertTrue(verify_udp("192.168.1.10", "8.8.8.8", dg))
            broken = bytearray(dg)
            broken[-1 if payload else 0] ^= 0xFF
            self.assertFalse(verify_udp("192.168.1.10", "8.8.8.8", bytes(broken)))


class TestCrypto(unittest.TestCase):
    def test_dh(self):
        r = crypto_toy.dh_exchange(23, 5, 6, 15)
        self.assertEqual((r["A"], r["B"]), (8, 19))
        self.assertEqual(r["s_alice"], r["s_bob"])
        self.assertEqual(r["s_alice"], 2)

    def test_primes(self):
        self.assertTrue(crypto_toy.is_prime(2 ** 127 - 1))
        self.assertFalse(crypto_toy.is_prime(2 ** 127 + 1))
        self.assertEqual([n for n in range(30) if crypto_toy.is_prime(n)], [2, 3, 5, 7, 11, 13, 17, 19, 23, 29])

    def test_brute_force(self):
        x, _ = crypto_toy.brute_force_dlog(5, 8, 23)
        self.assertEqual(pow(5, x, 23), 8)

    def test_avalanche(self):
        h1, h2 = crypto_toy.sha256_hex("a"), crypto_toy.sha256_hex("b")
        self.assertGreater(crypto_toy.bit_diff(h1, h2), 80)

    def test_cipher_suites(self):
        p = crypto_toy.parse_cipher_suite("TLS_AES_128_GCM_SHA256")
        self.assertTrue(p["tls13"] and p["pfs"] and p["aead"])
        p = crypto_toy.parse_cipher_suite("TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256")
        self.assertEqual((p["kx"], p["auth"], p["cipher"], p["mac"]), ("ECDHE", "RSA", "AES_128_GCM", "SHA256"))
        self.assertFalse(p["warnings"])
        p = crypto_toy.parse_cipher_suite("ECDHE-ECDSA-CHACHA20-POLY1305")
        self.assertEqual((p["kx"], p["auth"]), ("ECDHE", "ECDSA"))
        self.assertTrue(p["aead"])
        p = crypto_toy.parse_cipher_suite("AES256-SHA")
        self.assertEqual(p["kx"], "RSA")
        self.assertFalse(p["pfs"])
        p = crypto_toy.parse_cipher_suite("TLS_RSA_WITH_RC4_128_MD5")
        self.assertTrue(any("RC4" in w for w in p["warnings"]))
        with self.assertRaises(ValueError):
            crypto_toy.parse_cipher_suite("")


class TestQuestions(unittest.TestCase):
    def test_bank(self):
        self.assertEqual(set(QUESTIONS), {"osi", "tcpip", "ip", "udp", "tcp", "tls"})
        for topic, qs in QUESTIONS.items():
            self.assertGreaterEqual(len(qs), 10, topic)
            for q in qs:
                self.assertEqual(len(q["options"]), 4, q["q"])
                self.assertEqual(len(set(q["options"])), 4, q["q"])
                self.assertTrue(q["explain"])
        self.assertEqual(len(all_questions()), sum(len(v) for v in QUESTIONS.values()))


class TestSockets(unittest.TestCase):
    def _drain(self, events, until, timeout=3.0):
        got = []
        end = time.time() + timeout
        while time.time() < end:
            try:
                ev = events.get(timeout=0.05)
            except queue.Empty:
                continue
            got.append(ev)
            if until(got):
                break
        return got

    def test_hexdump(self):
        self.assertTrue(hexdump(b"hello").startswith("0000  68 65 6c 6c 6f"))

    def test_udp_echo(self):
        events = queue.Queue()
        srv = UdpEchoServer(events)
        port = srv.start()
        cli = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            reader = ClientReader(cli, events, udp=True)
            cli.sendto(b"ping", ("127.0.0.1", port))
            got = self._drain(events, lambda g: any(e["src"] == "client" and e["kind"] == "recv" for e in g))
            self.assertTrue(any(e.get("data") == b"ping" and e["src"] == "client" for e in got))
            reader.stop()
        finally:
            cli.close()
            srv.stop()

    def test_tcp_stream_coalescing(self):
        events = queue.Queue()
        srv = TcpEchoServer(events, read_delay=0.4)
        port = srv.start()
        cli = socket.create_connection(("127.0.0.1", port))
        try:
            for part in (b"a|", b"b|", b"c|"):
                cli.sendall(part)
            got = self._drain(events, lambda g: any(e["src"] == "server" and e["kind"] == "recv" for e in g))
            recv = [e for e in got if e["src"] == "server" and e["kind"] == "recv"]
            self.assertEqual(recv[0]["data"], b"a|b|c|")  # три send() → один recv()
        finally:
            cli.close()
            srv.stop()


if __name__ == "__main__":
    unittest.main()
