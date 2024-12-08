import os
import socket
import time
import threading

host = input("Host Name: ")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# tao ket noi voi server
try:
    sock.connect((host, 9876))
    print("Connected Successfully")
except:
    print("Unable to connect")
    exit(0)

infofile = sock.recv(4096).decode().strip()
print(f"Received infofile: {infofile}")  # in thong tin file

# tach du lieu
file_name, file_size = infofile.split("|")
file_size = int(file_size)

# chia file lam 4
part_size = file_size // 4
last_part_size = file_size - (part_size * 3)

# print(part_size, last_part_size)

# luu 4 process cua tung part
progress = [""] * 4

def download_part(i, start, end):
    with open(f"./data/{file_name}.part{i+1}", "wb") as part_file:
        chunk = 0
        sock.send(f"{start}|{end}".encode())
        while chunk < (end - start):
            # nhan du lieu tu server toi da 4096 byte hoac so byte con lai
            # toi nghi van de mat file la do nhan du lieu (SIZE)
            data = sock.recv(min(4096, (end - start) - chunk))  
            if not data:
                print(f"Connection lost while downloading part {i+1}")
                break
            part_file.write(data)  # ghi du lieu vao file
            chunk += len(data)  # update so byte da nhan
            process = min(chunk / (end - start) * 100, 100)  # tinh % tai xuong
            
            # cap nhat tien trinh tai xuong
            progress[i] = f"Part {i+1} - Process: {process:.2f}%/100%"

            os.system('clear')
            for p in progress:
                print(p) # in ra tien trinh cua cac part

            time.sleep(0.01)  # lam cham de xem tien trinh tai xuong
        print()

# tao thread
threads = []
for i in range(4):
    start = i * part_size
    end = (i + 1) * part_size if i != 3 else file_size 
    # print(f"Downloading Part {i+1} from byte {start} to byte {end}")
    thread = threading.Thread(target=download_part, args=(i, start, end))
    threads.append(thread)
    thread.start()  # bat dau tai xuong

# cho tat ca cac thread ket thuc
for thread in threads:
    thread.join()

# ghep cac part lai
with open(f"./data/{file_name}", "wb") as merged_file:
    for i in range(4):
        part_path = f"./data/{file_name}.part{i+1}"
        with open(part_path, "rb") as part_file:
            merged_file.write(part_file.read())
        os.remove(part_path) # xoa part temp sau khi ghep

# check kich thuoc file
merged_file_size = os.path.getsize(f"./data/{file_name}")
if merged_file_size == file_size:
    print(f"File downloaded successfully!")
else:
    print("Download failed, file size mismatch.")

sock.close()
