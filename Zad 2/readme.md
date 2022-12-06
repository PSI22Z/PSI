# Zad 2.2
Po zmianie wielkości bufora serwera na liczbę mniejszą niż wiadomość, która jest wysyłana przez klienta, 
serwer traktuje pojedynczą wiadomość od klienta jako wiele wiadomości co powoduje każdorazowe wysyłanie odebranych danych do klienta czyli błędne działanie 
programu: 
```
# Server - C client - python

Client connected at IP: 172.19.0.4 and port: 51886
Message from client: Hello TC
Message from client: P Server
Message from client: Hello TC
Message from client: P Server
Message from client: Hello TC
Message from client: P Server
reading stream message: Connection reset by peer
Can't send
```    
Z racji, że protokół TCP jest zorientowany na strumień a nie na
wiadomość, nadawca nie wie ile bajtów każdorazowo odczyta odbiorca. Aby 
umożliwić poprawne działanie programu należy w jakiś sposób powiadomić 
odbiorcę jakiej wielkości wiadomości może się spodziewać. Dzięki temu 
odbiorca niezależnie ile bajtów czyta za każdym razem, jest w stanie 
odebrać wiadomość jako całość. W naszym przypadku zostało to 
zrealizowane przy pomocy wysłania przed rozpoczęciem strumieniowania właściwej wiadomości
strumienia 4 bajtów informującego o długości wiadomości. Po 
modyfikacji zarówno klienta jak i serwera, program działa poprawnie:

```
# Server - C

Client connected at IP: 172.19.0.4 and port: 38850
receiving message of length 16:
Message from client: Hello TCP Server
receiving message of length 16:
Message from client: Hello TCP Server
receiving message of length 16:
Message from client: Hello TCP Server
Ending connection
```

```
# Server - Python 
Connection from: ('172.19.0.4', 59598)
receiving message of length 16: 
from connected user: Hello TCP Server
receiving message of length 16: 
from connected user: Hello TCP Server
receiving message of length 16: 
from connected user: Hello TCP Server
Waiting for data
```