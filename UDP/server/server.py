import socket
import os
import logging
import signal
import hashlib

logging.basicConfig(filename='checklog_server.log', level=logging.INFO,
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

def run_server():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
            server_socket.bind((SERVER_IP, SERVER_PORT))
            print(f"Server started on {SERVER_IP}:{SERVER_PORT}")

            # Handle Ctrl+C
            def signal_handler(sig, frame):
                print("Shutting down server...")
                raise KeyboardInterrupt

            signal.signal(signal.SIGINT, signal_handler)

            while True:
                try:
                    data, client_address = server_socket.recvfrom(BUFFER_SIZE)
                    request = data.decode().split()
                    
                    # request lay danh sach file co the tai ve
                    if request[0] == "get_file_list":
                        with open("text.txt", "rb") as f:
                            server_socket.sendto(f.read(), client_address)

                    # request lay kich thuoc file
                    elif request[0] == "filesize":
                        filename = request[1]
                        filepath = os.path.join("dataServer", filename)
                        if os.path.isfile(filepath):
                            filesize = os.path.getsize(filepath)
                            server_socket.sendto(str(filesize).encode(), client_address)
                        else:
                            server_socket.sendto(b"File not found", client_address)

                    # request lay checksum cua file
                    elif request[0] == "checksum":
                        filename = request[1]
                        filepath = os.path.join("dataServer", filename)
                        if os.path.isfile(filepath):
                            checksum = calculate_checksum(filepath)
                            server_socket.sendto(checksum.encode(), client_address)
                        else:
                            server_socket.sendto(b"File not found", client_address)

                    # request download file
                    elif request[0] == "download":
                        filename = request[1]
                        start = int(request[2])
                        end = int(request[3])
                        
                        # so thu tu packet ma client mong muon nhan
                        expected_packet = int(request[4])
                        
                        # filepath cua file can download
                        filepath = os.path.join("dataServer", filename)

                        with open(filepath, "rb") as f:
                            chunk_size = BUFFER_SIZE - 20  # reserve space for packet number
                            offset = expected_packet * chunk_size

                            while True:
                                try:
                                    if offset < end - start:
                                        f.seek(start + offset)
                                        chunk = f.read(min(chunk_size, end - (start + offset)))
                                        if chunk:
                                            # server gui packet cho client, kem theo so thu tu packet
                                            packet = f"{expected_packet:010d}|".encode() + chunk
                                            server_socket.sendto(packet, client_address)

                                            server_socket.settimeout(3)
                                            
                                            # server nhan ACK tu client
                                            ack, _ = server_socket.recvfrom(BUFFER_SIZE)
                                            
                                            # kiem tra ACK co dung so thu tu packet mong muon khong
                                            if ack.decode().strip() == f"ACK {expected_packet}":
                                                logging.info(f"Received valid ACK {expected_packet} from {client_address}")
                                                break
                                            else:
                                                print(f"Error ACK {ack.decode()}, expected ACK {expected_packet}. Retrying...")
                                                logging.warning(f"Error ACK from {client_address}, expected {expected_packet}. Retrying...")
                                    else:
                                        break

                                except socket.timeout:
                                    logging.warning(f"ACK timeout for packet {expected_packet} from {client_address}. Retrying...")

                except Exception as e:
                    logging.error(f"Error handling request: {e}")

    except KeyboardInterrupt:
        print("Server stopped.")
    except Exception as e:
        logging.error(f"Server encountered an error: {e}")

if __name__ == "__main__":
    if not os.path.exists("dataServer"):
        os.makedirs("dataServer")
    get_list_files()
    run_server()