import socket as sk
import os
import time
import threading as td


def get_file(skt, address, lock):
    with lock:
        skt.sendto(b"Digit a file name:", address)
    data, address = skt.recvfrom(4096)
    filename = data.decode()
    if filename in os.listdir(os.getcwd()):
        with lock:
            skt.sendto(f"{filename} of {os.path.getsize('./' + filename)} bytes found!".encode(), address)
        data, address = skt.recvfrom(1024)
        if data == b"start_download":
            seq = 0
            with open(filename, 'rb') as file:
                while byte := file.read(256):
                    with lock:
                        skt.sendto(byte, address)
                    data, address = skt.recvfrom(1024)
                    if int(data.decode()) == seq:
                        seq += 1
                    else:
                        with lock:
                            skt.sendto(b'error', address)
                        break
                file.close()
                with lock:
                    skt.sendto(b'eof', address)
        data, address = skt.recvfrom(1024)
        if data == b'successful_download':
            strr = b'\nDownload of ' + filename.encode() + b' completed!\n' + options
            with lock:
                skt.sendto(strr, address)
        elif data == b"download_error":
            strr = b'\nDownload of ' + filename.encode() + b' deleted!\n' + options
            with lock:
                skt.sendto(strr, address)
    else:
        strrr = b'Error: file not found!\n' + options
        with lock:
            skt.sendto(strrr, address)


def put_file(skt, address, lock):
    with lock:
        skt.sendto(b'What is the file name?', address)
    data, address = skt.recvfrom(1024)
    filename = data.decode()
    seqn = 0
    skt.sendto(b'start_upload', address)
    with open(filename, 'wb') as file:
        while True:
            data, address = skt.recvfrom(4096)
            sq, data = data.split(":")
            if data == b'eof':
                break
            if data == b'error':
                break
            file.write(data)
            with lock:
                skt.sendto(str(seqn).encode(), address)
            if sq == seqn:
                seqn += 1
            else:
                data = b'error'
                break;
        file.close()
    if data == b'error':
        strr = b'\nUpload of ' + filename.encode() + b' deleted!\n' + options
        with lock:
            skt.sendto(strr, address)
    else:
        strr = b'\nUpload of ' + filename.encode() + b' completed!\n' + options
        with lock:
            skt.sendto(strr, address)


def handle_host(address, data, clnum, lock):
    with lock:
        skt = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
        skt.bind((ip, 10000 + clnum))
        skt.settimeout(60)
    try:
        while True:
            if data == b'start':
                strr = b"Welcome!\n" + options
                with lock:
                    skt.sendto(strr, address)
            elif data == b'list':
                strr = "\n\tFiles:\n"
                for val in [f for f in os.listdir(os.getcwd()) if os.path.isfile(f)]:
                    strr += f"\t{val}\n"
                strr += options.decode()
                with lock:
                    skt.sendto(strr.encode(), address)
            elif data == b'get':
                get_file(skt, address, lock)
            elif data == b'put':
                put_file(skt, address, lock)
            else:
                strrr = b'Command not found!\n' + options
                with lock:
                    skt.sendto(strrr, address)

            print('\n\r waiting to receive message...')
            data, address = skt.recvfrom(1024)
            with lock:
                print(f'received {len(data)} bytes from {address}\nSocket: {skt.getsockname()}')
            print(data.decode())
    except Exception as er:
        print(er)
    finally:
        with lock:
            print(f"Closing socket: {skt.getsockname()}")
            skt.close()


options = b"""
    Type a command:
    list -> Remote file explorer
    llist -> Local file explorer
    get -> Download a file
    put -> Upload a file
"""

ip = '192.168.178.26'
sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
server_address = (ip, 10000)
print('\n\r starting up on %s port %s' % server_address)
sock.bind(server_address)
lck = td.Lock()
clients = 0
try:
    while True:
        dt, addr = sock.recvfrom(1024)
        clients += 1
        print(f'host: {addr} connected\nSocket: {sock.getsockname()}')
        thread = td.Thread(target=handle_host, args=[addr, dt, clients, lck], name=f"Host: {clients}")
        thread.start()
except Exception as err:
    print(err)
finally:
    print(f"Closing socket: {sock.getsockname()}")
    sock.close()
