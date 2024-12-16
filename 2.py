import socket
import os
import logging

# Debug check log
logging.basicConfig(filename='checklog_client.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

BUFFER_SIZE = 4096
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000
CLIENT_PORT = 5001
TIMEOUT = 5  # Added timeout

def client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind((SERVER_IP, CLIENT_PORT))
    logging.info("Client started.")

    server_address = (SERVER_IP, SERVER_PORT)

    # Receive file list
    client_socket.sendto(b"list", server_address)
    data, _ = client_socket.recvfrom(BUFFER_SIZE * 10)
    with open("text.txt", "wb") as f:
        f.write(data)

    with open("text.txt", "r") as f:
        print("Available files:")
        for line in f:
            print(line.strip())

    input("Press Enter to start download...")

    with open("input.txt", "r") as f:
        for filename in f:
            filename = filename.strip()
            logging.info(f"Starting download of {filename}...")

            filesize = None
            with open("text.txt", "r") as filelist:
                for line in filelist:
                    if filename in line:
                        filesize = int(line.split()[1])
                        break

            if filesize is None:
                logging.error(f"File {filename} not found in the server file list.")
                print(f"File {filename} not found in the server file list.")
                continue

            # Chia tệp thành các phần
            parts = []
            for i in range(4):
                start = i * (filesize // 4)
                end = filesize if i == 3 else (i + 1) * (filesize // 4)
                parts.append((start, end))
                logging.info(f"Downloading {filename} part {i + 1}: start={start}, end={end}")

            temp_files = []
            for i, (start, end) in enumerate(parts):
                temp_filename = f"download/{filename}.part{i+1}"
                temp_files.append(temp_filename)
                
                total_bytes = end - start
                chunk_size = BUFFER_SIZE - 20  # Match server's chunk size
                
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
                        print(f"\rPart {i+1}: {progress:.2f} / 100%", end="")
                    print()

            # Verify file size after combining parts
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

    client_socket.close()

if __name__ == "__main__":
    if not os.path.exists("download"):
        os.makedirs("download")
    client()
