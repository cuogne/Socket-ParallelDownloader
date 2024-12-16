import socket
import os
import logging
import time
import threading

logging.basicConfig(filename='checklog_client.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

BUFFER_SIZE = 4096
HEADER_SIZE = 20  # Size for packet number
CHUNK_SIZE = BUFFER_SIZE - HEADER_SIZE
SERVER_IP = "127.0.0.1" 
SERVER_PORT = 5000
TIMEOUT = 5
MAX_RETRIES = 3

lock = threading.Lock()
parts_progress = {}
downloaded_files = set()

def create_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((SERVER_IP, 0))  # Random port
    sock.settimeout(TIMEOUT)
    return sock

def display_progress(filename):
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"\nDownloading {filename}...")
    print("Available files:")
    
    with open("text.txt", "r") as f:
        for line in f:
            print(line.strip())
            
    print("\nDownloaded files:")
    for file in downloaded_files:
        print(file)
                
    print(f"\nDownload progress for {filename}:")
    for part in sorted(parts_progress.keys()):
        print(f"Part {part+1}: {parts_progress[part]:.2f} / 100%")
        
def download_part(filename, part_num, start, end, server_address):
    sock = create_socket()
    temp_filename = f"download/{filename}.part{part_num+1}"
    total_bytes = end - start
    
    with open(temp_filename, "wb") as outfile:
        received_bytes = 0
        expected_packet = 0
        retries = 0
        
        # Initialize progress for this part
        with lock:
            parts_progress[part_num] = 0
            display_progress(filename)
        
        while received_bytes < total_bytes and retries < MAX_RETRIES:
            try:
                # gui request voi expected_packet
                request = f"download {filename} {start} {end} {expected_packet}"
                sock.sendto(request.encode(), server_address)
                
                data, _ = sock.recvfrom(BUFFER_SIZE)
                
                # Nhan packet tu server
                packet_num, chunk = data.split(b"|", 1)
                packet_num = int(packet_num.decode())
                
                # Kiem tra so thu tu packet
                if packet_num == expected_packet:
                    outfile.write(chunk)                                      # Ghi du lieu vao file
                    received_bytes += len(chunk)                              # Tang so byte nhan duoc
                    
                    sock.sendto(f"ACK {packet_num}".encode(), server_address) # Gui ACK cho server
                    expected_packet += 1                                      # Tang so thu tu packet
                    retries = 0                                               # Reset retry counter
                    
                    # Update progress atomically
                    with lock:
                        parts_progress[part_num] = (received_bytes * 100) / total_bytes
                        display_progress(filename)
                else:
                    logging.warning(f"Out of order packet: got {packet_num}, expected {expected_packet}")
                    retries += 1
                    
            except socket.timeout:
                logging.warning(f"Timeout waiting for packet {expected_packet} for part {part_num+1}")
                retries += 1
                continue
            except Exception as e:
                logging.error(f"Error downloading part {part_num+1}: {e}")
                retries += 1
                
    sock.close()
    return temp_filename

def combine_parts(filename, temp_files, filesize):
    output_path = f"download/{filename}"
    with open(output_path, "wb") as outfile:
        bytes_written = 0
        for temp_file in temp_files:
            with open(temp_file, "rb") as infile:
                while chunk := infile.read(CHUNK_SIZE):
                    outfile.write(chunk)
                    bytes_written += len(chunk)
            os.remove(temp_file)
            
    if bytes_written != filesize:
        raise Exception(f"File size mismatch. Expected {filesize}, got {bytes_written}")

def client():
    server_address = (SERVER_IP, SERVER_PORT)
    
    # Get file list
    sock = create_socket()
    sock.sendto(b"list", server_address)
    data, _ = sock.recvfrom(BUFFER_SIZE * 10)
    with open("text.txt", "wb") as f:
        f.write(data)
    sock.close()
    
    display_progress("")
    
    try:
        while True:
            with open("input.txt", "r") as f:
                for filename in f:
                    filename = filename.strip()
                    if filename in downloaded_files:
                        continue
                        
                    # Get file size
                    filesize = None
                    with open("text.txt", "r") as filelist:
                        for line in filelist:
                            if filename in line:
                                filesize = int(line.split()[1])
                                break
                                
                    if filesize is None:
                        logging.error(f"File {filename} not found")
                        continue
                        
                    logging.info(f"Starting download of {filename}")
                    parts_progress.clear()
                    threads = []
                    temp_files = []
                    
                    # Initialize progress for all parts
                    for i in range(4):
                        parts_progress[i] = 0
                    
                    # Start download threads simultaneously
                    for i in range(4):
                        start = i * (filesize // 4)
                        end = filesize if i == 3 else (i + 1) * (filesize // 4)
                        thread = threading.Thread(
                            target=download_part,
                            args=(filename, i, start, end, server_address),
                            daemon=True  # Set as daemon thread
                        )
                        threads.append(thread)
                        temp_files.append(f"download/{filename}.part{i+1}")
                    
                    # Start all threads at once
                    for thread in threads:
                        thread.start()
                        
                    # Wait for all parts
                    for thread in threads:
                        thread.join()
                        
                    # Combine parts
                    try:
                        combine_parts(filename, temp_files, filesize)
                        downloaded_files.add(filename)
                        print(f"\nDownload completed for {filename}")
                    except Exception as e:
                        logging.error(f"Error combining parts: {e}")
                        
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\nExiting...")
        
if __name__ == "__main__":
    if not os.path.exists("download"):
        os.makedirs("download")
    client()