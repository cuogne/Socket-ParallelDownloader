import socket
import os
import logging

logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')

BUFFER_SIZE = 4096
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000

def server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    logging.info(f"Server started on {SERVER_IP}:{SERVER_PORT}")

    def list_files():
        with open("text.txt", "w") as f:
            for filename in os.listdir("dataServer"):
                filepath = os.path.join("dataServer", filename)
                if os.path.isfile(filepath):
                    filesize = os.path.getsize(filepath)
                    f.write(f"{filename} {filesize}\n")

    while True:
        try:
            data, client_address = server_socket.recvfrom(BUFFER_SIZE)
            request = data.decode().split()

            if request[0] == "list":
                list_files()
                with open("text.txt", "rb") as f:
                    server_socket.sendto(f.read(), client_address)
                    
            elif request[0] == "download":
                filename = request[1]
                start = int(request[2])
                end = int(request[3])
                expected_packet = int(request[4])
                
                filepath = os.path.join("dataServer", filename)
                
                with open(filepath, "rb") as f:
                    f.seek(start)
                    chunk_size = BUFFER_SIZE - 20  # Reserve space for packet number
                    offset = expected_packet * chunk_size
                    
                    if offset < end - start:
                        f.seek(start + offset)
                        chunk = f.read(min(chunk_size, end - (start + offset)))
                        
                        if chunk:
                            packet = f"{expected_packet:010d}|".encode() + chunk
                            server_socket.sendto(packet, client_address)
                            
                            try:
                                server_socket.settimeout(3)
                                ack, _ = server_socket.recvfrom(BUFFER_SIZE)
                                if not ack.decode().strip() == f"ACK {expected_packet}":
                                    logging.warning(f"Invalid ACK from {client_address}")
                            except socket.timeout:
                                logging.warning(f"ACK timeout from {client_address}")
                                
        except Exception as e:
            logging.error(f"Error handling request: {e}")

if __name__ == "__main__":
    if not os.path.exists("dataServer"):
        os.makedirs("dataServer")
    server()