import socket
import threading
import signal
import sys
import os

IP = '127.0.0.1'
PORT = 4499
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"
SERVER_DATA_PATH = 'dataServer'
TEXT_FILE = 'text.txt'

# ctrl + c => terminate
def signal_handler(_, __):
    print("\n[SHUTTING DOWN] Server is shutting down...")
    server.close()
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

#change size of file B, KB, MB
def change_size(size):
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024 or unit == "GB":
            return f"{size:.0f}{unit}"
        size /= 1024
        
def handle_client(conn, addr):
    # create new connection
    print(f'[NEW CONNECTION] {addr} connected.')
    conn.send("Welcome to the Server.".encode(FORMAT))
    connected = True
    
    while connected:
        try:
            msg = conn.recv(SIZE).decode(FORMAT)
            if not msg:
                break

            if msg == "DISCONNECT":
                connected = False
            elif msg == "GET FILELIST":
                # send the file list from the server, including content from text.txt
                files = []
                try:
                    # read file text.txt
                    with open(TEXT_FILE, "r") as file:
                        file_content = file.read()
                        files.append(f"File that Client can Download:\n{file_content}")
                except FileNotFoundError:
                    files.append(f"[ERROR] {TEXT_FILE} not found.")
                
                # send file for client
                file_list = "\n".join(files)
                conn.send(file_list.encode(FORMAT))
                
            elif msg.startswith("DOWNLOAD"):
                # handle file download request
                file_name = msg.split(" ", 1)[1]
                file_path = os.path.join(SERVER_DATA_PATH, file_name)

                if not os.path.exists(file_path) or not os.path.isfile(file_path):
                    conn.send(f"[ERROR] File '{file_name}' not found.".encode(FORMAT))
                else:
                    file_size = os.path.getsize(file_path)
                    conn.send(str(file_size).encode(FORMAT))

                    with open(file_path, "rb") as file:
                        while chunk := file.read(SIZE):
                            conn.send(chunk)
                            
            else:
                conn.send(f"[SERVER] Unknown command: {msg}".encode(FORMAT))
            
            print(f"[{addr}] {msg}")
            
        except ConnectionResetError:
            print(f"[DISCONNECTED] {addr} forcibly closed the connection.")
            break
        
    print(f"[DISCONNECTED] {addr} disconnected.")
    conn.close()
    
def main():
    global server
    print("[STARTING] Server is starting.")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(ADDR)
    server.listen()
    
    print("[LISTENING] Server is listening.")
    
    while True:
        try:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
        except KeyboardInterrupt:
            print("\n[SHUTTING DOWN] Server is shutting down...")
            break
        
    server.close()

if __name__ == "__main__":
    main()
