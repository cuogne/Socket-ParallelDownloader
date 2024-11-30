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
SERVER_DATA_PATH = 'dataServer'

"""
CMD@Msg
"""

def signal_handler(sig, frame):
    print('\n[SERVER] Exiting program...')
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def handle_client(conn, addr):
    print(f'[NEW CONNECTION] {addr} connected.')
    conn.send("Welcome to the File Server.".encode(FORMAT))
    
    while True:
        try:
            data = conn.recv(SIZE).decode(FORMAT)
            data = data.split("@")
            cmd = data[0]
        except ConnectionResetError:
            print(f'[ERROR] Connection reset by peer: {addr}')
            break
        
        if cmd == 'LIST':
            files = os.listdir(SERVER_DATA_PATH)
            send_data = "OK@"

            if len(files) == 0:
                send_data += "The server directory is empty"
            else:
                send_data += "\n".join(f for f in files)
            conn.send(send_data.encode(FORMAT))
        
        elif cmd == "UPLOAD":
            name, text = data[1], data[2]
            filepath = os.path.join(SERVER_DATA_PATH, name)
            with open(filepath, "w") as f:
                f.write(text)

            send_data = "OK@File uploaded successfully."
            conn.send(send_data.encode(FORMAT))
        
        elif cmd == "DELETE":
            files = os.listdir(SERVER_DATA_PATH)
            send_data = "OK@"
            filename = data[1]

            if len(files) == 0:
                send_data += "The server directory is empty"
            else:
                if filename in files:
                    os.system(f"rm {SERVER_DATA_PATH}/{filename}")
                    send_data += "File deleted successfully."
                else:
                    send_data += "File not found."

            conn.send(send_data.encode(FORMAT))
        
        elif cmd == 'HELP':
            send_data = "OK@"
            send_data += "LIST: List all the files from the server. \n"
            send_data += "UPLOAD <path>: UPLOAD a file to the server. \n"
            send_data += "DELETE <filename>: DELETE a file from the server. \n"
            send_data += "LOGOUT: Disconnected from the server.\n"
            send_data += "HELP: List all the commands."
            
            conn.send(send_data.encode(FORMAT))
        
        elif cmd == "LOGOUT":
            break
            
    print(f'[DISCONNECTED] {addr} disconnected.')
        

def main():
    print("[STARTING] Server is starting.")
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # ipv4/tcp
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(ADDR)
    server.listen()
    
    print("[LISTENING] Server is listening.")
    print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
    
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
        
if __name__ == "__main__":
    main()