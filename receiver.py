import os
import socket
import threading
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

lock = threading.Lock()
last_used_line = 0  # dòng cuối đã sử dụng

def create_connection(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((host, port))
    return sock

def display_progress(base_line, part_num, progress_percent):
    with lock:
        target_line = base_line + part_num  # Dòng của từng phần
        sys.stdout.write(f'\033[{target_line}H')  # Di chuyển con trỏ đến dòng của phần đó
        sys.stdout.write('\033[2K')  # Xóa nội dung dòng hiện tại
        sys.stdout.write(f"Part {part_num} - Progress: {progress_percent:.2f}% / 100%\n")
        sys.stdout.flush()
        time.sleep(0.01)

def download_part(host, port, file_name, part_num, start, end, base_line):
    sock = None
    try:
        sock = create_connection(host, port)
        sock.recv(1024)  # Xác nhận kết nối

        request = f"{file_name}|{start}-{end}".encode()
        sock.send(request)

        part_path = f"./data/{file_name}.part{part_num}"
        with open(part_path, "wb") as f:
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
                display_progress(base_line, part_num, progress_percent)

        return True

    except Exception as e:
        print(f"\nError downloading part {part_num}: {e}")
        return False

    finally:
        if sock:
            sock.close()


def merge_parts(file_name, parts):
    output_path = f"./data/{file_name}"
    try:
        with open(output_path, "wb") as output_file:
            for part_path in parts:
                with open(part_path, "rb") as part_file:
                    while chunk := part_file.read(8192):
                        output_file.write(chunk)
                os.remove(part_path)  # Xóa phần sau khi ghép
    except Exception as e:
        print(f"\nError merging parts: {e}")

def download_file(host, port, file_name, file_size):
    global last_used_line
    os.makedirs("./data", exist_ok=True)
    part_size = file_size // 4
    futures = []
    parts = []

    base_line = last_used_line + 1  # Dòng bắt đầu của tệp này
    last_used_line = base_line + 6  # Dòng cuối của tệp này (dành chỗ cho tiến trình và thông báo)

    print(f"\033[{base_line}HDownloading {file_name}...\n")  # In thông báo tải xuống

    with ThreadPoolExecutor(max_workers=4) as executor:
        for i in range(4):
            start = i * part_size
            end = start + part_size if i < 3 else file_size
            future = executor.submit(download_part, host, port, file_name, i + 1, start, end, base_line)
            futures.append(future)

        for i, future in enumerate(as_completed(futures)):
            if not future.result():
                print(f"Failed to download part {i + 1}")
            else:
                parts.append(f"./data/{file_name}.part{i + 1}")

    merge_parts(file_name, parts)
    
    print(f"\033[{base_line + 5}HDownload completed successfully for {file_name}!\n")
    print(f"\033[{base_line + 6}H" + "-" * 40)

def get_file_list_from_server(host, port):
    sock = create_connection(host, port)
    try:
        file_list = sock.recv(4096).decode().strip()
        print("Available files:")
        print(file_list)
        return [line.split("|") for line in file_list.splitlines()]
    finally:
        sock.close()

def load_input_file():
    input_file = "input.txt"
    if not os.path.exists(input_file):
        print(f"Input file '{input_file}' not found. Please create it and add filenames to download.")
        return []

    with open(input_file, "r") as f:
        return [line.strip() for line in f if line.strip()]

def main():
    global last_used_line
    host = input("Host Name: ")
    port = 9876

    # Nhận danh sách file từ server
    file_list = get_file_list_from_server(host, port)

    # Đọc danh sách file cần tải từ input.txt
    files_to_download = load_input_file()
    if not files_to_download:
        print("No files to download. Exiting.")
        return

    # Tạo một từ điển từ danh sách file server để tra cứu nhanh
    server_files = {file_name: int(file_size_str) for file_name, file_size_str in file_list}

    last_used_line = len(file_list) + 3  # dong bat dau danh sach file

    # tai file trong file input.txt
    for file_name in files_to_download:
        if file_name in server_files:
            file_size = server_files[file_name]
            download_file(host, port, file_name, file_size)
        else:
            print(f"\033[{last_used_line + 1}HFile '{file_name}' not found on server!")
            last_used_line += 2  # Tăng dòng cơ sở nếu không tìm thấy file

if __name__ == "__main__":
    main()
