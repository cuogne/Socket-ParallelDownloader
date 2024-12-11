import os
import socket
import threading
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

REQUEST_DOWNLOAD_FILE = "input.txt" # file chua danh sach file can download
DOWNLOAD_FOLDER = "data"            # thu muc chua file download
BUFFER_SIZE = 4096                  # kich thuoc buffer nhan du lieu
PORT = 9876                         # port ket noi toi server

lock = threading.Lock()             # khoa de tranh xung dot
last_used_line_in_terminal = 0      # dong cuoi cung su dung tren terminal

# tao ket noi toi server
def create_connection_to_server(HOST, PORT):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(30)  # increased timeout for more reliable connections
    try:
        client.connect((HOST, PORT))
        return client
    except socket.timeout:
        print(f"Connection timed out. Check server availability.")
        return None
    except Exception as e:
        print(f"Error creating connection: {e}")
        return None

# hien thi tien trinh download
def display_progress_download(base_line, part_num, percent):
    with lock:
        target_line = base_line + part_num
        sys.stdout.write(f'\033[{target_line}H')    # di chuyen con tro den dong target_line
        sys.stdout.write('\033[2K')                 # xoa dong hien tai
        sys.stdout.write(f"Part {part_num} - Progress: {percent:.2f}% / 100%\r") # hien thi tien trinh
        sys.stdout.flush()
        time.sleep(0.01)

# download tung part
def download_part(HOST, PORT, file_name, part_num, start, end, base_line, part_size):
    client = None
    try:
        client = create_connection_to_server(HOST, PORT)
        if not client:
            return False

        client.recv(BUFFER_SIZE) # nhan thong bao tu server

        request = f"{file_name}|{start}-{end}".encode() # goi du lieu lai theo format cho server
        client.sendall(request) # gui request cho server

        part_path = f"./{DOWNLOAD_FOLDER}/{file_name}.part{part_num}"
        with open(part_path, "wb") as f:
            received = 0 # bien luu tru so byte da nhan
            while received < part_size:
                # nhan kich thuoc chunk nho nhat giua BUFFER_SIZE va phan kich thuoc con lai
                chunk_size = min(BUFFER_SIZE, part_size - received) 
                data = client.recv(chunk_size)                          # nhan du lieu
                if not data:
                    raise ConnectionError(f"Connection lost at {received} bytes")
                f.write(data)                                           # ghi du lieu vao file
                received += len(data)                                   # cap nhat so byte da nhan                     
                percent = min(received / part_size * 100, 100)          # tinh phan tram de hien thi tien trinh
                display_progress_download(base_line, part_num, percent) # hien thi tien trinh
        return True

    except Exception as e:
        return False
    finally:
        if client:
            client.close()

# gop cac part lai thanh file hoan chinh
def merge_parts(file_name, parts):
    output_path = f"./{DOWNLOAD_FOLDER}/{file_name}"
    try:
        with open(output_path, "wb") as output_file:
            for part_path in parts:
                with open(part_path, "rb") as part_file:
                    while chunk := part_file.read(BUFFER_SIZE):
                        output_file.write(chunk)
                os.remove(part_path)
        return True
    except Exception as e:
        return False

# download file
def download_file(HOST, PORT, file_name, file_size):
    global last_used_line_in_terminal
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True) # tao thu muc data neu chua co
    # part_size = file_size // 4
    futures = []    # luu tru cac future cua tung part
    parts = []      # luu tru cac part da download

    base_line = last_used_line_in_terminal + 1 # tinh toan dong bat dau hien thi tien trinh download tren terminal
    last_used_line_in_terminal = base_line + 6 # cap nhat dong cuoi cung su dung tren terminal

    print(f"\033[{base_line}HDownloading {file_name}...\n")

    # cho toi da 4 ket noi cung luc
    with ThreadPoolExecutor(max_workers=4) as executor:
        for i in range(4):
            start = i * (file_size // 4)
            end = file_size if i == 3 else (i + 1) * (file_size // 4)
            
            part_size = end - start # tinh kich thuoc cua part
            
            # tao future cho tung part de xu ly song song
            future = executor.submit(download_part, HOST, PORT, file_name, i + 1, start, end, base_line, part_size)
            futures.append(future) # luu tru future

        # kiem tra ket qua download cua tung part xem co thanh cong hay khong
        for i, future in enumerate(as_completed(futures)):
            if not future.result():
                return False
            else:
                parts.append(f"./{DOWNLOAD_FOLDER}/{file_name}.part{i + 1}")

    success = merge_parts(file_name, parts)
    try:
        merged_file_size = os.path.getsize(f"./{DOWNLOAD_FOLDER}/{file_name}") # lay kich thuoc file sau khi gop
        # check kich thuoc file vua download voi kich thuoc file goc tren server
        if success and merged_file_size == file_size:
            print(f"\033[{base_line + 5}HDownload {file_name} completed successfully!\n")
            print(f"\033[{base_line + 6}H" + "-" * 40)
        else:
            print(f"\033[{base_line + 5}HDownload {file_name} errors! Expected:{file_size}, Got:{merged_file_size}\n")
    except FileNotFoundError:
        print(f"\033[{base_line + 5}HDownload of {file_name} failed! Merged file not found.")
    return success

# lay danh sach file co the download
def get_file_list_can_download(HOST, PORT):
    client = create_connection_to_server(HOST, PORT)
    if not client:
        return []  # Return empty list if connection fails

    try:
        file_list_str = client.recv(BUFFER_SIZE).decode().strip()
        file_list = []
        
        # hien thi file co the download tren terminal phia client
        print("Available files that client can download:")
        for line in file_list_str.splitlines():
            if "|" in line:
                file_name, file_size = line.split("|")
                file_list.append((file_name, file_size)) # ghi du lieu vao file_list
                print(f"{file_name} - {file_size} bytes")
        return file_list
    
    except Exception as e:
        print(f"Error getting file list: {e}")
        return []
    finally:
        if client:
            client.close()

# check new file in input.txt
def process_input_file(HOST, port, server_files, processed_files):
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
            print("\n".join(new_files))

        # download new files
        for file_name in new_files:
            if file_name in server_files:
                file_size = server_files[file_name]
                try:
                    download_file(HOST, port, file_name, file_size)
                except Exception as e:
                    print(f"[ERROR] Failed to download {file_name}: {e}")
            else:
                print(f"File '{file_name}' not found on server!")

        # update
        return processed_files + new_files

    return processed_files

def main():
    global last_used_line_in_terminal
    HOST = input("HOST Name: ")

    file_list = get_file_list_can_download(HOST, PORT)
    if not file_list:
        return  # Exit if file list retrieval fails

    server_files = {file_name: int(file_size_str) for file_name, file_size_str in file_list}
    last_used_line_in_terminal = len(file_list) + 5

    # track already processed files
    processed_files = []
    processed_files = process_input_file(HOST, PORT, server_files, processed_files)

    try:
        while True:
            # check for updates in input.txt every 5 seconds
            time.sleep(5)
            processed_files = process_input_file(HOST, PORT, server_files, processed_files)
    except KeyboardInterrupt:
        print("\nClient terminated...")

if __name__ == "__main__":
    main()