import os
import socket
import threading
import sys
import time
import logging

# Configure logging
logging.basicConfig(filename='client.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

REQUEST_DOWNLOAD_FILE = "input.txt" # file chua danh sach file can download
DOWNLOAD_FOLDER = "data"            # thu muc chua file download
BUFFER_SIZE = 4096                  # kich thuoc buffer nhan du lieu
PORT = 9876                         # port ket noi toi server                 

lock = threading.Lock()             # khoa de tranh xung dot
last_used_line_in_terminal = 0      # dong cuoi cung su dung tren terminal

# tao ket noi toi server
def create_connection_to_server(HOST, PORT):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(30)
    try:
        client.connect((HOST, PORT))
        logging.info(f"Connected to server {HOST}:{PORT}")
        return client
    except socket.timeout:
        logging.error(f"Connection timed out. Check server availability.")
        return None
    except Exception as e:
        logging.error(f"Error creating connection: {e}")
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
            logging.info(f"Successfully received part {part_num} of {file_name} - [{start}-{end}]") 
        return True

    except Exception as e:
        logging.error(f"Error downloading part {part_num}: {e}")
        return False
    finally:
        if client:
            client.close()
            logging.info(f"Connection closed for part {part_num}")

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
        logging.info(f"Successfully merged parts into {file_name}")
        return True
    except Exception as e:
        logging.error(f"Error merging parts for {file_name}: {e}")
        return False

# download file
def download_file(HOST, PORT, file_name, file_size):
    global last_used_line_in_terminal
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True) # tao thu muc data neu chua co
    
    threads = []    # luu tru cac thread cua tung part
    parts = []      # luu tru cac part da download

    base_line = last_used_line_in_terminal + 1 # tinh toan dong bat dau hien thi tien trinh download tren terminal
    last_used_line_in_terminal = base_line + 6 # cap nhat dong cuoi cung su dung tren terminal

    print(f"\033[{base_line}HDownloading {file_name}...\n")

    # cho toi da 4 ket noi cung luc
    for i in range(4):
        start = i * (file_size // 4)
        end = file_size if i == 3 else (i + 1) * (file_size // 4)
        
        part_size = end - start # tinh kich thuoc cua part
        
        # tao thread cho tung part de xu ly song song
        thread = threading.Thread(target=download_part, args=(HOST, PORT, file_name, i + 1, start, end, base_line, part_size))
        threads.append(thread) # luu tru thread
        thread.start()

    # doi cac thread ket thuc
    for thread in threads:
        thread.join()

    # kiem tra ket qua download cua tung part xem co thanh cong hay khong
    for i in range(4):
        part_path = f"./{DOWNLOAD_FOLDER}/{file_name}.part{i + 1}"
        if not os.path.exists(part_path):
            return False
        parts.append(part_path)

    success = merge_parts(file_name, parts)
    try:
        merged_file_size = os.path.getsize(f"./{DOWNLOAD_FOLDER}/{file_name}") # lay kich thuoc file sau khi gop
        # check kich thuoc file vua download voi kich thuoc file goc tren server
        if success and merged_file_size == file_size:
            print(f"\033[{base_line + 5}HDownload {file_name} completed successfully!\n")
            logging.info(f"Download {file_name} completed successfully!")
            
            print(f"\033[{base_line + 6}H" + "-" * 40)
        else:
            print(f"\033[{base_line + 5}HDownload {file_name} errors! Expected:{file_size}, Got:{merged_file_size}\n")
            logging.error(f"Download {file_name} errors! Expected:{file_size}, Got:{merged_file_size}")
            
    except FileNotFoundError:
        print(f"\033[{base_line + 5}HDownload of {file_name} failed! Merged file not found.")
        logging.error(f"Download of {file_name} failed! Merged file not found.")
        
    return success

def get_file_list_can_download(HOST, PORT):
    client = create_connection_to_server(HOST, PORT)
    if not client:
        return []

    try:
       # nhan danh sach file tu server
        file_list_str = client.recv(BUFFER_SIZE).decode().strip()
        file_list = []
        
        print("Available files that client can download:")
        for line in file_list_str.splitlines():
            if " " in line:
                file_name = line.split(" ")[0] # lay ten file
                
                # gui request file size cho server de lay kich thuoc goc
                request = f'{file_name}'.encode()
                client.sendall(request)
                
                # nhan response tu server (chua file_size cua file_name yeu cau)
                response = client.recv(BUFFER_SIZE).decode().strip()
                
                try:
                    file_size = int(response)
                    file_list.append((file_name, file_size))
                    print(f"[{file_name}] - {file_size} bytes")
                    
                except ValueError:
                    logging.error(f"Error getting size for {file_name}: {response}")
                    print(f"Error getting size for {file_name}: {response}")
                              
        return file_list
    except Exception as e:
        logging.error(f"Error getting file list: {e}")
        return []
    finally:
        if client:
            client.close()

# check new file in input.txt
def process_input_file(HOST, port, file_can_download, processed_files):
    if not os.path.exists(REQUEST_DOWNLOAD_FILE):
        return processed_files

    with open(REQUEST_DOWNLOAD_FILE, "r") as file:
        # don't use set() because it sorts the list => not in order in input.txt
        file_list = []
        for line in file:
            filename = line.strip()
            # neu filename chua co trong file_list thi them vao
            # => tranh truong hop file bi trung lap trong input.txt
            if filename and filename not in file_list:
                file_list.append(filename)

    new_files = []
    check_updated_file = False
    for file_name in file_list:
        if file_name not in processed_files:
            check_updated_file = True
            new_files.append(file_name)

    if new_files:  # if have new file
        if check_updated_file and processed_files:
            print(f"\nNew files found in input.txt: {new_files}")
            logging.info(f"New files found in input.txt: {new_files}") 

        # download new files 
        for file_name in new_files:
            if file_name in file_can_download:
                file_size = file_can_download[file_name]
                try:
                    input(f"\nPress Enter to download {file_name}...")
                    download_file(HOST, port, file_name, file_size, file_can_download)
                except Exception as e:
                    logging.error(f"[ERROR] Failed to download {file_name}: {e}")
                    print(f"[ERROR] Failed to download {file_name}: {e}")
            else:
                logging.error(f"File '{file_name}' not found on server!")
                print(f"File '{file_name}' not found on server!")

        # update processed files
        return processed_files + new_files

    return processed_files

def main():
    global last_used_line_in_terminal
    
    os.system('cls' if os.name == 'nt' else 'clear') # clear terminal while starting
    HOST = input("HOST Name: ")

    file_list = get_file_list_can_download(HOST, PORT)
    if not file_list:
        return  # Exit if file list retrieval fails

    file_can_download = {} # create a dictionary to store file_name and file_size
    
    for file_name, file_size in file_list:
        file_can_download[file_name] = file_size
        
    last_used_line_in_terminal = len(file_list) + 5

    # track already processed files
    processed_files = []
    processed_files = process_input_file(HOST, PORT, file_can_download, processed_files)

    try:
        while True:
            # check for updates in input.txt every 5 seconds
            time.sleep(5)
            processed_files = process_input_file(HOST, PORT, file_can_download, processed_files)
    except KeyboardInterrupt:
        logging.info("Client terminated...")
        print("\nClient terminated...")

if __name__ == "__main__":
    main()