import socket
import os
import logging
import signal
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BUFFER_SIZE = 4096
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000

# Global variable for the server socket
server_socket = None

def list_files():
    with open("text.txt", "w") as f:
        for filename in os.listdir("dataServer"):
            filepath = os.path.join("dataServer", filename)
            filesize = os.path.getsize(filepath)
            f.write(f"{filename} {filesize}\n")

def handle_list_request(server_socket, client_address):
    list_files()
    with open("text.txt", "rb") as f:
        server_socket.sendto(f.read(), client_address)

def handle_download_request(server_socket, client_address, request):
    try:
        filename = request[1]
        start = int(request[2])
        end = int(request[3])
        expected_packet = int(request[4])

        filepath = os.path.join("dataServer", filename)

        with open(filepath, "rb") as f:
            f.seek(start)
            total_bytes = end - start
            chunk_size = BUFFER_SIZE - 20  # Reserve space for packet number and delimiter

            offset = expected_packet * chunk_size
            if offset < total_bytes:
                # Only read if we haven't reached end
                f.seek(start + offset)
                chunk = f.read(min(chunk_size, total_bytes - offset))

                if chunk:  # Only send if we have data
                    packet = f"{expected_packet:010d}|".encode() + chunk
                    server_socket.sendto(packet, client_address)

                    # Wait for ACK
                    server_socket.settimeout(3)  # Set a short timeout for ACK
                    try:
                        ack_data, _ = server_socket.recvfrom(BUFFER_SIZE)
                        ack = ack_data.decode().strip()
                        if not ack == f"ACK {expected_packet}":
                            logging.warning(f"Invalid ACK: {ack}")
                    except socket.timeout:
                        logging.warning(f"ACK timeout for packet {expected_packet}")
                    finally:
                        server_socket.settimeout(None)  # Reset timeout
    except Exception as e:
        logging.error(f"Error during download request: {e}")

def signal_handler(sig, frame):
    logging.info("Server shutting down.")
    if server_socket:
        server_socket.close()
    sys.exit(0)

def server():
    global server_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))

    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    logging.info(f"Server started. Listening on {SERVER_IP}:{SERVER_PORT}")

    while True:
        try:
            # Wait for a request from a client
            data, client_address = server_socket.recvfrom(BUFFER_SIZE)
            request = data.decode().split()

            if request[0] == "list":
                handle_list_request(server_socket, client_address)
            elif request[0] == "download":
                handle_download_request(server_socket, client_address, request)
        except Exception as e:
            logging.error(f"Error processing request: {e}")

if __name__ == "__main__":
    server()
