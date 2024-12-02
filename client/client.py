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
    response = client.recv(SIZE).decode(FORMAT)
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

    file_path = os.path.join(CLIENT_DATA_PATH, file_name)
    os.makedirs(CLIENT_DATA_PATH, exist_ok=True)

    with open(file_path, "wb") as file:
        received = 0
        while received < file_size:
            data = client.recv(SIZE)
            file.write(data)
            received += len(data)
            progress = received / file_size * 100
            print(f"[PROGRESS] {progress:.2f}%/100%", end="\r")

    print(f"\n[COMPLETED] {file_name} downloaded successfully.")
    print("------------------------------------------------------------")

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
