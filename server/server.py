import os
import socket
import threading

SERVER_DATA_PATH = 'resources'
TEXT_FILE = 'text.txt'
BUFFER_SIZE = 4096

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((socket.gethostname(), 9876))
server.listen(5)
file_lock = threading.Lock()
print(f"Server started at {server.getsockname()}")

def change_size(size):
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(size)
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    return f"{size:.3f}{units[unit_index]}"

# doc danh sach file trong thu muc resources va ghi vao file text.txt
# ham nay chi ghi tu dong cho file text.txt de kh phai nhap thu cong (co the comment lai)
def write_text():
    resources_dir = os.path.join(os.path.dirname(__file__), SERVER_DATA_PATH)
    text_file = os.path.join(os.path.dirname(__file__), TEXT_FILE)
    
    with open(text_file, 'w') as f:
        for file_name in os.listdir(resources_dir):
            file_path = os.path.join(resources_dir, file_name)
            if os.path.isfile(file_path):
                file_size = change_size(os.path.getsize(file_path))
                f.write(f"{file_name} {file_size}\n")

def handle_client(client_sock, addr):
    try:
        text_file = os.path.join(os.path.dirname(__file__), TEXT_FILE)
        resources_dir = os.path.join(os.path.dirname(__file__), SERVER_DATA_PATH)
        
        # gui danh sach file co the down cho client
        with open(text_file, 'r') as f:
            file_list = f.read()
        client_sock.send(file_list.encode())

        while True:
            # nhan request tu client
            request = client_sock.recv(BUFFER_SIZE).decode().strip()
            if not request:
                break

            # Handle file size request (when no '|' in request)
            if '|' not in request:
                file_path = os.path.join(resources_dir, request)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    client_sock.send(str(file_size).encode())
                else:
                    client_sock.send(f"File {request} not found.".encode())
                continue

            # Handle download request (format: filename|start-end)
            parts = request.split('|')
            if len(parts) != 2:
                client_sock.send("Invalid request format.".encode())
                continue

            file_name, range_str = parts
            start, end = map(int, range_str.split('-'))
            file_path = os.path.join(resources_dir, file_name)

            if not os.path.isfile(file_path):
                client_sock.send(f"File {file_name} not found.".encode())
                continue

            #Send file chunk
            with file_lock:
                with open(file_path, 'rb') as f:
                    f.seek(start)
                    remaining = end - start
                    
                    while remaining > 0:
                        chunk_size = min(BUFFER_SIZE, remaining)
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        client_sock.sendall(chunk)
                        remaining -= len(chunk)

    except ConnectionResetError:
        print(f"Connection reset by peer {addr}")
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        client_sock.close()

def run():
    write_text()
    try:
        while True:
            client_sock, addr = server.accept()
            print(f"Connected by {addr}")
            thread = threading.Thread(target=handle_client, args=(client_sock, addr))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("\nServer is shutting down...")
    finally:
        server.close()

if __name__ == "__main__":
    run()