import os
import socket
import threading
import time

REQUEST_DOWNLOAD_FILE = "input.txt" # file chua danh sach file can download
DOWNLOAD_FOLDER = "data"            # thu muc chua file download
BUFFER_SIZE = 4096                  # kich thuoc buffer nhan du lieu
PORT = 9876                         # port ket noi toi server 

lock = threading.Lock()             # khoa de tranh xung dot du lieu
parts_progress = {}                 # luu tru tien do download cua tung part
downloaded_files = []               # luu tru danh sach cac file da download thanh cong

def create_connection_to_server(HOST, PORT):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(30)
    try:
        client.connect((HOST, PORT))
        return client
    except socket.timeout:
        print(f"Connection timed out. Check server availability.")
        return None
    except Exception as e:
        print(f"Error creating connection: {e}")
        return None

def display_progress_download(parts_progress, file_can_download, downloaded_files, file_name_downloading):
    os.system('cls' if os.name == 'nt' else 'clear')  # clear the screen
    
    print("Available files that client can download:")
    for file_name in file_can_download:
        print(f"[{file_name}]")
        
    print("\nDownloaded files:")
    for file_name in downloaded_files:
        print(f"[{file_name}]")
        
    print(f"\nDownload file {file_name_downloading} - Progress:")
    for part_num in sorted(parts_progress.keys()):
        percent = parts_progress[part_num]
        print(f"Part {part_num} - Progress: {percent:.2f}% / 100%")

# download tung part
def download_part(HOST, PORT, file_name, part_num, start, end, part_size, file_can_download):
    global parts_progress
    client = None
    try:
        client = create_connection_to_server(HOST, PORT)
        if not client:
            return False

        client.recv(BUFFER_SIZE)

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
                with lock:
                    parts_progress[part_num] = percent
                display_progress_download(parts_progress, file_can_download, downloaded_files, file_name)
        return True

    except Exception as e:
        print(f"Error downloading part {part_num}: {e}")
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
def download_file(HOST, PORT, file_name, file_size, file_can_download):
    global parts_progress, downloaded_files
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True) # tao thu muc data neu chua co
    
    threads = []    # luu tru cac thread cua tung part
    parts = []      # luu tru cac part da download
    parts_progress = {}  # reset parts_progress

    # cho toi da 4 ket noi cung luc
    for i in range(4):
        start = i * (file_size // 4)
        end = file_size if i == 3 else (i + 1) * (file_size // 4)
        
        part_size = end - start # tinh kich thuoc cua part
        
        # tao thread cho tung part de xu ly song song
        thread = threading.Thread(target=download_part, args=(HOST, PORT, file_name, i + 1, start, end, part_size, file_can_download))
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
        merged_file_size = os.path.getsize(f"./{DOWNLOAD_FOLDER}/{file_name}") # lay kich thuoc file sau khi merge
        
        # check xem file merged co bang file_size hay khong
        if success and merged_file_size == file_size:
            print(f"Download {file_name} completed successfully!\n")
            print("-" * 40)
            downloaded_files.append(file_name)  # them file_name vao danh sach file da download thanh cong
        else:
            print(f"Download {file_name} errors! Expected:{file_size}, Got:{merged_file_size}\n")
    except FileNotFoundError:
        print(f"Download of {file_name} failed! Merged file not found.")
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
                    print(f"[{file_name}]")
                except ValueError:
                    print(f"Error getting size for {file_name}: {response}")          
        return file_list
    except Exception as e:
        print(f"Error getting file list: {e}")
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

        # download new files 
        for file_name in new_files:
            if file_name in file_can_download:
                file_size = file_can_download[file_name]
                try:
                    input(f"\nPress Enter to download {file_name}...")
                    download_file(HOST, port, file_name, file_size, file_can_download)
                except Exception as e:
                    print(f"[ERROR] Failed to download {file_name}: {e}")
            else:
                print(f"File '{file_name}' not found on server!")

        # update processed files
        return processed_files + new_files

    return processed_files

def main():
    HOST = input("HOST Name: ")

    file_list = get_file_list_can_download(HOST, PORT)
    if not file_list:
        return

    file_can_download = {}
    for file_name, file_size in file_list:
        file_can_download[file_name] = file_size

    processed_files = []
    processed_files = process_input_file(HOST, PORT, file_can_download, processed_files)

    try:
        while True:
            # check new file in input.txt every 5 seconds
            time.sleep(5)
            processed_files = process_input_file(HOST, PORT, file_can_download, processed_files)
    except KeyboardInterrupt:
        print("\nClient terminated...")

if __name__ == "__main__":
    main()