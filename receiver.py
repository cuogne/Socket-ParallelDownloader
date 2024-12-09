import os
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

lock = threading.Lock()
progress = [""] * 4

def create_connection(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((host, port))
    return sock

def download_part(host, port, part_num, start, end, file_name):
    sock = None
    try:
        sock = create_connection(host, port)
        sock.recv(1024)
        
       # goi format request cho server
        request = f"{start}-{end}".encode() # 12893-25786
        # print(f"Requesting part {part_num} with range: {start}-{end}")
        sock.send(request) # gui cho server de biet phan can down
        
        with open(f"./data/{file_name}.part{part_num}", "wb") as f:
            received = 0 # luu so byte da nhan
            part_size = end - start # kich thuoc part can down
            
            while received < part_size:
                chunk_size = min(4096, part_size - received)
                data = sock.recv(chunk_size)
                
                if not data:
                    raise ConnectionError(f"Connection lost at {received} bytes")
                    
                f.write(data) # ghi du lieu vao file
                received += len(data) # tang so byte da nhan
                
                # tinh toan tien do
                progress_percent = min(received / part_size * 100, 100)
                with lock:
                    progress[part_num-1] = f"Part {part_num} - Progress: {progress_percent:.2f}%/100%"
                    os.system('clear')
                    for p in progress:
                        print(p)
                    time.sleep(0.01)  # delay         
        return True
        
    except Exception as e:
        print(f"\nError downloading part {part_num}: {e}")
        return False
        
    finally:
        if sock:
            sock.close()

def download_file(host, port):
    sock = create_connection(host, port)
    infofile = sock.recv(4096).decode().strip() # nhan infofile gom file_name|file_size
    sock.close()
    
    # print(f"Received file info: {infofile}")
    file_name, file_size = infofile.split("|") #tach
    file_size = int(file_size)
    
    os.makedirs("./data", exist_ok=True) # tao thu muc data
    
    part_size = file_size // 4
    futures = []
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        for i in range(4):
            start = i * part_size
            end = start + part_size if i < 3 else file_size
            
            future = executor.submit(download_part,host, port, i+1, start, end, file_name)
            futures.append(future)
            
       # cho tat ca download xong
        failed_parts = []
        for i, future in enumerate(as_completed(futures)):
            if not future.result():
                failed_parts.append(i+1)
                
    if failed_parts:
        print(f"\nFailed to download parts: {failed_parts}")
        return
        
    # gop file
    print("\nMerging file parts...")
    try:
        with open(f"./data/{file_name}", "wb") as merged_file:
            total_size = 0
            for i in range(4):
                part_path = f"./data/{file_name}.part{i+1}"
                with open(part_path, "rb") as part_file:
                    while True:
                        chunk = part_file.read(8192)
                        if not chunk:
                            break
                        merged_file.write(chunk)
                        total_size += len(chunk)
                os.remove(part_path) # xoa file part sau khi gop
                
        if total_size == file_size: # check lai kich thuoc
            print(f"\nDownload completed successfully!")
        else:
            print(f"\nSize mismatch! Expected: {file_size}, Got: {total_size}")
            
    except Exception as e:
        print(f"\nError merging files: {e}")

def main():
    host = input("Host Name: ")
    port = 9876
    download_file(host, port)

if __name__ == "__main__":
    main()
