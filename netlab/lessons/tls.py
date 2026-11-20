"""Урок 6. SSL и TLS."""
from __future__ import annotations

from .. import theme as T
from ..i18n import N_, _
from ..ui.animation import Scenario, Step, Tween, later
from ..ui.interactive import CipherDecoder, TlsVersions
from ..ui.labs import DhLab, HashLab, TlsProbeLab
from ..ui.scene import Chip, SequenceScenario, fade_in, grow_line, node_box, round_rect
from .base import LessonSpec

THEORY = r"""
# SSL и TLS
**TLS (Transport Layer Security)** защищает данные поверх TCP: на нём работают HTTPS, защищённая почта, многие VPN и API. **SSL (Secure Sockets Layer)** — его предшественник от Netscape. Все версии SSL сломаны и запрещены, но по привычке все говорят «SSL-сертификат».

## Три задачи TLS
- **Конфиденциальность** — посторонний не прочитает данные (симметричное шифрование AES / ChaCha20).
- **Целостность** — данные нельзя незаметно изменить (AEAD-тег).
- **Аутентификация** — вы говорите именно с bank.example, а не с самозванцем (сертификат + цифровая подпись).

## История версий
|Версия|Год|Статус|
|---|---|---|
|SSL 2.0|1995|Запрещён (RFC 6176)|
|SSL 3.0|1996|Запрещён (RFC 7568) — атака POODLE|
|TLS 1.0|1999|Устарел (RFC 8996) — BEAST, старые хэши|
|TLS 1.1|2006|Устарел (RFC 8996)|
|TLS 1.2|2008|Используется; безопасен с правильными шифрами|
|TLS 1.3|2018|Современный стандарт (RFC 8446): быстрее и проще|

## Криптография за две минуты
- **Симметричное шифрование** — один ключ и шифрует, и расшифровывает (AES, ChaCha20). Очень быстро. Но как договориться о ключе через сеть, которую подслушивают?
- **Асимметричная криптография** — пара ключей: открытый и закрытый (RSA, ECDSA, Ed25519). Медленно, но позволяет делать **подписи** и договариваться о ключах.
- **Обмен Диффи–Хеллмана (ECDHE)** — две стороны вырабатывают общий секрет, передавая только открытые значения. Подслушивающий вычислить его не может. (Попробуйте в «Практике».)
- **Хэш-функция** (SHA-256) — «отпечаток» данных: малейшее изменение входа полностью меняет результат.
> TLS комбинирует всё: ECDHE — чтобы договориться о ключе, подпись и сертификат — чтобы проверить сервер, симметричный AEAD-шифр — чтобы быстро шифровать трафик.

## Рукопожатие TLS 1.2 (2 RTT)
1. **ClientHello** — версии, наборы шифров, случайное число, **SNI** (имя сайта).
2. **ServerHello, Certificate, ServerKeyExchange, ServerHelloDone** — выбранный шифр, сертификат, параметры ECDHE, подписанные ключом сервера.
3. **ClientKeyExchange, ChangeCipherSpec, Finished** — клиентская часть ECDHE, переход на шифрование.
4. **ChangeCipherSpec, Finished** — сервер подтверждает. Можно передавать данные.

## Рукопожатие TLS 1.3 (1 RTT)
1. **ClientHello + key_share** — клиент сразу угадывает группу (обычно X25519) и отправляет свой открытый ключ.
2. **ServerHello + key_share**, а дальше уже **зашифрованные** EncryptedExtensions, Certificate, CertificateVerify, Finished.
3. **Finished** клиента — и сразу данные приложения.
Что ещё изменилось в 1.3: удалены RSA-обмен ключами, CBC, RC4, SHA-1, сжатие и пересогласование; осталось 5 наборов шифров; сертификат теперь тоже зашифрован; появился **0-RTT** при повторном подключении (с риском повтора запроса).

## Сертификаты и цепочка доверия
Сертификат X.509 содержит **имя** (CN и SAN — список доменов), **открытый ключ** сервера, **срок действия**, **издателя** (CA) и его **подпись**.
```
Корневой CA            (лежит в хранилище ОС / браузера)
  └─ подписал → Промежуточный CA
                  └─ подписал → bank.example
```
Браузер проверяет подписи по цепочке до доверенного корня, совпадение имени, срок действия и отзыв (OCSP/CRL). Что-то не так — предупреждение «Подключение не защищено».

## Набор шифров (cipher suite)
`TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256` (TLS 1.2) читается так:
- **ECDHE** — обмен ключами (эфемерный Диффи–Хеллман на эллиптических кривых);
- **RSA** — аутентификация сервера (тип ключа в сертификате);
- **AES_128_GCM** — симметричный шифр с проверкой целостности (AEAD);
- **SHA256** — хэш для вывода ключей.
В TLS 1.3 имя короче: `TLS_AES_128_GCM_SHA256` — обмен ключами и подпись согласуются отдельно.
> Разберите любой набор во вкладке «Интерактив → Наборы шифров».

## Прямая секретность (Forward Secrecy)
С **эфемерным** обменом (ECDHE) для каждого сеанса создаётся новый ключ и после сеанса уничтожается. Даже если через год украдут закрытый ключ сервера, записанный ранее трафик не расшифровать. В TLS 1.3 прямая секретность обязательна.

## Записи TLS
После рукопожатия данные идут **записями** (records): заголовок 5 байт (тип 23 = application_data, версия `03 03`, длина) + зашифрованные данные + тег AEAD. Именно байты `17 03 03 …` вы увидите в Wireshark вместо HTTP.

## Полезные команды
```
openssl s_client -connect example.com:443 -servername example.com
openssl s_client -connect example.com:443 -tls1_2
curl -v https://example.com
```
В Wireshark фильтр `tls.handshake` покажет сообщения рукопожатия.
"""

CL = (N_("Клиент"), N_("браузер"), T.ACCENT)
SV = (N_("Сервер"), "bank.example : 443", T.GOOD)


class _TlsSeq(SequenceScenario):
    actors = [CL, SV]
    start_y = 104

    def build_extra(self, c):
        c.create_text(440, 74, text=_("(TCP-соединение уже установлено)"), fill=T.DIM, font=T.F(8))


class Tls12Scenario(_TlsSeq):
    title = "TLS 1.2"
    intro = N_("Классическое рукопожатие TLS 1.2 с обменом ECDHE. TCP-соединение уже установлено. Следите за счётчиком "
               "**RTT** слева.")
    dy = 26
    gap = 16

    def steps(self):
        data = _("Данные")
        return [
            self.msg(0, 1, "ClientHello", _("**ClientHello**: поддерживаемые версии и наборы шифров, случайное число "
                     "client_random, расширения — в том числе **SNI** = bank.example (на одном IP может быть много "
                     "сайтов)."), "ClientHello", T.WARN),
            self.msg(1, 0, "ServerHello + Certificate + ServerKeyExchange + Done", _("Сервер выбирает версию и шифр, "
                     "присылает **сертификат** и свою половину ECDHE (**ServerKeyExchange**), подписанную закрытым "
                     "ключом сертификата — так клиент убедится, что параметры не подменили."), "ServerHello", T.WARN,
                     rtt=True, chip="ServerHello…"),
            self.note(0, _("✔ сертификат проверен, ключи вычислены"), _("Клиент проверяет цепочку сертификатов, имя и "
                      "срок, проверяет подпись ServerKeyExchange, генерирует свою половину ECDHE и вычисляет общий "
                      "секрет → ключи сессии."), _("Проверка"), color=T.GOOD, advance=26),
            self.msg(0, 1, "ClientKeyExchange + ChangeCipherSpec + Finished", _("Клиент отправляет свою половину ECDHE, "
                     "объявляет переход на шифрование (**ChangeCipherSpec**) и шлёт **Finished** — хэш всего рукопожатия, "
                     "уже зашифрованный. Если кто-то подменил сообщения, хэши не сойдутся."), _("Ключи"), T.WARN,
                     chip="ClientKeyExchange…"),
            self.msg(1, 0, "ChangeCipherSpec + Finished", _("Сервер тоже переходит на шифрование и подтверждает "
                     "рукопожатие своим **Finished**."), "Finished", T.WARN, rtt=True, chip="Finished"),
            self.msg(0, 1, _("Application Data: GET /  (зашифровано)"), _("Только теперь — данные приложения. "
                     "**2 RTT** на рукопожатие (плюс 1 RTT на TCP)."), data, T.GOOD, chip="GET /"),
            self.msg(1, 0, "Application Data: 200 OK", _("Ответ сервера тоже зашифрован ключом сессии."), data, T.GOOD,
                     chip="200 OK"),
        ]


class Tls13Scenario(_TlsSeq):
    title = "TLS 1.3"
    intro = N_("В TLS 1.3 клиент **угадывает** группу обмена ключами и сразу отправляет свой ключ. Это экономит целый RTT.")
    dy = 30
    gap = 22

    def steps(self):
        data = _("Данные")
        return [
            self.msg(0, 1, "ClientHello + key_share (X25519)", _("**ClientHello** сразу содержит **key_share** — "
                     "открытый ключ клиента для X25519 (32 байта). Клиент не ждёт, пока сервер выберет параметры."),
                     "ClientHello", T.WARN, chip="ClientHello"),
            self.msg(1, 0, "ServerHello + key_share + {Cert, Verify, Finished}", _("Сервер отвечает своим **key_share** — "
                     "общий секрет готов у обоих! Поэтому всё остальное (в фигурных скобках) уже **зашифровано**: "
                     "сертификат, подпись рукопожатия (CertificateVerify) и Finished."), "ServerHello", T.WARN, rtt=True,
                     chip="ServerHello…"),
            self.note(0, _("✔ ключи готовы, сертификат проверен"), _("Клиент вычисляет ключи, расшифровывает и проверяет "
                      "сертификат и подпись."), _("Проверка"), color=T.GOOD, advance=28),
            self.msg(0, 1, "{Finished} + Application Data: GET /", _("Клиент отправляет **Finished** и в том же полёте — "
                     "**первые данные**. Рукопожатие заняло **1 RTT**."), data, T.GOOD, chip="Finished + GET"),
            self.msg(1, 0, "Application Data: 200 OK", _("Ответ сервера. Сравните с TLS 1.2: на целый RTT быстрее — на "
                     "мобильной сети это 50–200 мс на каждое новое соединение."), data, T.GOOD, chip="200 OK"),
            Step(_("**0-RTT:** при повторном подключении клиент может отправить данные прямо в первом сообщении, "
                   "используя ключ из прошлой сессии (PSK). Но такие данные можно перехватить и **повторить**, поэтому "
                   "0-RTT разрешают только для безопасных запросов вроде GET."), None, "0-RTT"),
        ]


class EavesdropScenario(Scenario):
    title = N_("Зачем шифровать")
    intro = N_("Между клиентом и банком сидит **Ева**: она видит весь трафик (публичный Wi-Fi, взломанный роутер, "
               "провайдер). Сравним HTTP и HTTPS.")

    def build(self, c):
        self.c = c
        node_box(c, 90, 150, 140, 60, N_("Клиент"), N_("браузер"), T.ACCENT, size=12)
        node_box(c, 790, 150, 140, 60, N_("Сервер"), "bank.example", T.GOOD, size=12)
        c.create_line(160, 150, 720, 150, fill=T.BORDER, width=4)
        node_box(c, 440, 330, 150, 60, N_("Ева"), N_("перехватчик"), T.BAD, size=12)
        c.create_line(440, 154, 440, 300, fill=T.tint(T.BAD, 0.4), dash=(5, 4), width=2)
        round_rect(c, 540, 300, 866, 400, r=10, fill=T.CARD, outline=T.tint(T.BAD, 0.4))
        c.create_text(556, 316, text=_("ЧТО ВИДИТ ЕВА"), fill=T.BAD, font=T.F(8, "bold"), anchor="w")
        self.eve = c.create_text(556, 346, text="—", fill=T.MUTED, font=T.F(10, "bold", mono=True), anchor="nw", width=300)
        self.mode = c.create_text(440, 40, text="", fill=T.TEXT, font=T.F(14, "bold"))
        self.cl_status = c.create_text(90, 210, text="", fill=T.MUTED, font=T.F(9, "bold"), width=170)
        self.sv_status = c.create_text(790, 210, text="", fill=T.MUTED, font=T.F(9, "bold"), width=170)

    def _send(self, text, color, eve_text, eve_color, server_text, server_color, tamper=None):
        c = self.c
        ch = Chip(c, 165, 150, text, color, size=9, h=24)
        copy = Chip(c, 440, 150, text, color, size=8, h=20)
        c.itemconfigure(copy.tag, state="hidden")
        tws = [ch.tween_to(440, 150, 900),
               later(900, lambda: c.itemconfigure(copy.tag, state="normal")),
               copy.tween_to(440, 272, 700, delay=900),
               later(1600, lambda: (copy.delete(), c.itemconfigure(self.eve, text=eve_text, fill=eve_color)))]
        if tamper:
            tws.append(later(950, lambda: ch.set(text=tamper, color=T.BAD)))
        tws.append(ch.tween_to(715, 150, 900, delay=1000))
        tws.append(later(1950, lambda: (ch.delete(), c.itemconfigure(self.sv_status, text=server_text, fill=server_color))))
        return tws

    def steps(self):
        c = self.c
        record = "17 03 03 00 4a 8f 2c e1 9b 0d…"

        def http():
            c.itemconfigure(self.mode, text=_("HTTP — без шифрования"), fill=T.BAD)
            return self._send("POST /login  pass=qwerty123", T.WARN, "pass=qwerty123\n\n" + _("Пароль украден!"), T.BAD,
                              _("получено:") + "\npass=qwerty123", T.MUTED)

        def https():
            c.itemconfigure(self.mode, text=_("HTTPS — HTTP внутри TLS"), fill=T.GOOD)
            c.itemconfigure(self.sv_status, text="")
            return self._send(record, T.GOOD, "17 03 03 00 4a 8f 2c e1…\n\n" + _("Шум. Ключа сессии у меня нет."), T.MUTED,
                              _("✔ расшифровано:") + "\nPOST /login", T.GOOD)

        def tamper():
            c.itemconfigure(self.mode, text=_("Ева пытается изменить данные"), fill=T.WARN)
            c.itemconfigure(self.sv_status, text="")
            return self._send(record, T.GOOD, _("меняю байт 8f → ff…"), T.WARN,
                              _("✘ тег AEAD не совпал") + "\nalert bad_record_mac\n" + _("соединение разорвано"), T.BAD,
                              tamper="17 03 03 00 4a ff 2c e1 9b 0d…")

        def mitm():
            c.itemconfigure(self.mode, text=_("Ева выдаёт себя за банк (MITM)"), fill=T.BAD)
            c.itemconfigure(self.sv_status, text="")
            c.itemconfigure(self.eve, text=_("Вот мой «сертификат»\nbank.example…"), fill=T.WARN)
            ch = Chip(c, 440, 300, _("Certificate: bank.example (подписан Евой)"), T.BAD, size=8, h=22)
            verdict = _("✘ издатель не доверенный CA\n→ «Подключение не защищено»")
            return [ch.tween_path([(440, 190), (165, 190)], 1600),
                    later(1650, lambda: (ch.delete(), c.itemconfigure(self.cl_status, text=verdict, fill=T.BAD)))]

        return [
            Step(_("**HTTP**: логин и пароль идут открытым текстом. Ева просто копирует их из потока."), http, "HTTP"),
            Step(_("**HTTPS**: те же данные упакованы в зашифрованную TLS-запись. Ева видит только заголовок записи "
                   "(`17 03 03` — application data, TLS 1.2+) и случайный на вид шум."), https, "HTTPS"),
            Step(_("Ева меняет один байт шифротекста. Сервер проверяет **тег AEAD** (AES-GCM / ChaCha20-Poly1305) — "
                   "он не сходится, запись отвергается, соединение рвётся. Незаметно изменить данные нельзя."), tamper,
                 _("Целостность")),
            Step(_("Ева перехватывает соединение и подсовывает свой сертификат на имя bank.example. Но подписать его "
                   "доверенным CA она не может — браузер показывает предупреждение. Это **аутентификация**."), mitm, "MITM"),
            Step(_("**Итог: TLS даёт три гарантии** — конфиденциальность (Ева не читает), целостность (Ева не меняет) и "
                   "аутентификацию (Ева не притворится сервером). Главное — не нажимать «всё равно перейти» на "
                   "предупреждении о сертификате!"), None, _("Итог")),
        ]


class CertChainScenario(Scenario):
    title = N_("Цепочка доверия")
    intro = N_("Почему браузер верит, что сервер — действительно bank.example? Потому что может построить **цепочку "
               "подписей** до корневого центра сертификации, которому доверяет ОС.")

    def build(self, c):
        self.c = c
        self.cards = {}
        subj, iss, term = _("Субъект: {v}"), _("Издатель: {v}"), _("Срок: {v}")
        specs = {
            "root": (30, "Example Root CA", [subj.format(v="Example Root CA"), _("Издатель: сам себя (самоподписан)"),
                                             term.format(v="2015 – 2035")], T.ACCENT2),
            "mid": (170, "Example Issuing CA 2", [subj.format(v="Example Issuing CA 2"), iss.format(v="Example Root CA"),
                                                  term.format(v="2024 – 2027")], T.WARN),
            "leaf": (310, "bank.example", ["SAN: bank.example, www.bank.example", iss.format(v="Example Issuing CA 2"),
                                           term.format(v="2025 – 2026")], T.GOOD),
        }
        for key, (y, title, lines, col) in specs.items():
            r = round_rect(c, 60, y, 420, y + 100, r=10, fill=T.tint(col, 0.82), outline=col, width=2)
            items = [(r, "fill", T.tint(col, 0.82)), (r, "outline", col)]
            t = c.create_text(78, y + 18, text=title, fill=T.TEXT, font=T.F(12, "bold"), anchor="w")
            items.append((t, "fill", T.TEXT))
            for i, line in enumerate(lines):
                items.append((c.create_text(78, y + 44 + i * 18, text=line, fill=T.MUTED, font=T.F(9), anchor="w"),
                              "fill", T.MUTED))
            self.cards[key] = items
            for item, attr, _col in items:
                c.itemconfigure(item, **{attr: T.CANVAS})
        round_rect(c, 500, 30, 860, 200, r=10, fill=T.CARD, outline=T.BORDER)
        c.create_text(516, 48, text=_("ДОВЕРЕННЫЕ КОРНИ (хранилище ОС / браузера)"), fill=T.MUTED, font=T.F(8, "bold"),
                      anchor="w")
        self.store = {}
        for i, name in enumerate(["Global Trust Root R1", "Example Root CA", "Sample Secure Root G2",
                                  "Demo Certification Authority", _("… ещё ~150 корней")]):
            y = 76 + i * 25
            self.store[i] = (c.create_rectangle(508, y - 11, 852, y + 11, fill=T.CARD, outline=""),
                             c.create_text(520, y, text=name, fill=T.TEXT if i < 4 else T.DIM, font=T.F(9), anchor="w"))
        round_rect(c, 500, 230, 860, 420, r=10, fill=T.CARD, outline=T.BORDER)
        c.create_text(516, 248, text=_("ПРОВЕРКИ БРАУЗЕРА"), fill=T.MUTED, font=T.F(8, "bold"), anchor="w")
        self.check_y = 276

    def _check(self, text, delay=0):
        item = self.c.create_text(516, self.check_y, text=f"✔  {text}", fill=T.CANVAS, font=T.F(9, "bold"), anchor="w")
        self.check_y += 24
        return fade_in(self.c, [(item, "fill", T.GOOD)], 500, delay)

    def _arrow(self, y1, y2, delay=0):
        c = self.c
        line = c.create_line(400, y1, 400, y1, fill=T.TEXT, width=2, arrow="last")
        lbl = c.create_text(408, (y1 + y2) / 2, text=_("подписал"), fill=T.CANVAS, font=T.F(9, "bold"), anchor="w")
        return [Tween(600, grow_line(c, line, 400, y1, 400, y2), delay=delay)] + fade_in(c, [(lbl, "fill", T.TEXT)], 400,
                                                                                          delay)

    def steps(self):
        c = self.c

        def lock():
            x, y = 560, 390
            body = c.create_rectangle(x - 12, y - 6, x + 12, y + 14, fill=T.GOOD, outline="")
            arc = c.create_arc(x - 9, y - 22, x + 9, y + 4, start=0, extent=180, style="arc", outline=T.GOOD, width=4)
            txt = c.create_text(x + 24, y + 4, text=_("Соединение защищено"), fill=T.GOOD, font=T.F(12, "bold"), anchor="w")
            return fade_in(c, [(body, "fill", T.GOOD), (arc, "outline", T.GOOD), (txt, "fill", T.GOOD)], 700)

        def store_hit():
            rect, _txt = self.store[1]
            c.itemconfigure(rect, fill=T.tint(T.GOOD, 0.7))
            line = c.create_line(420, 80, 500, 101, fill=T.GOOD, width=2, dash=(5, 3))
            return self._check(_("корень есть в хранилище доверенных"), 200) + fade_in(c, [(line, "fill", T.GOOD)], 400)

        return [
            Step(_("В рукопожатии сервер присылает **свой сертификат** и **промежуточный**. Корневой не присылается — "
                   "он уже лежит в хранилище ОС или браузера."),
                 lambda: fade_in(c, self.cards["leaf"] + self.cards["mid"], 800), _("Цепочка")),
            Step(_("Сначала простые проверки: имя сайта есть в **SAN** сертификата, срок действия не истёк."),
                 lambda: self._check(_("имя bank.example есть в SAN")) + self._check(_("срок действия в порядке"), 300),
                 _("Имя и срок")),
            Step(_("Подпись на сертификате bank.example проверяется **открытым ключом промежуточного CA**. Подделать её "
                   "без закрытого ключа CA невозможно."),
                 lambda: self._arrow(270, 310) + self._check(_("подпись bank.example верна"), 500), _("Подпись 1")),
            Step(_("Промежуточный сертификат подписан **корневым CA**. Браузер берёт корень из своего хранилища."),
                 lambda: fade_in(c, self.cards["root"], 600) + self._arrow(130, 170, 400)
                 + self._check(_("подпись промежуточного CA верна"), 900), _("Подпись 2")),
            Step(_("Корневой сертификат найден в **списке доверенных** — на нём цепочка заканчивается. Дополнительно "
                   "браузер может проверить, не отозван ли сертификат (OCSP / CRL)."), store_hit, _("Корень")),
            Step(_("Все проверки пройдены → **замок** в адресной строке. Если бы любое звено не сошлось (самоподписанный "
                   "сертификат, чужое имя, истёкший срок), браузер показал бы предупреждение. Проверьте это вживую "
                   "в «Практике» на сайтах *.badssl.com."), lock, _("Доверие")),
        ]


LESSON = LessonSpec(
    key="tls", number=6, title=N_("SSL и TLS"), short="SSL / TLS",
    subtitle=N_("Шифрование, рукопожатия TLS 1.2 и 1.3, сертификаты, наборы шифров"),
    color=T.GOOD, theory=THEORY,
    scenarios=[Tls12Scenario, Tls13Scenario, EavesdropScenario, CertChainScenario],
    interactive=[(N_("Версии SSL/TLS"), lambda p: TlsVersions(p)), (N_("Наборы шифров"), lambda p: CipherDecoder(p))],
    practice=[(N_("Проверка сайта"), lambda p, solved: TlsProbeLab(p, solved)),
              (N_("Диффи–Хеллман"), lambda p, solved: DhLab(p, solved)),
              ("SHA-256", lambda p, solved: HashLab(p, solved))],
)
