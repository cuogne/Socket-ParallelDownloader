import os
import socket
import threading

RESOURCES_SERVER = 'resources'
TEXT_FILE = 'text.txt'
BUFFER_SIZE = 4096
FORMAT = 'utf-8'

init_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
init_server.bind((socket.gethostname(), 9876))
init_server.listen(5)
file_lock = threading.Lock()
print(f"Server started at {init_server.getsockname()}")

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
    
    with open(text_file, 'w', encoding=FORMAT) as f:
        for file_name in os.listdir(resources_dir):
            file_path = os.path.join(resources_dir, file_name)
            if os.path.isfile(file_path):
                file_size = change_size(os.path.getsize(file_path))
                f.write(f"{file_name} {file_size}\n")

def handle_client(server, addr):
    try:
        text_file = os.path.join(os.path.dirname(__file__), TEXT_FILE)
        resources_dir = os.path.join(os.path.dirname(__file__), RESOURCES_SERVER)
        
        # gui danh sach file co the down cho client
        with open(text_file, 'r', encoding=FORMAT) as f:
            file_list = f.read()
        server.send(file_list.encode(FORMAT))

        while True:
            # nhan request tu client
            request = server.recv(BUFFER_SIZE).decode(FORMAT).strip()
            if not request:
                break
            
            # request voi format kh co '|' thi no la request yeu cau file_size
            # request = f'{file_name}'.encode(FORMAT)
            if '|' not in request:
                file_path = os.path.join(resources_dir, request)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    server.send(str(file_size).encode(FORMAT)) # gui file_size ve client
                else:
                    server.send(f"File {request} not found.".encode(FORMAT))
                continue

            # request voi format co '|' thi no la request yeu cau tai file va range can down
            # request = f"{file_name}|{start}-{end}".encode(FORMAT)
            parts = request.split('|') # tach lam 2 phan: file_name va range [start, end]
            if len(parts) != 2:
                # sai dinh dang format
                server.send("Invalid request format.".encode(FORMAT))
                continue

            file_name, range_str = parts
            start, end = map(int, range_str.split('-')) # tach range lay start va end
            file_path = os.path.join(resources_dir, file_name)

            if not os.path.isfile(file_path):
                server.send(f"File {file_name} not found.".encode(FORMAT))
                continue

            #Send file chunk
            with file_lock:
                with open(file_path, 'rb') as f:
                    f.seek(start)
                    remaining = end - start # tinh so byte con lai can gui trong range
                    
                    while remaining > 0:
                        chunk_size = min(BUFFER_SIZE, remaining)
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        server.sendall(chunk)
                        remaining -= len(chunk)

    except ConnectionResetError:
        print(f"Connection reset by peer {addr}")
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        server.close()

def run_server():
    write_text() # can comment this
    try:
        while True:
            server, addr = init_server.accept()
            print(f"Connected by {addr}")
            thread = threading.Thread(target=handle_client, args=(server, addr))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("\nServer is shutting down...")
    finally:
        server.close()

if __name__ == "__main__":
    run_server()