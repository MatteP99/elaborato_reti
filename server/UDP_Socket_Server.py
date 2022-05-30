import socket as sk
import os
import threading as td
import time
import traceback


def get_file(skt, address, lock):
    with lock:
        skt.sendto(b"Digit a file name:", address)
    data, address = skt.recvfrom(4096)
    filename = data.decode()
    if filename in os.listdir(os.getcwd()):
        with lock:
            skt.sendto(f"{filename} of {os.path.getsize('./' + filename)} bytes found!".encode(), address)
        data, address = skt.recvfrom(1024)
        skt.settimeout(5)
        if data == b"start_download":
            sequence_num_err = -1
            sequence_num = 0
            chunk_size = 256
            with open(filename, 'rb') as file:
                while byte := file.read(chunk_size):
                    # Dopo 500 chunk inviati a seguito dell'errore resetto la dimensione dei chunk
                    if sequence_num == sequence_num_err + 500 and tries == 0:
                        chunk_size = 256
                        sequence_num_err = -1
                    # Se non ho errori ogni 5 chunk incremento il numero di chunk da inviare
                    if sequence_num_err == -1 and chunk_size < 1000 and (sequence_num % 5) == 0:
                        chunk_size += 5
                    tries = 0
                    with lock:
                        skt.sendto(f"{sequence_num}::".encode() + byte, address)
                    while True:
                        try:
                            data, address = skt.recvfrom(1024)
                            break
                        except sk.timeout:
                            sequence_num_err = sequence_num
                            if chunk_size > 32:
                                chunk_size /= 2
                                chunk_size = int(chunk_size)
                            print(f"\nSocket: {skt.getsockname()}\nPacket lost. resending data!")
                            time.sleep(0.5)
                            with lock:
                                skt.sendto(f"{sequence_num}::".encode() + byte, address)
                            tries += 1
                            if tries > 5:
                                break
                    if int(data.decode()) == sequence_num:
                        sequence_num += 1
                    else:
                        sequence_num = -1
                        with lock:
                            skt.sendto(b'error', address)
                        break
            skt.settimeout(60)
            if sequence_num != -1:
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
    old_seq = 0
    skt.sendto(b'start_upload', address)
    with open(filename, 'wb') as file:
        while True:
            data, address = skt.recvfrom(1024)
            if b"::" in data:
                if seqn > 0:
                    old_seq = seqn
                seqn = int(data.split(b"::")[0])
                data = b"::".join(data.split(b"::")[1:])
            if data == b'eof' or data == b'error':
                break
            file.write(data)
            with lock:
                skt.sendto(str(seqn).encode(), address)
            if seqn != old_seq + 1 and seqn > 0:
                data = b'error'
                break
    if data == b'error':
        os.remove(filename)
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
                strr = "\n\tServer files:\n"
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

            print('\n\rwaiting to receive message...')
            data, address = skt.recvfrom(1024)
            with lock:
                print(f'received {len(data)} bytes from {address}\nSocket: {skt.getsockname()}')
            print(data.decode())
    except sk.timeout:
        print("Timed out!")
    except Exception as info:
        print(f"\nError: {info}\n")
        traceback.print_exc()
    finally:
        with lock:
            print(f"\nClosing socket: {skt.getsockname()}")
            skt.close()


options = b"""
    Type a command:
    list -> Server file explorer
    llist -> Local file explorer
    get -> Download a file
    put -> Upload a file
"""

ip = '192.168.178.26'
sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
server_address = (ip, 10000)
print('\n\rstarting up on %s port %s' % server_address)
sock.bind(server_address)
lck = td.Lock()
clients = 0
try:
    while True:
        dt, addr = sock.recvfrom(1024)
        clients += 1
        print(f'\nhost: {addr} connected\nSocket: {sock.getsockname()}')
        thread = td.Thread(target=handle_host, args=[addr, dt, clients, lck], name=f"Host: {clients}")
        thread.start()
except Exception as err:
    print(err)
except KeyboardInterrupt:
    print("\nClosing program...")
finally:
    print(f"\nClosing socket: {sock.getsockname()}")
    sock.close()
