import os
import socket
import threading
import signal
import sys

# Config
RESOURCES_SERVER = 'resources'
TEXT_FILE = 'text.txt'
BUFFER_SIZE = 4096
HOST = socket.gethostbyname(socket.gethostname())
PORT = 9876

init_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
file_lock = threading.Lock()
is_running = True

def signal_handler(signum, frame):
    global is_running
    print("\nShutting down server...")
    is_running = False
    init_server.close()
    sys.exit(0)

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
    resources_dir = os.path.join(os.path.dirname(__file__), RESOURCES_SERVER)
    text_file = os.path.join(os.path.dirname(__file__), TEXT_FILE)
    
    with open(text_file, 'w') as f:
        for file_name in os.listdir(resources_dir):
            file_path = os.path.join(resources_dir, file_name)
            if os.path.isfile(file_path):
                file_size = change_size(os.path.getsize(file_path))
                f.write(f"{file_name} {file_size}\n")

def send_file_chunk(server, filepath, start, end):
    try:
        with open(filepath, 'rb') as f:
            # lock only for seek operation
            with file_lock:
                f.seek(start)
            
            remaining = end - start # kich thuoc chunk can gui
            
            while remaining > 0 and is_running:
                chunk_size = min(BUFFER_SIZE, remaining)
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                server.sendall(chunk)
                remaining -= len(chunk)
                
        return True
    except Exception as e:
        print(f"Error sending file chunk: {e}")
        return False

def handle_client(server, addr):
    client_id = f"{addr[0]}:{addr[1]}" # dia chi IP va cong cua client
    print(f"New connection from {client_id}")
    
    try:
        # gui danh sach file co the down cho client
        with open(TEXT_FILE, 'r') as f:
            server.send(f.read().encode())

        while is_running:
            # nhan request tu client
            request = server.recv(BUFFER_SIZE).decode().strip()
            if not request:
                break

            # request voi format kh co '|' thi no la request yeu cau file_size
            # request = f'{file_name}'.encode()
            if '|' not in request:
                filepath = os.path.join(RESOURCES_SERVER, request)
                if os.path.isfile(filepath):
                    filesize = os.path.getsize(filepath)
                    server.send(str(filesize).encode())
                else:
                    server.send(f"File {request} not found.".encode())
                    print(f"File {request} not found for {client_id}")
                continue

            # request voi format co '|' thi no la request yeu cau tai file va range can down
            # request = f"{file_name}|{start}-{end}".encode()
            parts = request.split('|') # tach lam 2 phan: file_name va range [start, end]
            if len(parts) != 2:
                server.send("Invalid request format.".encode())
                continue

            filename, range_str = parts
            try:
                start, end = map(int, range_str.split('-')) # tach range thanh start va end
            except ValueError:
                server.send("Invalid range format.".encode())
                continue

            filepath = os.path.join(RESOURCES_SERVER, filename)
            if not os.path.isfile(filepath):
                server.send(f"File {filename} not found.".encode())
                continue

            success = send_file_chunk(server, filepath, start, end)
            
            if not success:
                print(f"Error sending file chunk to {client_id}")
                
    except ConnectionResetError:
        print(f"Connection reset by {client_id}")
    except Exception as e:
        print(f"Error handling {client_id}: {e}")
    finally:
        server.close()
        print(f"Connection closed for {client_id}")

def run_server():
    signal.signal(signal.SIGINT, signal_handler)
    
    os.makedirs(RESOURCES_SERVER, exist_ok=True)
    
    # Update file list
    write_text()
    
    try:
        init_server.bind((HOST, PORT)) # dang ky dia chi IP va cong
        init_server.listen(5)
        print(f"Server started on {HOST}:{PORT}")

        while is_running:
            try:
                server, addr = init_server.accept()
                thread = threading.Thread(
                    target=handle_client,
                    args=(server, addr),
                    daemon=True
                )
                thread.start()
            except socket.error as e:
                if is_running:
                    print(f"Socket error: {e}")

    except Exception as e:
        print(f"Server error: {e}")
    finally:
        server.close()

if __name__ == "__main__":
    run_server()