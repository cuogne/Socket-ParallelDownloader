import socket
import signal
import sys
import os
import time

IP = '127.0.0.1'
PORT = 4499
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"
REQUEST_FILE = 'input.txt'
CLIENT_DATA_PATH = 'dataClient'

# ctrl + c => terminate
def signal_handler(_, __):
    print("\n[SHUTTING DOWN] Client is shutting down...")
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

# get file from server
def get_file_list(client):
    client.send("GET FILELIST".encode(FORMAT))
    response = b""
    while b"\n" not in response:
        response += client.recv(SIZE)
    response = response.decode(FORMAT).strip()
    print("\n[SERVER FILE LIST]:") # print file on terminal
    print(response) 

# handle downloadFile
def download_file(client, file_name):
    client.send(f"DOWNLOAD {file_name}".encode(FORMAT))

    # receive file size or error message
    response = client.recv(SIZE).decode(FORMAT)
    if response.startswith("[ERROR]"):
        print(response)
        return

    try:
        file_size = int(response)
    except ValueError:
        print("[ERROR] Failed to parse file size.")
        return

    print(f"[DOWNLOADING] {file_name} ({file_size} bytes)")

    # file_path = os.path.join(CLIENT_DATA_PATH, file_name)
    os.makedirs(CLIENT_DATA_PATH, exist_ok=True)
    
    part_size = file_size // 4
    last_part_size = file_size - (part_size * 3)
    
    for i in range(4):
        current_part_size = part_size if i < 3 else last_part_size
            
        with open(f"./{CLIENT_DATA_PATH}/{file_name}.part{i+1}", "wb") as part_file:
            chunk = 0
            while chunk < current_part_size:
                # nhan du lieu toi thieu giua 1024 va so byte con lai
                data = client.recv(min(1024, current_part_size - chunk))
                
                if not data:
                    print(f"Connection lost while downloading part {i+1}")
                    break
                
                part_file.write(data) # ghi du lieu vao file
                chunk += len(data) # tinh so byte da nhan
                progress = min(chunk / current_part_size * 100, 100) # tinh phan tram de hien thi tien trinh
                print(f"Part {i+1} downloaded {progress:.2f}%/100%", end="\r")
                time.sleep(0.1) # delay 0.1s de tai cham
                
            print()
    
    with open(f"./{CLIENT_DATA_PATH}/{file_name}", "wb") as merged_file:
        for i in range(4):
            part_path = f"./{CLIENT_DATA_PATH}/{file_name}.part{i + 1}"
            with open(part_path, "rb") as part_file:
                merged_file.write(part_file.read())
            os.remove(part_path) # xoa cac part tam sau khi tai xong
            
    merged_file_size = os.path.getsize(f"./{CLIENT_DATA_PATH}/{file_name}")
    if merged_file_size == file_size: # check xem file merge lai co bang file goc kh
        print(f"[COMPLETED] {file_name} downloaded successfully.")
    else:
        print("[ERROR] File size mismatch after merging.")

# read and update input.txt each 5s
def process_input_file(client, processed_files):
    if not os.path.exists(REQUEST_FILE):
        return processed_files

    with open(REQUEST_FILE, "r") as file:
        file_list = file.read().splitlines()

    # new_files = [file_name for file_name in file_list if file_name not in processed_files]
    
    # check if new file in input.txt
    new_files = []
    check_updated_file = False
    for file_name in file_list:
        if file_name not in processed_files:
            check_updated_file = True
            new_files.append(file_name)
        
    if new_files: # if have new file
        if check_updated_file and processed_files:
            print("[UPDATE] Updated file in input.txt:")
            print("\n".join(new_files))
        
        # down new file
        for file_name in new_files:
            try:
                download_file(client, file_name)
            except Exception as e:
                print(f"[ERROR] Failed to download {file_name}: {e}")

        # update 
        return processed_files + new_files

    return processed_files

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)

    try:
        welcome_msg = client.recv(SIZE).decode(FORMAT)
        print(f"[SERVER]: {welcome_msg}")

        # display server file list
        get_file_list(client)

        # track already processed files
        processed_files = []
        processed_files = process_input_file(client, processed_files)
        
        while True:
            # check for updates in input.txt every 5 seconds
            time.sleep(5)

            # process the input.txt to check for any new files
            processed_files = process_input_file(client, processed_files)
            
    except Exception as e:
        print(f"[ERROR]: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
