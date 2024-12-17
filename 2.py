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
parts_progress = {}                 # tao dict de luu trang thai download cua tung part
downloaded_files = set()            # tao set de luu trang thai download cua tung file
file_list_can_download = {}         # tao dict de luu cac file co the download

def create_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((SERVER_IP, 0))
    sock.settimeout(TIMEOUT)
    return sock

def display_progress(filename):
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # hien thi cac file co the download len client
    print("\nAvailable files can download:")
    for fname, fsize in file_list_can_download.items():
        print(f"{fname} ({fsize} bytes)")

    # hien thi cac file da download
    if downloaded_files:
        print("\nDownloaded files:")
        for file in downloaded_files:
            print(file)
    
    # hien thi progress download cua tung part cua filename            
    if filename:
        print(f"\nDownload progress for {filename}:")
        for part in sorted(parts_progress.keys()):
            print(f"Part {part+1}: {parts_progress[part]:.2f}% / 100%")

def download_part(filename, part_num, start, end, server_address):
    sock = create_socket()
    temp_filename = f"download/{filename}.part{part_num+1}"
    total_bytes = end - start
    
    with open(temp_filename, "wb") as outfile:
        received_bytes = 0          # so byte nhan duoc
        expected_packet = 0         # so packet duoc gui tu server
        retries = 0                 # so lan gui lai khi timeout
        
        with lock:
            parts_progress[part_num] = 0
            display_progress(filename)
        
        while received_bytes < total_bytes and retries < MAX_RETRIES:
            try:
                # gui request download part tu start den end qua server
                request = f"download {filename} {start} {end} {expected_packet}"
                sock.sendto(request.encode(), server_address)
                
                data, _ = sock.recvfrom(BUFFER_SIZE)
                packet_num, chunk = data.split(b"|", 1)                        # tach packet number va chunk
                packet_num = int(packet_num.decode())                          # chuyen packet number tu byte sang int
                
                if packet_num == expected_packet:                              # kiem tra so thu tu packet
                    outfile.write(chunk)                                       # ghi chunk vao file
                    received_bytes += len(chunk)                               # tinh so byte nhan duoc
                    sock.sendto(f"ACK {packet_num}".encode(), server_address)  # gui ACK cho server
                    expected_packet += 1                                       # tang so thu tu packet
                    retries = 0
                    
                    with lock:
                        # cap nhat progress download cua part
                        parts_progress[part_num] = min(100, (received_bytes / total_bytes) * 100)
                        display_progress(filename)
                        
                else:
                    # log khi nhan packet khong dung thu tu
                    logging.warning(f"Out of order packet: got {packet_num}, expected {expected_packet}")
                    retries += 1
                    
            except socket.timeout:
                # log khi timeout
                logging.warning(f"Timeout waiting for packet {expected_packet} for part {part_num+1}")
                retries += 1
                
            except Exception as e:
                # log khi co loi xay ra
                logging.error(f"Error downloading part {part_num+1}: {e}")
                retries += 1
                
                if retries >= MAX_RETRIES:
                    break
                
    sock.close()
    return temp_filename

def merge_file_part(filename, temp_files, filesize):
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
    
    # nhan file list tu server chua cac file co the download
    sock = create_socket()
    sock.sendto(b"get_file_list", server_address)
    data, _ = sock.recvfrom(BUFFER_SIZE * 10)
    
    # tao dict file_list_can_download de luu file va filesize 
    for line in data.decode().split('\n'):
        if line.strip():
            filename, _  = line.split()
            
            # gui request filesize cho server de lay kich thuoc go
            sock.sendto(f"filesize {filename}".encode(), server_address)
            data, _ = sock.recvfrom(BUFFER_SIZE)
            
            filesize = int(data.decode()) # ep kieu cho file size tu byte sang int
            file_list_can_download[filename] = filesize        
    
    sock.close()
    
    display_progress("")
    
    try:
        while True:
            with open("input.txt", "r") as f:
                for filename in f:
                    filename = filename.strip() # xoa khoang trang o dau va cuoi chuoi
                    
                    if filename in downloaded_files:
                        continue # bo qua file da download
                        
                    filesize = file_list_can_download.get(filename) # lay filesize tu dict file_list_can_download
                    
                    if not filesize:
                        logging.error(f"File {filename} not found")
                        continue

                    logging.info(f"Starting download of {filename}")
                    
                    input("Press Enter to start downloading...") # nhan Enter de bat dau download    
                    
                    parts_progress.clear()
                    threads = []
                    temp_files = []
                    
                    for i in range(4):
                        parts_progress[i] = 0
                        start = i * (filesize // 4)
                        end = filesize if i == 3 else (i + 1) * (filesize // 4)
                        
                        logging.info(f"Downloading part {i+1} of {filename} from {start} to {end}")
                        
                        thread = threading.Thread(
                            target=download_part,
                            args=(filename, i, start, end, server_address),
                            daemon=True
                        )
                        threads.append(thread)
                        temp_files.append(f"download/{filename}.part{i+1}")
                    
                    [t.start() for t in threads]
                    [t.join() for t in threads]
                        
                    try:
                        merge_file_part(filename, temp_files, filesize)
                        downloaded_files.add(filename)
                        print(f"\nDownload completed for {filename}")
                    except Exception as e:
                        print(f"Error combining parts: {e}")
                        logging.error(f"Error combining parts: {e}")
                        
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\nExiting...")
        
if __name__ == "__main__":
    if not os.path.exists("download"):
        os.makedirs("download")
    client()