import os
import socket
import threading
import sys
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

REQUEST_DOWNLOAD_FILE = "input.txt"
DOWNLOAD_FOLDER = "data"

# debug check log, you can comment this line to disable log
logging.basicConfig(filename='client_log.log', level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s')

lock = threading.Lock()
last_used_line = 0

# tao ket noi toi server
def create_connection(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(30)  # increased timeout for more reliable connections
    try:
        sock.connect((host, port))
        return sock
    except socket.timeout:
        print(f"Connection timed out. Check server availability.")
        return None
    except Exception as e:
        print(f"Error creating connection: {e}")
        return None

def display_progress(base_line, part_num, percent):
    with lock:
        target_line = base_line + part_num
        sys.stdout.write(f'\033[{target_line}H') # di chuyen con tro den dong target_line
        sys.stdout.write('\033[2K') # xoa dong hien tai
        sys.stdout.write(f"Part {part_num} - Progress: {percent:.2f}% / 100%\r") # hien thi tien trinh
        sys.stdout.flush() 
        time.sleep(0.01) # Consider removing or adjusting sleep time

def download_part(host, port, file_name, part_num, start, end, base_line, part_size):
    sock = None
    try:
        sock = create_connection(host, port)
        if not sock:
            return False

        sock.recv(1024)

        request = f"{file_name}|{start}-{end}".encode() # goi du lieu lai
        sock.sendall(request) # gui request cho server

        part_path = f"./{DOWNLOAD_FOLDER}/{file_name}.part{part_num}"
        with open(part_path, "wb") as f:
            received = 0
            while received < part_size:
                # nhan kich thuoc chunk nho nhat giua 4096 va part_size - received
                chunk_size = min(4096, part_size - received) 
                data = sock.recv(chunk_size)
                if not data:
                    raise ConnectionError(f"Connection lost at {received} bytes")
                f.write(data) # ghi du lieu vao file
                received += len(data) # cap nhat so byte da nhan
                percent = min(received / part_size * 100, 100) # tinh phan tram de hien thi tien trinh
                display_progress(base_line, part_num, percent) # hien thi tien trinh

        return True

    except Exception as e:
        logging.exception(f"Error downloading part {part_num} of {file_name}: {e}")  #Log the exception
        return False
    finally:
        if sock:
            sock.close()

def merge_parts(file_name, parts):
    output_path = f"./{DOWNLOAD_FOLDER}/{file_name}"
    try:
        with open(output_path, "wb") as output_file:
            for part_path in parts:
                with open(part_path, "rb") as part_file:
                    while chunk := part_file.read(8192):
                        output_file.write(chunk)
                os.remove(part_path)
        return True
    except Exception as e:
        logging.exception(f"Error merging parts for {file_name}: {e}") #Log exception
        return False

def download_file(host, port, file_name, file_size):
    global last_used_line
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    part_size = file_size // 4
    futures = []
    parts = []

    base_line = last_used_line + 1
    last_used_line = base_line + 6

    logging.info(f"Starting download of {file_name}...") # check log
    print(f"\033[{base_line}HDownloading {file_name}...\n")

    with ThreadPoolExecutor(max_workers=4) as executor:
        for i in range(4):
            start = i * part_size
            end = start + part_size if i < 3 else file_size
            future = executor.submit(download_part, host, port, file_name, i + 1, start, end, base_line, part_size)
            futures.append(future)

        for i, future in enumerate(as_completed(futures)):
            if not future.result():
                logging.error(f"Failed to download part {i + 1} of {file_name}. Aborting download.")
                return False
            else:
                parts.append(f"./{DOWNLOAD_FOLDER}/{file_name}.part{i + 1}")

    success = merge_parts(file_name, parts)
    try:
        merged_file_size = os.path.getsize(f"./{DOWNLOAD_FOLDER}/{file_name}")
        # check kich thuoc file vua download voi kich thuoc file goc tren server
        if success and merged_file_size == file_size:
            print(f"\033[{base_line + 5}HDownload completed successfully for {file_name}!\n")
            print(f"\033[{base_line + 6}H" + "-" * 40)
        else:
            print(f"\033[{base_line + 5}HDownload of {file_name} completed with errors! Check the files. Size mismatch: Expected {file_size}, Got {merged_file_size if success else 'N/A'}\n")
    except FileNotFoundError:
        print(f"\033[{base_line + 5}HDownload of {file_name} failed! Merged file not found.")
    return success

def get_file_list_from_server(host, port):
    sock = create_connection(host, port)
    if not sock:
        return []  # Return empty list if connection fails

    try:
        file_list_str = sock.recv(4096).decode().strip()
        print("Available files:")
        print(file_list_str)
        return [line.split("|") for line in file_list_str.splitlines() if "|" in line]  # More robust splitting
    except Exception as e:
        print(f"Error getting file list: {e}")
        return []
    finally:
        if sock:
            sock.close()

# check new file in input.txt
def process_input_file(host, port, server_files, processed_files):
    if not os.path.exists(REQUEST_DOWNLOAD_FILE):
        return processed_files

    with open(REQUEST_DOWNLOAD_FILE, "r") as file:
        file_list = file.read().splitlines()

    new_files = []
    check_updated_file = False
    for file_name in file_list:
        if file_name not in processed_files:
            check_updated_file = True
            new_files.append(file_name)

    if new_files:  # if have new file
        if check_updated_file and processed_files:
            print("[UPDATE] Updated file in input.txt:")
            print("\n".join(new_files))

        # download new files
        for file_name in new_files:
            if file_name in server_files:
                file_size = server_files[file_name]
                try:
                    download_file(host, port, file_name, file_size)
                except Exception as e:
                    print(f"[ERROR] Failed to download {file_name}: {e}")
            else:
                print(f"File '{file_name}' not found on server!")

        # update
        return processed_files + new_files

    return processed_files

def main():
    global last_used_line
    host = input("Host Name: ")
    port = 9876

    file_list = get_file_list_from_server(host, port)
    if not file_list:
        return  # Exit if file list retrieval fails

    server_files = {file_name: int(file_size_str) for file_name, file_size_str in file_list}
    last_used_line = len(file_list) + 5

    # track already processed files
    processed_files = []
    processed_files = process_input_file(host, port, server_files, processed_files)

    try:
        while True:
            # check for updates in input.txt every 5 seconds
            time.sleep(5)

            # process the input.txt to check for any new files
            processed_files = process_input_file(host, port, server_files, processed_files)
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting...")

if __name__ == "__main__":
    main()