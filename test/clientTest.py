import os
import socket
import threading
import signal
import sys

IP = '127.0.0.1'
PORT = 4466
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf=8"
SERVER_DATA_PATH = 'clientData'

def signal_handler(sig, frame):
    print('\n[CLIENT] Exiting program...')
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    
    while True:
        data = client.recv(SIZE).decode(FORMAT)
        cmd, msg = data.split('@')
    
        if cmd == "DISCONNECTED":
            print(f'{msg}')
            break
        elif cmd == "OK":
            print(f'{msg}')
            
        data = input("> ")
        data = data.split(" ")
        cmd = data[0]
        
        
        if cmd == "LIST":
            client.send(cmd.encode(FORMAT))
        
        elif cmd == "DELETE":
            client.send(f"{cmd}@{data[1]}".encode(FORMAT))
        
        if cmd == 'HELP':
            client.send(cmd.encode(FORMAT))
            
        elif cmd == 'LOGOUT':
            client.send(cmd.encode(FORMAT))
            break
        elif cmd == "UPLOAD":
            # UPLOAD@filename.txt
            path = data[1]
            with open(f'{path}', 'r') as f :
                text = f.read()
                
            ## dataClient/abc.txt => [dataClient, abc.txt]
            filename = path.split("/")[-1]
            send_data = f"{cmd}@{filename}@{text}"
            client.send(send_data.encode(FORMAT))
        
    print("Disconnected from the server.")
    client.close()
            
if __name__ == "__main__":
    main()