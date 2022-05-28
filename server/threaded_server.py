import os
import socketserver as ss
import time

options = b"""
    Type a command:
    list -> Remote file explorer
    llist -> Local file explorer
    get -> Download a file
    put -> Upload a file
"""


class Handler(ss.BaseRequestHandler):
    def handle(self):
        data = self.request[0]
        while True:
            if data == b'start':
                strr = b"Welcome!\n" + options
                self.request[1].sendto(strr, self.client_address)
            elif data == b'list':
                strr = "\n\tRemote files:\n"
                for val in [f for f in os.listdir(os.getcwd()) if os.path.isfile(f)]:
                    strr += f"\t{val}\n"
                strr += options.decode()
                self.request[1].sendto(strr.encode(), self.client_address)
            elif data == b'get':
                self.get_file()
            elif data == b'put':
                self.put_file()
            else:
                strrr = b'Command not found!\n' + options
                self.request[1].sendto(strrr, self.client_address)

            print('\n\r waiting to receive message...')
            data, _ = self.request[1].recvfrom(1024)
            print(f'received {len(data)} bytes from {self.client_address}\nSocket: {self.request[1].getsockname()}')
            print(data.decode())

    def get_file(self):
        self.request[1].sendto(b"Digit a file name:", self.client_address)
        data, _ = self.request[1].recvfrom(4096)
        filename = data.decode()
        if filename in os.listdir(os.getcwd()):
            self.request[1].sendto(
                f"{filename} of {os.path.getsize('./' + filename)} bytes found!".encode(), self.client_address)
            data, _ = self.request[1].recvfrom(1024)
            if data == b"start_download":
                seqn = 0
                with open(filename, 'rb') as file:
                    while byte := file.read(256):
                        if byte:
                            self.request[1].sendto(byte, self.client_address)
                            data, _ = self.request[1].recvfrom(1024)
                            if int(data.decode()) == seqn:
                                seqn += 1
                            else:
                                self.request[1].sendto(b'error', self.client_address)
                                break
                        else:
                            self.request[1].sendto(b'eof', self.client_address)
                            break
                    file.close()
            data, _ = self.request[1].recvfrom(1024)
            if data == b'successful_download':
                strr = b'\nDownload of ' + filename.encode() + b' completed!\n' + options
                self.request[1].sendto(strr, self.client_address)
            elif data == b"download_error":
                strr = b'\nDownload of ' + filename.encode() + b' deleted!\n' + options
                self.request[1].sendto(strr, self.client_address)
        else:
            strrr = b'Error: file not found!\n' + options
            self.request[1].sendto(strrr, self.client_address)

    def put_file(self):
        self.request[1].sendto(b'What is the file name?', self.client_address)
        data, _ = self.request[1].recvfrom(1024)
        filename = data.decode()
        seqn = 0
        self.request[1].sendto(b'start_upload', self.client_address)
        with open(filename, 'wb') as file:
            while True:
                data, _ = self.request[1].recvfrom(4096)
                self.request[1].sendto(str(seqn).encode(), self.client_address)
                if data == b'eof':
                    break
                if data == b'error':
                    break
                file.write(data)
                seqn += 1
            file.close()
        if data == b'error':
            strr = b'\nUpload of ' + filename.encode() + b' deleted!\n' + options
            self.request[1].sendto(strr, self.client_address)
        else:
            strr = b'\nUpload of ' + filename.encode() + b' completed!\n' + options
            self.request[1].sendto(strr, self.client_address)


with ss.ThreadingUDPServer(('localhost', 10000), Handler) as server:
    server.serve_forever()

