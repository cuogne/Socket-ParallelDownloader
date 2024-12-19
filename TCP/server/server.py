import os
import socket
import threading
import signal
import sys
import logging

# Config
RESOURCES_SERVER = 'resources'
TEXT_FILE = 'text.txt'
BUFFER_SIZE = 4096
HOST = socket.gethostbyname(socket.gethostname())
PORT = 9876

init_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
file_lock = threading.Lock()
is_running = True

# Setup logging
logging.basicConfig(filename='server.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def signal_handler(signum, frame):
    global is_running
    print("\nShutting down server...")
    logging.info("Shutting down server...")
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
            with file_lock:
                f.seek(start)
            
            remaining = end - start
            
            while remaining > 0 and is_running:
                chunk_size = min(BUFFER_SIZE, remaining)
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                server.sendall(chunk)
                remaining -= len(chunk)
                
        logging.info(f"Successfully sent {os.path.basename(filepath)} chunk to {server.getpeername()}")
        return True
    except Exception as e:
        logging.error(f"Error sending file chunk: {e}")
        return False

def handle_client(server, addr):
    client_id = f"{addr[0]}:{addr[1]}"
    print(f"New connection from {client_id}")
    logging.info(f"New connection from {client_id}")
    
    try:
        with open(TEXT_FILE, 'r') as f:
            server.send(f.read().encode())

        while is_running:
            request = server.recv(BUFFER_SIZE).decode().strip()
            if not request:
                break

            if '|' not in request:
                filepath = os.path.join(RESOURCES_SERVER, request)
                if os.path.isfile(filepath):
                    filesize = os.path.getsize(filepath)
                    server.send(str(filesize).encode())
                    logging.info(f"Sent filesize for {request} to {client_id}")
                else:
                    server.send(f"File {request} not found.".encode())
                    print(f"File {request} not found for {client_id}")
                    logging.warning(f"File {request} not found for {client_id}")
                continue

            parts = request.split('|')
            if len(parts) != 2:
                server.send("Invalid request format.".encode())
                continue

            filename, range_str = parts
            try:
                start, end = map(int, range_str.split('-'))
            except ValueError:
                server.send("Invalid range format.".encode())
                continue

            filepath = os.path.join(RESOURCES_SERVER, filename)
            if not os.path.isfile(filepath):
                server.send(f"File {filename} not found.".encode())
                continue

            logging.info(f"Sending {filename} [{start}-{end}] to {client_id}")
            success = send_file_chunk(server, filepath, start, end)
            
            if not success:
                print(f"Error sending file chunk to {client_id}")
                logging.error(f"Error sending file chunk to {client_id}")
                
    except ConnectionResetError:
        print(f"Connection reset by {client_id}")
        logging.warning(f"Connection reset by {client_id}")
    except Exception as e:
        print(f"Error handling {client_id}: {e}")
        logging.error(f"Error handling {client_id}: {e}")
    finally:
        server.close()
        print(f"Connection closed for {client_id}")
        logging.info(f"Connection closed for {client_id}")

def run_server():
    signal.signal(signal.SIGINT, signal_handler)
    
    os.makedirs(RESOURCES_SERVER, exist_ok=True)
    
    write_text()
    
    try:
        init_server.bind((HOST, PORT))
        init_server.listen(5)
        print(f"Server started on {HOST}:{PORT}")
        logging.info(f"Server started on {HOST}:{PORT}")

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
                    logging.error(f"Socket error: {e}")

    except Exception as e:
        print(f"Server error: {e}")
        logging.error(f"Server error: {e}")
    finally:
        server.close()
        logging.info("Server stopped")

if __name__ == "__main__":
    run_server()