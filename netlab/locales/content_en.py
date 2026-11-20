"""English content: lesson theory, cheat sheet and the question bank."""


def Q(q, options, explain):
    return {"q": q, "options": options, "explain": explain}


THEORY = {}

THEORY["osi"] = r"""
# The OSI model
The OSI model (Open Systems Interconnection, ISO/IEC 7498) is a reference model that splits network communication into **7 layers**. Each layer solves its own task and uses the services of the layer below without knowing how it works inside.
> Why bother? The model is a common language for engineers. “It's a layer 2 problem” immediately tells you to look at switches, VLANs or MAC addresses, not at the application.

## The seven layers
|#|Layer|PDU|Examples|
|---|---|---|---|
|7|Application|Data|HTTP, DNS, SMTP, SSH|
|6|Presentation|Data|TLS*, UTF-8, JPEG|
|5|Session|Data|RPC, NetBIOS|
|4|Transport|Segment / datagram|TCP, UDP, QUIC|
|3|Network|Packet|IPv4, IPv6, ICMP|
|2|Data Link|Frame|Ethernet, Wi-Fi, ARP*|
|1|Physical|Bits|cable, fiber, radio|
* TLS and ARP don't fit the model perfectly: TLS is often placed between layers 4 and 7, ARP between 2 and 3.
> Mnemonic, top to bottom: **A**ll **P**eople **S**eem **T**o **N**eed **D**ata **P**rocessing. Bottom to top: **P**lease **D**o **N**ot **T**hrow **S**ausage **P**izza **A**way.

## Encapsulation
When an application sends data, it goes **down** the layers, and each layer adds its own **header** (the data link layer also adds a trailer). This is **encapsulation**:
```
[ Data ]                                    ← layers 7–5
[ TCP | Data ]                              ← 4: segment
[ IP | TCP | Data ]                         ← 3: packet
[ Ethernet | IP | TCP | Data | FCS ]        ← 2: frame
0101101001110010…                           ← 1: bits
```
The receiver does it in reverse — **decapsulation**: each layer reads “its” header, strips it and passes the contents up.
> Layer N “talks” to layer N on the other side through its header (peer-to-peer), but physically the data always goes down → across the wire → up. Watch the “Encapsulation” animation.

## Which devices work at which layer
- **Cable, hub, repeater** — L1: they just repeat the signal.
- **Switch, access point** — L2: forward frames by MAC address using a “MAC → port” table.
- **Router** — L3: chooses the path by IP address and connects different networks.
- **Firewall, load balancer** — L3–L4, and “smart” ones (NGFW, L7 load balancers) up to L7.
- **Computer, server** — all 7 layers.

## The layers in detail
### 1. Physical
Transmits individual bits: voltages, frequencies, light, connectors, speed. Knows nothing about the meaning of the data. Examples: twisted pair (1000BASE-T), optical fiber, the Wi-Fi radio channel.
### 2. Data Link
Groups bits into **frames**, addresses devices within one local network by **MAC address** (48 bits, e.g. `3c:52:82:1a:9f:04`), detects errors (FCS/CRC).
### 3. Network
Delivery between **different networks**: logical **IP addresses**, routing, TTL, fragmentation. Protocols: IPv4, IPv6, ICMP.
### 4. Transport
Delivers data to a **specific application** by **port number**. TCP is reliable and ordered, UDP is fast with no guarantees.
### 5. Session
Sets up, maintains and tears down the “dialog” between applications. The real TCP/IP stack has no separate session layer — applications and TLS do this job.
### 6. Presentation
Responsible for the **format** of the data: encodings, serialization, compression and **encryption**.
### 7. Application
The protocols programs use directly: HTTP, DNS, SMTP, SSH, FTP.
!> The browser itself is not “layer 7”. Layer 7 is the **protocol** — HTTP — that the browser uses.

## Troubleshooting “bottom up”
1. L1: is the port LED on, is the cable / Wi-Fi connected?
2. L2: is the gateway's MAC address in the ARP table (`arp -a`)?
3. L3: did you get an IP address (`ipconfig`), does the gateway answer (`ping 192.168.1.1`)?
4. L4: is the port open (`Test-NetConnection example.com -Port 443`)?
5. L7: does the service itself respond (browser, `curl`)?
> OSI is a **reference** model. The real Internet runs on the **TCP/IP** stack (next lesson), but OSI layers are the shared vocabulary.
"""

THEORY["tcpip"] = r"""
# The TCP/IP model
The TCP/IP stack is what the **Internet actually runs on**. It predates OSI (ARPANET, 1970s; described in RFC 1122) and has **4 layers**.

## Mapping to OSI
|TCP/IP|OSI layers|Protocols|PDU|
|---|---|---|---|
|Application|7, 6, 5|HTTP, DNS, TLS, SSH, SMTP|Data|
|Transport|4|TCP, UDP, QUIC|Segment / datagram|
|Internet|3|IP, ICMP, IPsec|Packet|
|Network access (Link)|2, 1|Ethernet, Wi-Fi, ARP|Frame|
> Many textbooks use a “hybrid” 5-layer model: physical, data link, network, transport, application.

## Addressing at each layer
- **Application** — names and URLs: `https://example.com/page`.
- **Transport** — **ports** (0–65535): which program on the host the data is for. 443 is HTTPS, 53 is DNS.
- **Internet** — **IP addresses**: which host on the Internet.
- **Network access** — **MAC addresses**: which device on the local segment.
> An “IP address + port” pair is called a **socket**. A TCP connection is uniquely identified by four values: client IP and port + server IP and port.

## Ports
- **0–1023** — well-known: 22 SSH, 53 DNS, 80 HTTP, 443 HTTPS.
- **1024–49151** — registered: 3306 MySQL, 5432 PostgreSQL, 3389 RDP.
- **49152–65535** — dynamic (ephemeral): the OS hands them to clients for outgoing connections.
> The full port table is in the “Reference” section.

## What happens when you open https://example.com
1. **DNS** (usually UDP/53): the browser learns the IP address for the name.
2. **ARP**: the computer learns the MAC address of the gateway (router), if it doesn't know it yet.
3. **TCP**: a three-way handshake with the server on port 443.
4. **TLS**: the handshake, certificate verification, key agreement.
5. **HTTP**: the `GET /` request and the `200 OK` response — already inside the encrypted channel.
6. The browser renders the page and makes new requests for images, styles and scripts.
> All these steps are shown in the “Loading a website” animation.

## Helper protocols
- **ARP** — finds the MAC for an IP on the local network: “Who has 192.168.1.1? Tell 192.168.1.10”.
- **ICMP** — IP's control messages: `ping` (Echo Request/Reply), “destination unreachable”, “TTL exceeded”.
- **DHCP** — automatically hands out the IP address, mask, gateway and DNS (UDP 67/68), the DORA sequence.
- **DNS** — translates names into addresses (UDP/TCP 53).
- **NAT** — a home router replaces private addresses (192.168.x.x) with its public one so many devices can share one IP.

## The end-to-end principle
Routers in the middle of the network only handle layers 1–3. Transport and applications run **only on the end hosts**. That keeps the network simple and fast, and puts all the “smart” logic (reliability, encryption) at the edges.

## OSI or TCP/IP?
|Aspect|OSI|TCP/IP|
|---|---|---|
|Layers|7|4|
|Origin|ISO committee, “theory first”|ARPANET, “working code first”|
|Used for|Common language, teaching, troubleshooting|Real networks and the Internet|
|Session and presentation|Separate layers|Part of the application layer|
"""

THEORY["ip"] = r"""
# The IP protocol
IP (Internet Protocol) is the network-layer protocol. Its job is to deliver a **packet** from one host to another across many intermediate networks. IP works on a **best effort** basis: packets may be lost, duplicated or arrive out of order. Reliability is TCP's job.

## IPv4 addresses
32 bits, written as 4 decimal **octets**:
```
192      .168      .1        .10
11000000 .10101000 .00000001 .00001010
```
An address splits into a **network part** (the network number) and a **host part** (the device number within that network). The **mask** sets the boundary.

## Mask and prefix (CIDR)
A mask is 32 bits: ones first (network), then zeros (hosts). The `/24` notation is the number of ones.
|Prefix|Mask|Addresses|Hosts|
|---|---|---|---|
|/8|255.0.0.0|16,777,216|16,777,214|
|/16|255.255.0.0|65,536|65,534|
|/24|255.255.255.0|256|254|
|/25|255.255.255.128|128|126|
|/26|255.255.255.192|64|62|
|/27|255.255.255.224|32|30|
|/28|255.255.255.240|16|14|
|/30|255.255.255.252|4|2|
> Hosts = 2^(32 − prefix) − 2. Minus two because the **first** address is the network itself and the **last** is the broadcast address.

## Computing a subnet in your head
Example: `192.168.10.77/26`.
1. Mask /26 = 255.255.255.**192**. The “interesting” octet is the fourth.
2. Block size = 256 − 192 = **64**. Networks go in steps of 64: .0, .64, .128, .192.
3. 77 falls into block 64…127 → network `192.168.10.64`, broadcast `192.168.10.127`.
4. Hosts: `.65` – `.126`, 62 in total.
> Check yourself in “Interactive → Subnet calculator” and practice in “Practice” — exercises are generated endlessly.

## Special ranges
|Range|Purpose|
|---|---|
|10.0.0.0/8|Private network (RFC 1918)|
|172.16.0.0/12|Private network (RFC 1918): 172.16 – 172.31|
|192.168.0.0/16|Private network (RFC 1918)|
|127.0.0.0/8|Loopback — “talking to itself” (127.0.0.1)|
|169.254.0.0/16|Link-local (APIPA) — DHCP didn't answer|
|100.64.0.0/10|ISP CGNAT|
|224.0.0.0/4|Multicast (group delivery)|
|255.255.255.255|Broadcast on the local network|
Private addresses aren't routed on the Internet — to get out, the router does **NAT**.

## The IPv4 header
At least **20 bytes**. The most important fields:
- **TTL** — “time to live”: every router decrements it by 1; at zero the packet is discarded. Protects against loops; `tracert` is built on it.
- **Protocol** — what's inside: 6 = TCP, 17 = UDP, 1 = ICMP.
- **Source / Destination Address** — the sender's and recipient's IP. They **don't change** along the way (unless there's NAT).
- **Identification, Flags, Fragment Offset** — for fragmentation when a packet exceeds the link **MTU** (usually 1500 bytes).
> You can “touch” every field in “Interactive → IPv4 header”.

## Routing
A router looks at the destination IP and searches its **routing table** for the entry with the **longest matching prefix** (longest prefix match). If nothing matches, the default route `0.0.0.0/0` is used.
- The IP addresses in the packet stay the same along the whole path.
- MAC addresses change on **every** hop: a new frame is built for each one.
- A computer sends packets to other networks through its **default gateway**.

## IPv6 in brief
128 bits in hexadecimal: `2001:db8:85a3::8a2e:370:7334` (`::` replaces runs of zeros). There are enough addresses for everyone, NAT isn't needed, there's no broadcast (multicast instead), the header is a fixed 40 bytes, TTL became **Hop Limit**, and ARP was replaced by **NDP**.

## Useful commands
```
ipconfig /all            your addresses, mask, gateway, DNS (Windows)
ping 8.8.8.8             host reachability (ICMP Echo)
tracert example.com      the packet's path (traceroute on Linux/macOS)
route print              routing table
arp -a                   ARP table: IP → MAC
```
"""

THEORY["udp"] = r"""
# The UDP protocol
UDP (User Datagram Protocol, RFC 768, 1980) is the simplest transport protocol. It takes the application's data, adds an **8-byte header** and sends it. That's it.

## UDP properties
- **Connectionless** — no handshake, data can be sent immediately.
- **No guarantees** — a datagram may be lost, arrive twice or out of order. Nobody retransmits it.
- **Preserves message boundaries** — one `sendto()` = one datagram = one `recvfrom()`.
- **Light and fast** — minimal latency, the server keeps no connection state.
- **Supports broadcast and multicast** — one message to many recipients.

## The UDP header (8 bytes)
```
 0               15 16              31
+------------------+------------------+
|   Source Port    | Destination Port |
+------------------+------------------+
|      Length      |     Checksum     |
+------------------+------------------+
|              Data ...               |
```
- **Source Port** — the sender's port (where to reply). May be 0.
- **Destination Port** — the recipient's port (which application).
- **Length** — header + data length in bytes (at least 8).
- **Checksum** — computed over a pseudo-header (IP addresses, protocol, length), the header and the data. Optional in IPv4 (0), mandatory in IPv6.
> Build your own datagram in “Interactive → UDP builder” — the length and checksum are computed live.

## Where UDP is used
|Protocol|Port|Why UDP|
|---|---|---|
|DNS|53|A short request-response: easier to retry than to set up a connection|
|DHCP|67/68|The client has no IP yet — broadcast is needed|
|NTP|123|Minimal, stable latency matters|
|VoIP, video calls (RTP)|various|A late packet is useless — better to skip it|
|Online games|various|Fresh data matters more than complete data|
|QUIC / HTTP/3|443|Reliability is implemented on top of UDP by the protocol itself|
|SNMP, Syslog, TFTP|161, 514, 69|Simplicity|
> If an application on UDP needs reliability, it builds it itself: message numbers, acknowledgments, timeouts and retries. That's how DNS clients, TFTP and QUIC work.

## UDP in Python
```
import socket

# server
srv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
srv.bind(("127.0.0.1", 9999))
data, addr = srv.recvfrom(65535)     # wait for one datagram
srv.sendto(data, addr)               # echo it back

# client
cli = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
cli.sendto("hello".encode(), ("127.0.0.1", 9999))
print(cli.recvfrom(65535))
```
Notice there's no `listen()`, `accept()` or `connect()` — we just send. Try it in “Practice → Live sockets”.
!> The maximum UDP payload is 65,507 bytes (65,535 − 8 UDP − 20 IP). But datagrams larger than the MTU (~1472 bytes of data) are split into IP fragments, and losing any fragment kills the whole datagram. That's why DNS and games keep messages small.

## UDP vs TCP in one sentence
UDP is a **postcard**: drop it in the box and hope it arrives. TCP is **registered mail with a delivery receipt**: slower and more expensive, but you know it got there.
"""

THEORY["tcp"] = r"""
# The TCP protocol
TCP (Transmission Control Protocol, RFC 9293) is reliable transport on top of unreliable IP. The application sees a **byte stream** that is guaranteed to arrive **complete, uncorrupted and in order**.

## What TCP does
- **Connection setup** — the three-way handshake: SYN → SYN-ACK → ACK.
- **Byte numbering** — every byte has a sequence number.
- **Acknowledgments (ACK)** — the receiver says which byte it expects next.
- **Retransmission** — unacknowledged data is sent again: on timeout (RTO) or after 3 duplicate ACKs (fast retransmit).
- **Ordering** — segments are reassembled in the right order, duplicates are discarded.
- **Flow control** — the window keeps a slow receiver from being flooded.
- **Congestion control** — Slow Start, CUBIC, BBR reduce the rate when the network is congested.

## The three-way handshake
```
Client                                       Server (LISTEN)
SYN_SENT     ---- SYN, seq=1000 ------------>
             <--- SYN-ACK, seq=5000, ack=1001   SYN_RCVD
ESTABLISHED  ---- ACK, seq=1001, ack=5001 -->   ESTABLISHED
```
- The **ISN** (initial sequence number) is chosen **randomly** — protection against spoofing and confusion with old connections.
- The **SYN** flag “consumes” one number, so ack = ISN + 1.
- Why three messages and not two? Each side must make sure the other received **its** initial number.

## Sequence and acknowledgment numbers
- **seq** — the number of the first data byte in the segment.
- **ack** — the number of the **next** byte the receiver expects (so everything before it has arrived).
> The client sent `seq=1001` with 100 bytes (bytes 1001…1100). The server replies `ack=1101`.
Acknowledgments are **cumulative**: `ack=1301` confirms everything up to and including byte 1300.

## The window and the sliding window
The **Window** field says how many bytes the receiver can accept right now. The sender may have that much unacknowledged data “in flight” — this is the **sliding window**. A window of 0 means “stop, I can't keep up”. The bigger the window, the higher the throughput on high-latency links: throughput ≤ window / RTT.

## Flags
|Flag|Meaning|
|---|---|
|SYN|Synchronize numbers — start of a connection|
|ACK|The ack field is valid (in almost every segment)|
|FIN|The sender has finished sending data|
|RST|Immediate connection reset (port closed, error)|
|PSH|Deliver data to the application immediately|
|URG|There is urgent data (almost never used)|

## Closing a connection
Usually 4 segments: **FIN → ACK, FIN → ACK**, because each side closes **its own** direction independently (a “half-closed” connection is possible). The side that closes first goes through **TIME_WAIT** (2×MSL, usually 30–120 s) so that late segments don't end up in a new connection with the same ports.
> **RST** ends a connection instantly with no acknowledgments — for example when you connect to a closed port. Try the “closed port” button in “Practice → Live sockets”.

## TCP states
`CLOSED`, `LISTEN`, `SYN_SENT`, `SYN_RCVD`, `ESTABLISHED`, `FIN_WAIT_1`, `FIN_WAIT_2`, `CLOSE_WAIT`, `LAST_ACK`, `TIME_WAIT`. See them on your machine: `netstat -an` or `Get-NetTCPConnection` in PowerShell.

## TCP is a stream, not messages
TCP doesn't preserve `send()` boundaries. Three calls `send("one")`, `send("two")`, `send("three")` may arrive in a single `recv()` as `"onetwothree"` — or in pieces. Protocols on top of TCP separate messages themselves: by length (Content-Length in HTTP), by a delimiter (`\r\n`) or by framing (HTTP/2).
> See it live: “Practice → Live sockets”, enable the read delay and press “3 messages in a row”.

## TCP in Python
```
import socket
srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.bind(("127.0.0.1", 9000)); srv.listen()     # LISTEN
conn, addr = srv.accept()                        # wait for a handshake
data = conn.recv(4096)                           # read from the stream
conn.sendall(data)

cli = socket.create_connection(("127.0.0.1", 9000))  # SYN → SYN-ACK → ACK
cli.sendall(b"hello")
cli.close()                                           # FIN
```

## TCP or UDP?
|Aspect|TCP|UDP|
|---|---|---|
|Connection|Yes (handshake)|No|
|Reliability|Guaranteed|None|
|Ordering|Preserved|Not guaranteed|
|Message boundaries|No (stream)|Yes (datagrams)|
|Header|20–60 bytes|8 bytes|
|Startup|1 RTT handshake|Instant|
|Examples|HTTP/1.1 and 2, SSH, mail, databases|DNS, VoIP, games, QUIC|
"""

THEORY["tls"] = r"""
# SSL and TLS
**TLS (Transport Layer Security)** protects data on top of TCP: HTTPS, secure email, many VPNs and APIs run on it. **SSL (Secure Sockets Layer)** is its predecessor from Netscape. All SSL versions are broken and prohibited, but out of habit everyone still says “SSL certificate”.

## The three jobs of TLS
- **Confidentiality** — outsiders can't read the data (symmetric encryption, AES / ChaCha20).
- **Integrity** — data can't be modified unnoticed (the AEAD tag).
- **Authentication** — you are really talking to bank.example and not an impostor (certificate + digital signature).

## Version history
|Version|Year|Status|
|---|---|---|
|SSL 2.0|1995|Prohibited (RFC 6176)|
|SSL 3.0|1996|Prohibited (RFC 7568) — POODLE attack|
|TLS 1.0|1999|Deprecated (RFC 8996) — BEAST, old hashes|
|TLS 1.1|2006|Deprecated (RFC 8996)|
|TLS 1.2|2008|In use; secure with the right ciphers|
|TLS 1.3|2018|The modern standard (RFC 8446): faster and simpler|

## Cryptography in two minutes
- **Symmetric encryption** — one key both encrypts and decrypts (AES, ChaCha20). Very fast. But how do you agree on a key over a network that's being watched?
- **Asymmetric cryptography** — a key pair: public and private (RSA, ECDSA, Ed25519). Slow, but it enables **signatures** and key agreement.
- **Diffie–Hellman key exchange (ECDHE)** — two sides derive a shared secret while sending only public values. An eavesdropper can't compute it. (Try it in “Practice”.)
- **Hash function** (SHA-256) — a data “fingerprint”: the slightest change to the input completely changes the output.
> TLS combines them all: ECDHE to agree on a key, a signature and certificate to verify the server, a symmetric AEAD cipher to encrypt the traffic quickly.

## The TLS 1.2 handshake (2 RTT)
1. **ClientHello** — versions, cipher suites, a random number, **SNI** (the site name).
2. **ServerHello, Certificate, ServerKeyExchange, ServerHelloDone** — the chosen cipher, the certificate, the ECDHE parameters signed with the server's key.
3. **ClientKeyExchange, ChangeCipherSpec, Finished** — the client's half of ECDHE, switch to encryption.
4. **ChangeCipherSpec, Finished** — the server confirms. Data can now flow.

## The TLS 1.3 handshake (1 RTT)
1. **ClientHello + key_share** — the client guesses the group right away (usually X25519) and sends its public key.
2. **ServerHello + key_share**, followed by the already **encrypted** EncryptedExtensions, Certificate, CertificateVerify, Finished.
3. The client's **Finished** — and application data immediately.
What else changed in 1.3: RSA key exchange, CBC, RC4, SHA-1, compression and renegotiation were removed; only 5 cipher suites remain; the certificate is now encrypted too; **0-RTT** appeared for reconnections (with a replay caveat).

## Certificates and the chain of trust
An X.509 certificate contains the **name** (CN and SAN — a list of domains), the server's **public key**, the **validity period**, the **issuer** (CA) and the issuer's **signature**.
```
Root CA                (lives in the OS / browser store)
  └─ signed → Intermediate CA
                  └─ signed → bank.example
```
The browser checks the signatures up the chain to a trusted root, the name match, the validity dates and revocation (OCSP/CRL). Anything wrong — a “Your connection is not private” warning.

## Cipher suites
`TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256` (TLS 1.2) reads like this:
- **ECDHE** — key exchange (ephemeral elliptic-curve Diffie–Hellman);
- **RSA** — server authentication (the key type in the certificate);
- **AES_128_GCM** — a symmetric cipher with integrity checking (AEAD);
- **SHA256** — the hash for key derivation.
In TLS 1.3 the name is shorter: `TLS_AES_128_GCM_SHA256` — key exchange and signature are negotiated separately.
> Decode any suite in “Interactive → Cipher suites”.

## Forward secrecy
With an **ephemeral** exchange (ECDHE) a new key is created for each session and destroyed afterwards. Even if the server's private key is stolen a year later, previously recorded traffic can't be decrypted. Forward secrecy is mandatory in TLS 1.3.

## TLS records
After the handshake data travels in **records**: a 5-byte header (type 23 = application_data, version `03 03`, length) + the encrypted data + the AEAD tag. Those `17 03 03 …` bytes are what you'll see in Wireshark instead of HTTP.

## Useful commands
```
openssl s_client -connect example.com:443 -servername example.com
openssl s_client -connect example.com:443 -tls1_2
curl -v https://example.com
```
In Wireshark the `tls.handshake` filter shows the handshake messages.
"""

CHEAT = r"""
# Cheat sheet
## OSI at a glance
|#|Layer|PDU|Address|Device|Protocols|
|---|---|---|---|---|---|
|7|Application|Data|URL, name|—|HTTP, DNS, SMTP|
|6|Presentation|Data|—|—|TLS, UTF-8, JPEG|
|5|Session|Data|—|—|RPC, NetBIOS|
|4|Transport|Segment|Port|L4 firewall|TCP, UDP|
|3|Network|Packet|IP|Router|IP, ICMP|
|2|Data Link|Frame|MAC|Switch|Ethernet, ARP|
|1|Physical|Bits|—|Hub, cable|1000BASE-T|

## TCP vs UDP
|Aspect|TCP|UDP|
|---|---|---|
|Connection|SYN/SYN-ACK/ACK handshake|None|
|Reliability|Acknowledgments and retransmits|None|
|Ordering|Guaranteed|No|
|Message boundaries|No (stream)|Yes|
|Flow control|Window|No|
|Header|20–60 bytes|8 bytes|
|Used by|Web, mail, SSH, databases|DNS, VoIP, games, QUIC|

## TLS 1.2 vs TLS 1.3
|Aspect|TLS 1.2|TLS 1.3|
|---|---|---|
|Handshake|2 RTT|1 RTT (0-RTT on resumption)|
|Key exchange|RSA, DHE, ECDHE|(EC)DHE only|
|Forward secrecy|Optional|Always|
|Ciphers|Dozens, incl. CBC|5, AEAD only|
|Certificate|In plaintext|Encrypted|

## Numbers worth remembering
- Headers: Ethernet **14** + FCS **4**, IPv4 **20**, IPv6 **40**, TCP **20**, UDP **8**, TLS record **5** bytes.
- Ethernet MTU is **1500** bytes → TCP MSS is usually **1460**, max UDP payload without fragmentation — **1472**.
- Default TTL: **64** (Linux, macOS), **128** (Windows), **255** (network gear).
- Ports: ephemeral **49152–65535**, well-known **0–1023**.
- IPv4 Protocol field: ICMP **1**, TCP **6**, UDP **17**.

## Glossary
- **RTT** (Round-Trip Time) — the time for a “there and back” trip between two nodes.
- **MTU** — the maximum packet size a link carries without fragmentation.
- **MSS** — the maximum amount of data in one TCP segment.
- **ISN** — TCP's initial sequence number.
- **NAT** — address translation (usually private to public) on a router.
- **CIDR** — classless addressing with a prefix: `10.0.0.0/8`.
- **CA** — a certificate authority that signs certificates.
- **SNI** — the site name in the ClientHello; the server uses it to pick a certificate.
- **ALPN** — negotiating the protocol on top of TLS (h2 = HTTP/2).
- **AEAD** — encryption with integrity checking (AES-GCM, ChaCha20-Poly1305).
- **PFS** — forward secrecy: old sessions can't be decrypted even with a stolen server key.
- **MITM** — a man-in-the-middle attack.
"""

QUESTIONS = {
    "osi": [
        Q("How many layers does the OSI model have?", ["7", "4", "5", "6"],
          "OSI has seven layers: physical, data link, network, transport, session, presentation, application."),
        Q("At which OSI layer does a switch operate?", ["Data Link (L2)", "Physical (L1)", "Network (L3)", "Transport (L4)"],
          "A switch forwards frames by MAC address using a “MAC → port” table — that's the data link layer."),
        Q("At which layer does a router operate?", ["Network (L3)", "Data Link (L2)", "Transport (L4)", "Application (L7)"],
          "A router chooses the path between networks by IP address — the network layer."),
        Q("What is the data unit (PDU) of TCP called?", ["Segment", "Frame", "Packet", "Bit"],
          "L4 (TCP) — segment, L3 — packet, L2 — frame, L1 — bits. For UDP it's a datagram."),
        Q("What is the data link layer PDU called?", ["Frame", "Packet", "Segment", "Datagram"],
          "At L2 data is wrapped in a frame with MAC addresses in the header and an FCS checksum at the end."),
        Q("What is encapsulation?", ["Each layer adding its header as data goes down the stack",
                                     "Encrypting data at the presentation layer", "Compressing data before sending",
                                     "Splitting a packet into fragments"],
          "When sending, data goes top-down and each layer “wraps” it in its own header."),
        Q("Which OSI layer does HTTP belong to?", ["Application (L7)", "Transport (L4)", "Session (L5)", "Network (L3)"],
          "HTTP is an application protocol used directly by browsers and web servers."),
        Q("Which addresses are used at the data link layer?", ["MAC addresses", "IP addresses", "Port numbers", "Domain names"],
          "A MAC address (48 bits) is the physical address of a network interface, valid within the local segment."),
        Q("What is the presentation layer (L6) responsible for?", ["Data format: encoding, compression, encryption",
                                                                     "Choosing a route", "Sending bits over the cable",
                                                                     "Delivery by port number"],
          "L6 converts data to a form both sides understand: UTF-8, JPEG, ASN.1, encryption."),
        Q("At which layer does a hub operate?", ["Physical (L1)", "Data Link (L2)", "Network (L3)", "Transport (L4)"],
          "A hub simply repeats the electrical signal to all ports — it knows nothing about addresses."),
        Q("At which layer do port numbers appear?", ["Transport (L4)", "Network (L3)", "Data Link (L2)", "Session (L5)"],
          "Ports in the TCP and UDP headers identify which application on the host the data is for."),
        Q("What happens to the headers at the receiving side?",
          ["Each layer reads and strips its header and passes the data up", "New headers are added",
           "The headers are sent back to the sender", "The headers stay all the way to the application"],
          "This is decapsulation: L2 strips Ethernet, L3 strips IP, L4 strips TCP, and the application gets clean data."),
    ],
    "tcpip": [
        Q("How many layers does the classic TCP/IP model (RFC 1122) have?", ["4", "7", "3", "5"],
          "Application, transport, internet and network access."),
        Q("Which OSI layers does the TCP/IP application layer correspond to?", ["5, 6 and 7", "Only 7", "4–7", "6 and 7"],
          "In TCP/IP the session and presentation layers are merged into the application layer."),
        Q("Which protocol translates a domain name into an IP address?", ["DNS", "ARP", "DHCP", "ICMP"],
          "DNS (Domain Name System) answers “what is the IP of example.com?”."),
        Q("Which protocol finds a MAC address for an IP on the local network?", ["ARP", "DNS", "NAT", "ICMP"],
          "ARP broadcasts “Who has 192.168.1.1?” and the owner of the address replies with its MAC."),
        Q("What is the standard HTTPS port?", ["443", "80", "22", "8443"],
          "HTTPS is 443/TCP (and HTTP/3 is 443/UDP). Unencrypted HTTP is 80."),
        Q("What uniquely identifies a TCP connection?", ["Client IP and port + server IP and port",
                                                         "Only the server's IP address", "The MAC addresses of both sides",
                                                         "The TLS session number"],
          "The four values (src IP, src port, dst IP, dst port) are unique for each connection."),
        Q("Which port range does IANA reserve for ephemeral (dynamic) ports?", ["49152–65535", "0–1023", "1024–2048", "8000–9000"],
          "The client OS assigns a temporary port from this range for each outgoing connection."),
        Q("Which protocol does the ping command use?", ["ICMP", "TCP", "UDP", "ARP"],
          "ping sends an ICMP Echo Request and waits for an Echo Reply."),
        Q("What does DHCP do?", ["Automatically assigns the IP address, mask, gateway and DNS", "Encrypts traffic",
                                 "Translates names into addresses", "Finds the best route"],
          "DHCP: Discover → Offer → Request → Ack, over UDP 67/68."),
        Q("What does NAT do on a home router?", ["Replaces private addresses with the router's public address",
                                                 "Encrypts traffic", "Assigns MAC addresses", "Compresses packets"],
          "NAT lets many devices with 192.168.x.x addresses reach the Internet through one public IP."),
        Q("Which layers does a transit router process when forwarding a packet?", ["1–3", "1–2", "1–4", "All 7"],
          "The end-to-end principle: transport and applications exist only on the end hosts."),
    ],
    "ip": [
        Q("How many bits are in an IPv4 address?", ["32", "128", "48", "64"], "4 octets × 8 bits = 32 bits (about 4.3 billion addresses)."),
        Q("How many host addresses are in a /24 network?", ["254", "256", "255", "252"],
          "2^8 = 256 addresses, minus the network address and the broadcast = 254."),
        Q("Which mask corresponds to /26?", ["255.255.255.192", "255.255.255.128", "255.255.255.224", "255.255.192.0"],
          "26 ones: 8+8+8+2 → the last octet is 11000000 = 192."),
        Q("What is the network address of 192.168.1.130/25?", ["192.168.1.128", "192.168.1.0", "192.168.1.129", "192.168.1.255"],
          "/25 → blocks of 128: 0–127 and 128–255. 130 is in the second block → network .128."),
        Q("Which of these addresses is private (RFC 1918)?", ["172.20.5.1", "172.32.0.1", "8.8.8.8", "100.200.1.1"],
          "The private range 172.16.0.0/12 covers 172.16.x.x … 172.31.x.x. 172.32 is already public."),
        Q("What happens when a packet's TTL reaches 0?", ["The packet is discarded and an ICMP Time Exceeded goes to the sender",
                                                          "The packet is returned to the sender", "TTL is reset to 64",
                                                          "The packet is delivered anyway"],
          "That's how IP protects against routing loops. tracert/traceroute is built on the same mechanism."),
        Q("What changes in a packet as it passes through a router (without NAT)?", ["The frame's MAC addresses and the TTL",
                                                                                     "The destination IP", "The source IP",
                                                                                     "The port number"],
          "IP addresses stay the same end to end, while the L2 frame is rebuilt on every hop."),
        Q("How many bits are in an IPv6 address?", ["128", "64", "32", "256"], "128 bits, written as 8 groups of 4 hex digits."),
        Q("What is the IPv4 Protocol field value for TCP?", ["6", "17", "1", "4"], "1 — ICMP, 6 — TCP, 17 — UDP."),
        Q("A computer got the address 169.254.12.7. What does that mean?",
          ["The DHCP server didn't answer, so the OS assigned a link-local address", "It's a public address",
           "It's loopback", "It's multicast"],
          "169.254.0.0/16 (APIPA) signals a DHCP problem: you can't reach the Internet with such an address."),
        Q("Which rule does a router use to choose a route?", ["Longest matching prefix", "The first table entry",
                                                              "The shortest prefix", "Random choice"],
          "Longest prefix match: /24 beats /16, and 0.0.0.0/0 always matches but is chosen last."),
        Q("What is the minimum IPv4 header size?", ["20 bytes", "8 bytes", "40 bytes", "60 bytes"],
          "20 bytes without options (IHL=5). 40 bytes is the fixed IPv6 header."),
    ],
    "udp": [
        Q("What is the size of the UDP header?", ["8 bytes", "20 bytes", "16 bytes", "4 bytes"], "Just 4 fields of 16 bits: ports, length, checksum."),
        Q("What does UDP guarantee?", ["Nothing: no delivery, no ordering, no duplicate protection", "Delivery", "Ordering",
                                       "No duplicates"],
          "UDP is “fire and forget”. If reliability is needed, the application implements it."),
        Q("Which protocol usually uses UDP port 53?", ["DNS", "HTTP", "SSH", "SMTP"], "DNS queries are short; it's easier to retry them than to set up a connection."),
        Q("Why do voice calls (VoIP) use UDP?", ["A late packet is useless — retransmission would only add delay",
                                                  "UDP encrypts voice", "UDP is more reliable than TCP", "UDP has more ports"],
          "Better to lose 20 ms of audio than to wait for a retransmission and get stuttering."),
        Q("An application sent 100 bytes over UDP. What is the Length field?", ["108", "100", "120", "128"],
          "Length = 8 header bytes + 100 data bytes."),
        Q("Does UDP preserve message boundaries?", ["Yes: one sendto() — one datagram — one recvfrom()", "No, it's a byte stream",
                                                    "Only for broadcast", "Only in IPv6"],
          "Unlike TCP, UDP delivers messages whole (or not at all)."),
        Q("Which modern protocol implements reliable delivery on top of UDP?", ["QUIC (the basis of HTTP/3)", "FTP", "SMTP", "Telnet"],
          "QUIC has its own acknowledgments, retransmissions, congestion control and built-in TLS 1.3."),
        Q("Does UDP have a handshake?", ["No", "Yes, three-way", "Yes, two-way", "Only for DNS"],
          "UDP doesn't set up a connection — data can be sent immediately."),
        Q("Is the UDP checksum mandatory in IPv4?", ["No — a value of 0 means “not computed”", "Yes, always",
                                                     "Only for datagrams over 512 bytes", "UDP has no checksum"],
          "It's optional in IPv4 and mandatory in IPv6."),
        Q("Which calls does a UDP server NOT need, unlike TCP?", ["listen() and accept()", "bind()", "socket()", "recvfrom()"],
          "A UDP server only needs socket() → bind() → recvfrom()/sendto()."),
    ],
    "tcp": [
        Q("What is the order of the TCP three-way handshake?", ["SYN → SYN-ACK → ACK", "SYN → ACK → FIN", "ACK → SYN → SYN-ACK",
                                                                "HELLO → ACK → DONE"],
          "Client: SYN, server: SYN-ACK, client: ACK — then both sides are ESTABLISHED."),
        Q("The client sent a SYN with seq=7000. What ack will the SYN-ACK carry?", ["7001", "7000", "7002", "0"],
          "A SYN consumes one sequence number, so ack = ISN + 1."),
        Q("A segment with seq=1500 carries 500 bytes. What ack will the receiver send?", ["2000", "2001", "1501", "1999"],
          "Bytes 1500…1999 were received; the next expected one is 2000."),
        Q("What does the RST flag mean?", ["Immediate connection reset", "Start of a connection", "Graceful close", "Urgent data"],
          "RST tears the connection down without acknowledgments — for example when connecting to a closed port."),
        Q("What is the Window field for?", ["Flow control: how many bytes the receiver can accept",
                                            "The application window number", "Segment lifetime", "Header length"],
          "The sender can't have more unacknowledged data “in flight” than the window size."),
        Q("What happens when a segment is lost?", ["The sender retransmits it after a timeout or 3 duplicate ACKs",
                                                   "The connection is dropped", "The receiver restores it from the checksum",
                                                   "Nothing, the data is lost"],
          "This is TCP's main job — reliable delivery through retransmission."),
        Q("Which state does the side that initiated the close end up in after the final ACK?", ["TIME_WAIT", "CLOSE_WAIT", "LISTEN", "SYN_RCVD"],
          "TIME_WAIT lasts 2×MSL so that late segments don't end up in a new connection with the same ports."),
        Q("Why is the initial sequence number (ISN) chosen randomly?",
          ["Protection against spoofed segments and confusion with old connections", "For encryption", "It's faster", "IPv6 requires it"],
          "A predictable ISN would let an attacker inject forged segments into other people's connections."),
        Q("Does TCP preserve send() boundaries?", ["No — it's a byte stream", "Yes, always", "Only with PSH", "Only with Nagle disabled"],
          "Several send() calls may arrive in one recv() and vice versa. Message boundaries are the application protocol's job."),
        Q("What is the minimum TCP header size?", ["20 bytes", "8 bytes", "32 bytes", "40 bytes"],
          "20 bytes without options (Data Offset = 5), at most 60."),
        Q("Which state is a server in while waiting for incoming connections?", ["LISTEN", "ESTABLISHED", "SYN_SENT", "TIME_WAIT"],
          "After bind() and listen() the socket is in the LISTEN state."),
        Q("What is a “cumulative acknowledgment”?", ["ack=N confirms all bytes up to N−1 inclusive",
                                                     "Every byte is acknowledged separately", "An ACK is sent once per second",
                                                     "Only segments with PSH are acknowledged"],
          "A single ACK can acknowledge many segments at once."),
    ],
    "tls": [
        Q("Which protocol version is the most modern?", ["TLS 1.3", "TLS 1.2", "SSL 3.0", "SSL 4.0"],
          "TLS 1.3 (RFC 8446, 2018). SSL 4.0 doesn't exist."),
        Q("How many RTTs does a full TLS 1.3 handshake take?", ["1", "2", "3", "0"],
          "The client sends its key_share right away, so the keys are ready after the server's first reply. 0-RTT is only for resumption."),
        Q("What does the server certificate provide?", ["Authentication: binding a public key to a domain name",
                                                        "Traffic compression", "A faster connection", "Storage of user passwords"],
          "With its signature, the CA vouches that “this public key belongs to example.com”."),
        Q("What is symmetric encryption used for in TLS?", ["Encrypting the data itself — it's fast",
                                                            "Signing the certificate", "Verifying the CA chain", "DNS"],
          "AES or ChaCha20 encrypt the traffic; asymmetric crypto is only used to agree on a key and verify the server."),
        Q("What is forward secrecy?", ["Stealing the server's long-term key doesn't expose past sessions",
                                       "Encrypting only outgoing data", "Having no certificate", "Exchanging the key in advance"],
          "It comes from an ephemeral exchange (ECDHE): each session's key is destroyed after use."),
        Q("Which key exchange method was removed from TLS 1.3?", ["Static RSA", "ECDHE", "X25519", "key_share"],
          "RSA key exchange provides no forward secrecy, so TLS 1.3 dropped it."),
        Q("What does GCM mean in AES_128_GCM?", ["An AEAD mode: encryption + integrity check", "The key length",
                                                 "A hash function", "The certificate type"],
          "Galois/Counter Mode encrypts and computes an authenticity tag, so any tampering is detected immediately."),
        Q("What does a browser check in a certificate?", ["Signatures up to a trusted CA, the domain name and the validity dates",
                                                          "Only the validity dates", "Only the key length", "The client's IP address"],
          "Plus revocation (OCSP/CRL). Any error — a “Your connection is not private” warning."),
        Q("What does the SNI extension in the ClientHello carry?", ["The name of the site the client is connecting to",
                                                                     "The user's password", "The private key", "The OS version"],
          "One IP can host many sites — the server uses SNI to choose the right certificate."),
        Q("Why is SSL 3.0 prohibited?", ["The POODLE vulnerability and outdated cryptography", "It's too slow", "It's paid",
                                         "It doesn't support IPv6"],
          "POODLE (2014) can decrypt data by exploiting how CBC padding works. RFC 7568 prohibited SSL 3.0."),
        Q("What is sent over the network in a Diffie–Hellman exchange?", ["Only public values (p, g, A, B)", "The shared secret",
                                                                          "The parties' private keys", "A password"],
          "Each side computes the shared secret itself; an eavesdropper sees only the public numbers."),
        Q("Which three goals does TLS achieve?", ["Confidentiality, integrity, authentication", "Speed, compression, caching",
                                                  "Routing, addressing, NAT", "Reliability, ordering, flow control"],
          "Encryption, integrity checking (AEAD) and server authentication (the certificate)."),
    ],
}
