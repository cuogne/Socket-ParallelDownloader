import os
import socket
import threading
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

lock = threading.Lock()
progress = [""] * 4

def create_connection(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((host, port))
    return sock

def init_progress_display(file_name):
    """Initialize the progress display"""
    print(f"Downloading {file_name}...")
    # Print initial progress lines
    for i in range(4):
        sys.stdout.write(f"Part {i+1} - Progress: 0.00%/100%\n")
    # Move cursor up to first progress line
    sys.stdout.write('\033[4A')
    sys.stdout.flush()

def update_progress(part_num, progress_percent):
    """Update progress for a specific part"""
    with lock:
        # Calculate lines to move down (account for header line)
        lines_down = part_num
        # Move cursor to correct line
        sys.stdout.write(f'\033[{lines_down}B')
        # Clear entire line
        sys.stdout.write('\033[2K')
        # Move to start of line and write progress
        sys.stdout.write(f"\rPart {part_num} - Progress: {progress_percent:.2f}%/100%")
        # Move cursor back to original position
        sys.stdout.write(f'\033[{lines_down}A')
        sys.stdout.flush()
        time.sleep(0.01)

def download_part(host, port, part_num, start, end, file_name):
    sock = None
    try:
        sock = create_connection(host, port)
        sock.recv(1024)
        
        request = f"{start}-{end}".encode()
        sock.send(request)
        
        with open(f"./data/{file_name}.part{part_num}", "wb") as f:
            received = 0
            part_size = end - start
            
            while received < part_size:
                chunk_size = min(4096, part_size - received)
                data = sock.recv(chunk_size)
                
                if not data:
                    raise ConnectionError(f"Connection lost at {received} bytes")
                    
                f.write(data)
                received += len(data)
                
                progress_percent = min(received / part_size * 100, 100)
                update_progress(part_num, progress_percent)
                
        return True
        
    except Exception as e:
        print(f"\nError downloading part {part_num}: {e}")
        return False
        
    finally:
        if sock:
            sock.close()

# Rest of the code remains the same, just add init_progress_display call
def download_file(host, port):
    sock = create_connection(host, port)
    infofile = sock.recv(4096).decode().strip()
    sock.close()
    
    file_name, file_size = infofile.split("|")
    file_size = int(file_size)
    
    os.makedirs("./data", exist_ok=True)
    
    # Initialize progress display
    init_progress_display(file_name)
    
    part_size = file_size // 4
    futures = []
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        for i in range(4):
            start = i * part_size
            end = start + part_size if i < 3 else file_size
            future = executor.submit(download_part, host, port, i+1, start, end, file_name)
            futures.append(future)
            
        failed_parts = []
        for i, future in enumerate(as_completed(futures)):
            if not future.result():
                failed_parts.append(i+1)
                
    # Move cursor down past progress display before showing completion messages
    sys.stdout.write('\033[4B')
    sys.stdout.flush()
    
    if failed_parts:
        print(f"\nFailed to download parts: {failed_parts}")
        return
        
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
