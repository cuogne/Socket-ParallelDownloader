import socket
import os
import logging
import signal
import sys
import hashlib

logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')

BUFFER_SIZE = 4096
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000

def change_size(size):
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(size)
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    return f"{size:.3f}{units[unit_index]}"

def calculate_checksum(filepath):
    md5_hash = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()

def get_list_files():
    with open("text.txt", "w") as f:
        for filename in os.listdir("dataServer"):
            filepath = os.path.join("dataServer", filename)
            if os.path.isfile(filepath):
                filesize = change_size(os.path.getsize(filepath))
                f.write(f"{filename} {filesize}\n")

def server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    logging.info(f"Server started on {SERVER_IP}:{SERVER_PORT}")

    def signal_handler(sig, frame):
        logging.info("Shutting down server...")
        server_socket.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    while True:
        try:
            data, client_address = server_socket.recvfrom(BUFFER_SIZE)
            request = data.decode().split()

            if request[0] == "get_file_list":
                with open("text.txt", "rb") as f:
                    server_socket.sendto(f.read(), client_address)
                    
            elif request[0] == "filesize":
                filename = request[1]
                filepath = os.path.join("dataServer", filename)
                if os.path.isfile(filepath):
                    filesize = os.path.getsize(filepath)
                    server_socket.sendto(str(filesize).encode(), client_address)
                else:
                    server_socket.sendto(b"File not found", client_address)
                    
            elif request[0] == "checksum":
                filename = request[1]
                filepath = os.path.join("dataServer", filename)
                if os.path.isfile(filepath):
                    checksum = calculate_checksum(filepath)
                    server_socket.sendto(checksum.encode(), client_address)
                else:
                    server_socket.sendto(b"File not found", client_address)
                    
            elif request[0] == "download":
                filename = request[1]
                start = int(request[2])
                end = int(request[3])
                
                # Client gửi expected_packet trong request
                expected_packet = int(request[4])
                
                filepath = os.path.join("dataServer", filename)
                
                with open(filepath, "rb") as f:
                    f.seek(start)
                    chunk_size = BUFFER_SIZE - 20  # Reserve space for packet number
                    offset = expected_packet * chunk_size
                    
                    # Đọc từ file và gửi cho client
                    if offset < end - start:
                        f.seek(start + offset)
                        chunk = f.read(min(chunk_size, end - (start + offset)))
                        
                        if chunk:
                            # Server đánh số packet khi gửi
                            packet = f"{expected_packet:010d}|".encode() + chunk
                            server_socket.sendto(packet, client_address)
                            
                            try:
                                server_socket.settimeout(3) # Set timeout 3s
                                ack, _ = server_socket.recvfrom(BUFFER_SIZE)
                                
                                # kiem tra ACK co dung so thu tu khong
                                if not ack.decode().strip() == f"ACK {expected_packet}":
                                    logging.warning(f"Invalid ACK from {client_address}")
                                    # Server sẽ gửi lại khi client request lại gói tin này
                            except socket.timeout:
                                logging.warning(f"ACK timeout from {client_address}")
                                
        except Exception as e:
            logging.error(f"Error handling request: {e}")

if __name__ == "__main__":
    get_list_files() # create file list
    server()