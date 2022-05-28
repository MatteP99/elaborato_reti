import os
import socket as sk
import time

# Create il socket UDP
sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)

server_address = ('localhost', 10000)

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
        if "found" in response and msg in response:
            fname = response.split(" ")[0]
            flen = int(response.split(" ")[2])
            recv = 0
            seq = 0
            sock.sendto(b"start_download", server)
            with open(fname, 'wb') as file:
                while True:
                    data, server = sock.recvfrom(1024)
                    recv = recv+len(data)
                    print(f"Download: {round(recv/flen*100, 2)}%")
                    if data == b'eof':
                        break
                    elif data == b'error':
                        break
                    file.write(data)
                    sock.sendto(str(seq).encode(), server)
                    seq += 1
                file.close()
                if data == b'error':
                    os.remove(fname)
                    sock.sendto(b'download_error', server)
                else:
                    sock.sendto(b'successful_download', server)
                data, server = sock.recvfrom(1024)
                print(data.decode())
        if "What is the file name?" in response:
            fname = input("File name: ")
            flen = os.path.getsize('./' + fname)
            sock.sendto(fname.encode(), server)
            sent = 0
            seq = 0
            data, server = sock.recvfrom(1024)
            if data == b"start_upload":
                with open(fname, 'rb') as file:
                    while byte := file.read(256):
                        sent += len(byte)
                        print(f"Upload: {round(sent / flen * 100, 2)}%")
                        sock.sendto(byte, server)
                        data, server = sock.recvfrom(1024)
                        if int(data.decode()) == seq:
                            seq += 1
                        else:
                            sock.sendto(b'error', server)
                            break
                    file.close()
                    sock.sendto(b'eof', server)
                data, server = sock.recvfrom(1024)
                print(data.decode())
except Exception as info:
    print(info)
finally:
    print('closing socket')
    sock.close()
