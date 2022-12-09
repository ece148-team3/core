import socket
import tqdm
import numpy as np
import os
import sys
from io import StringIO

class CLIENT:

    def __init__(self):
        self.SEPARATOR = "<SEPARATOR>"
        self.BUFFER_SIZE = 4096

        self.host = "192.168.113.47"

        self.port = 5001

        self.s = socket.socket()
    
    def send(self, image):
        print(f"[+] Connecting to {self.host}:{self.port}")
        self.s.connect((self.host, self.port))
        print("[+] Connected.")

        if not isinstance(image, np.ndarray):
            print('[+] Not a valid numpy image')
            return
        
        f = StringIO()
        np.savez_compressed(f,frame=image)
        f.seek(0)
        out = f.read()
        self.s.sendall(out)
        self.s.shutdown(1)
        self.s.close()
        print('image sent')
    


        # self.s.send(f"BEV image{self.SEPARATOR}{self.datasize}".encode())

        # # start sending the file
        # progress = tqdm.tqdm(range(self.data), f"Sending BEV image", unit="B", unit_scale=True, unit_divisor=1024)
        # with self.data as f:    
        #     while True:
        #         # read the bytes from the file
        #         bytes_read = f.read(self.BUFFER_SIZE)
        #         if not bytes_read:
        #             # file transmitting is done
        #             break
        #         # we use sendall to assure transimission in 
        #         # busy networks
        #         self.s.sendall(bytes_read)
        #         # update the progress bar
        #         progress.update(len(bytes_read))

    def close(self):
        # close the socket
        self.s.close()