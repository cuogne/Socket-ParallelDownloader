import socket
import threading
import os

DATA_FOLDER = "dataserver"

def handle_client(conn, addr):
    print(f"New connection from {addr}")
    try:
        while True:
            request = conn.recv(1024).decode()
            if not request:
                break
            
            if request.startswith("SIZE"):
                # Handle file size request
                _, file_name = request.strip().split()
                file_path = os.path.join(DATA_FOLDER, file_name)
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    conn.sendall(str(file_size).encode())
                else:
                    conn.sendall(b"ERROR: File not found")

            elif request.startswith("GET"):
                # Handle file chunk request
                try:
                    _, range_info = request.strip().split()
                    file_name, start_byte, chunk_size = range_info.split(':')
                    start_byte = int(start_byte)
                    chunk_size = int(chunk_size)
                    
                    file_path = os.path.join(DATA_FOLDER, file_name)
                    
                    if not os.path.exists(file_path):
                        conn.sendall(b"ERROR: File not found")
                        continue

                    with open(file_path, "rb") as f:
                        f.seek(start_byte)
                        data = f.read(chunk_size)
                        conn.sendall(data)
                except Exception as e:
                    conn.sendall(b"ERROR: Invalid request")
                    print(f"Error processing request from {addr}: {e}")
            else:
                conn.sendall(b"ERROR: Unknown command")
    except Exception as e:
        print(f"Connection error with {addr}: {e}")
    finally:
        conn.close()

def start_server(host='localhost', port=12345):
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"Server running at {host}:{port}")
        
        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    start_server()
