import socket
import os
import logging
import time
import signal

# Debug check log
logging.basicConfig(filename='checklog_client.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

BUFFER_SIZE = 4096
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000
CLIENT_PORT = 5001
TIMEOUT = 5  # Added timeout

def start_client_socket():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind((SERVER_IP, CLIENT_PORT))
    logging.info("Client started.")
    return client_socket

def receive_file_list(client_socket, server_address):
    client_socket.sendto(b"list", server_address)
    data, _ = client_socket.recvfrom(BUFFER_SIZE * 10)
    with open("text.txt", "wb") as f:
        f.write(data)

def display_available_files():
    with open("text.txt", "r") as f:
        print("Available files:")
        for line in f:
            print(line.strip())

def get_filesize(filename):
    with open("text.txt", "r") as filelist:
        for line in filelist:
            if filename in line:
                return int(line.split()[1])
    return None

def download_file_part(client_socket, server_address, filename, part, start, end):
    temp_filename = f"download/{filename}.part{part+1}"
    total_bytes = end - start

    with open(temp_filename, "wb") as outfile:
        received_bytes = 0
        expected_packet = 0

        while received_bytes < total_bytes:
            try:
                request = f"download {filename} {start} {end} {expected_packet}"
                client_socket.sendto(request.encode(), server_address)

                data, _ = client_socket.recvfrom(BUFFER_SIZE)
                packet_num, chunk = data.split(b"|", 1)
                packet_num = int(packet_num.decode())

                if packet_num == expected_packet:
                    outfile.write(chunk)
                    received_bytes += len(chunk)
                    client_socket.sendto(f"ACK {packet_num}".encode(), server_address)
                    expected_packet += 1
                else:
                    print(f"Out of order packet: got {packet_num}, expected {expected_packet}")

            except socket.timeout:
                print(f"Timeout waiting for packet {expected_packet}")
                continue

            progress = min(100, received_bytes * 100 / total_bytes)
            print(f"\rPart {part+1}: {progress:.2f} / 100%", end="")
        print()

    return temp_filename

def combine_file_parts(filename, temp_files, filesize):
    final_path = f"download/{filename}"
    with open(final_path, "wb") as outfile:
        bytes_written = 0
        for temp_file in temp_files:
            with open(temp_file, "rb") as infile:
                while chunk := infile.read(BUFFER_SIZE):
                    outfile.write(chunk)
                    bytes_written += len(chunk)
            os.remove(temp_file)

    if bytes_written != filesize:
        print(f"Error: File size mismatch. Expected {filesize}, got {bytes_written}")
    else:
        print(f"Successfully downloaded {filename}")

def client():
    client_socket = start_client_socket()
    server_address = (SERVER_IP, SERVER_PORT)

    receive_file_list(client_socket, server_address)
    display_available_files()

    downloaded_files = set()

    try:
        while True:
            with open("input.txt", "r") as f:
                for filename in f:
                    filename = filename.strip()
                    if filename in downloaded_files:
                        continue

                    logging.info(f"Starting download of {filename}...")

                    filesize = get_filesize(filename)
                    if filesize is None:
                        logging.error(f"File {filename} not found in the server file list.")
                        print(f"File {filename} not found in the server file list.")
                        continue
                    
                    input("Press Enter to continue...")
                    
                    parts = [(i * (filesize // 4), filesize if i == 3 else (i + 1) * (filesize // 4)) for i in range(4)]
                    temp_files = []
                    for i, (start, end) in enumerate(parts):
                        temp_file = download_file_part(client_socket, server_address, filename, i, start, end)
                        temp_files.append(temp_file)

                    combine_file_parts(filename, temp_files, filesize)
                    downloaded_files.add(filename)

            time.sleep(5)
    except KeyboardInterrupt:
        print("\nClient interrupted. Exiting...")
        logging.info("Client interrupted by user.")
    finally:
        client_socket.close()

if __name__ == "__main__":
    if not os.path.exists("download"):
        os.makedirs("download")
    client()
