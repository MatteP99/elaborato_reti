import os
import socket as sk
import alive_progress as ab
import time
import traceback


def put_file(addr):
    while True:
        fname = input("Client> ")
        if fname in os.listdir(os.getcwd()):
            break
        else:
            print(f"The file {fname} doesn't exist!\nDigit a valid file name.")
    flen = os.path.getsize('./' + fname)
    sock.sendto(fname.encode(), addr)
    sent = 0
    sequence_num_err = -1
    sequence_num = 0
    chunk_size = 256
    data, server = sock.recvfrom(1024)
    if data == b"start_upload":
        sock.settimeout(5)
        with open(fname, 'rb') as file:
            with ab.alive_bar(manual=True, theme="classic", dual_line=True, title="Upload:", force_tty=True) as bar:
                while byte := file.read(chunk_size):
                    # Dopo 500 chunk inviati a seguito dell'errore resetto la dimensione dei chunk
                    if sequence_num == sequence_num_err + 500 and retransmitted == 0:
                        chunk_size = 256
                        sequence_num_err = -1
                    # Se non ho errori ogni 5 chunk incremento il numero di chunk da inviare
                    if sequence_num_err == -1 and chunk_size < 4050:
                        chunk_size += 1
                    retransmitted = 0
                    sent += len(byte)
                    bar(sent/flen)
                    sock.sendto(f"{sequence_num}::".encode() + byte, server)
                    while True:
                        try:
                            data, server = sock.recvfrom(1024)
                            break
                        except sk.timeout:
                            sequence_num_err = sequence_num
                            if chunk_size > 32:
                                # Dimezzo il numero dei dati da inviare alla prossima iterazione
                                chunk_size /= 2
                                chunk_size = int(chunk_size)
                            retransmitted += 1
                            time.sleep(0.5)
                            sock.sendto(f"{sequence_num}::".encode() + byte, server)
                            print("!RESENDING DATA!")
                            if retransmitted > 20:
                                break
                    if b'Upload of ' + fname.encode() + b' deleted!' in data:
                        sequence_num = -1
                        break
                    sq = int(data.decode())
                    if sq == sequence_num:
                        sequence_num += 1
                    elif sq == sequence_num - 2:
                        sock.sendto(f"{sq}::".encode() + old_data, server)
                        data, server = sock.recvfrom(1024)
                        if int(data.decode()) == sequence_num - 1:
                            sock.sendto(f"{sq}::".encode() + data, server)
                            data, server = sock.recvfrom(1024)
                            if int(data.decode()) == sequence_num:
                                sequence_num += 1
                            else:
                                sequence_num = -1
                                sock.sendto(b'error', server)
                                break
                        else:
                            sequence_num = -1
                            sock.sendto(b'error', server)
                            break
                    else:
                        print(f"Expected:{sequence_num}\nReceived:{data.decode()}")
                        sequence_num = -1
                        sock.sendto(b'error', server)
                        break
                    old_data = byte
        if sequence_num != -1:
            sock.sendto(b'eof', server)
            data, server = sock.recvfrom(1024)
        print(data.decode())
        sock.settimeout(15)


def get_file(res, addr):
    fname = response.split(" ")[0]
    flen = int(response.split(" ")[2])
    recv = 0
    old_sequence_num = 0
    sequence_num = 0
    sock.sendto(b"start_download", addr)
    with open(fname, 'wb') as file:
        with ab.alive_bar(manual=True, theme="classic", title="Download:", force_tty=True, dual_line=True) as bar:
            while True:
                data, server = sock.recvfrom(4096)
                if b"::" in data:
                    if sequence_num > 0:
                        old_sequence_num = sequence_num
                    sequence_num = int(data.split(b"::")[0])
                    data = b"::".join(data.split(b"::")[1:])
                if data == b'eof' or data == b'error':
                    break
                sock.sendto(str(sequence_num).encode(), server)
                if old_sequence_num == sequence_num and sequence_num > 0:
                    continue
                file.write(data)
                recv = recv+len(data)
                bar(recv/flen)
    if data == b'error':
        os.remove(fname)
        sock.sendto(b'download_error', server)
    else:
        sock.sendto(b'successful_download', server)
    data, server = sock.recvfrom(1024)
    print(data.decode())


if __name__ == "__main__":
    sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
    sock.settimeout(15)
    while True:
        try:
            ip = input("IP server (empty => localhost): ")
            if ip == "":
                ip = "localhost"
            server_address = (ip, 10000)
            sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
            sock.sendto(b'try', server_address)
            break
        except Exception as e:
            print("Invalid IP address!")

    try:
        sock.sendto(b'start', server_address)
        dt, server_address = sock.recvfrom(1024)
        print(dt.decode())
        while True:
            t1 = time.time()
            msg = input("Client> ")
            t2 = time.time() - t1
            if t2 > 50:
                raise sk.timeout
            if msg == 'llist':
                strr = "\n\tLocal files:\n"
                for val in [f for f in os.listdir(os.getcwd()) if os.path.isfile(f)]:
                    strr += f"\t{val}\n"
                print(strr)
                continue
            sock.sendto(msg.encode(), server_address)
            dt, server_address = sock.recvfrom(4096)
            response = dt.decode()
            if msg != "list":
                print(f"Server> {response}")
            else:
                print(response)
            if f"{msg} of" in response and "bytes found!" in response:
                get_file(response, server_address)
            if "What is the file name?" in response:
                put_file(server_address)
    except sk.timeout:
        print("\nTimed out!")
    except KeyboardInterrupt:
        print("\nClosing the program...")
    except Exception as info:
        print(f"\nError: {info}\n")
        traceback.print_exc()
    finally:
        print('Closing socket')
        sock.close()
