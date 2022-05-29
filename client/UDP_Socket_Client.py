import os
import socket as sk
import time

# Create il socket UDP
sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
sock.settimeout(15)
server_address = ('192.168.178.26', 10000)

try:
    sock.sendto(b'start', server_address)
    data, server = sock.recvfrom(1024)
    print(data.decode())
    while True:
        msg = input("Client> ")
        if msg == 'llist':
            strr = "\n\tLocal files:\n"
            for val in [f for f in os.listdir(os.getcwd()) if os.path.isfile(f)]:
                strr += f"\t{val}\n"
            print(strr)
            continue
        sock.sendto(msg.encode(), server)
        data, server = sock.recvfrom(4096)
        response = data.decode()
        print(response)
        if f"{msg} of" in response and "bytes found!" in response:
            fname = response.split(" ")[0]
            flen = int(response.split(" ")[2])
            recv = 0
            seq = 0
            sock.sendto(b"start_download", server)
            with open(fname, 'wb') as file:
                while True:
                    data, server = sock.recvfrom(1024)
                    if b"::" in data:
                        sq = data.split(b"::")[0]
                        data = b"::".join(data.split(b"::")[1:])
                    if data == b'eof' or data == b'error':
                        break
                    recv = recv+len(data)
                    print(f"Download: {round(recv/flen*100, 2)}%")
                    file.write(data)
                    sock.sendto(str(seq).encode(), server)
                    if int(sq) == seq:
                        seq += 1
            if data == b'error':
                os.remove(fname)
                sock.sendto(b'download_error', server)
            else:
                sock.sendto(b'successful_download', server)
            data, server = sock.recvfrom(1024)
            print(data.decode())
        if "What is the file name?" in response:
            fname = input("Client> ")
            flen = os.path.getsize('./' + fname)
            sock.sendto(fname.encode(), server)
            sent = 0
            seq = 0
            data, server = sock.recvfrom(1024)
            if data == b"start_upload":
                sock.settimeout(5)
                with open(fname, 'rb') as file:
                    while byte := file.read(256):
                        sent += len(byte)
                        print(f"Upload: {round(sent / flen * 100, 2)}%")
                        sock.sendto(f"{seq}::".encode() + byte, server)
                        while True:
                            try:
                                data, server = sock.recvfrom(1024)
                                break
                            except sk.timeout:
                                sock.sendto(f"{seq}::".encode() + byte, server)
                                print("\nRESENDING DATA!\n")
                        if int(data.decode()) == seq:
                            seq += 1
                        else:
                            seq = -1
                            sock.sendto(b'error', server)
                            break
                if seq != -1:
                    sock.sendto(b'eof', server)
                data, server = sock.recvfrom(1024)
                print(data.decode())
                sock.settimeout(15)
except Exception as info:
    print(info)
finally:
    print('closing socket')
    sock.close()
