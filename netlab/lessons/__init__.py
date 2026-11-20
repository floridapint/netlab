from . import ip, osi, tcp, tcpip, tls, udp

LESSONS = [osi.LESSON, tcpip.LESSON, ip.LESSON, udp.LESSON, tcp.LESSON, tls.LESSON]
BY_KEY = {lesson.key: lesson for lesson in LESSONS}
