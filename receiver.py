import os
import socket
import time

host = input("Host Name: ")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# tao ket noi voi socket
try:
    sock.connect((host, 9876))
    print("Connected Successfully")
except:
    print("Unable to connect")
    exit(0)
    
infofile = sock.recv(1024).decode().strip()
print(f"Received infofile: {infofile}") # in ra test thu

# nhan file_name va file_size
file_name, file_size = infofile.split("|")
file_size = int(file_size)

# tinh toan de chia 4 phan
part_size = file_size // 4
last_part_size = file_size - (part_size * 3)  # xu li cai thang cuoi cung ra rieng

# bat dau tinh gio down thu
start_time = time.time()

# tai 4 phan cua file
for i in range(4):
    if i < 3:
        current_part_size = part_size
    else:
        current_part_size = last_part_size

    ''' phai xu li them da luong de 4 cai part down cung luc'''
    
    with open(f"./download/{file_name}.part{i+1}", "wb") as part_file:
        chunk = 0
        while chunk < current_part_size:
            data = sock.recv(min(1024, current_part_size - chunk))  # nhan du lieu toi thieu giua 1024 va so byte con lai
            if not data:
                print(f"Connection lost while downloading part {i+1}")
                break
            part_file.write(data)  # ghi du lieu vao file
            chunk += len(data)  # tinh toan so byte da nhan
            process = min(chunk / current_part_size * 100, 100)  # tinh toan phan tram de hien thi tien trinh (toi da la 100)
            print(f"Part {i+1} downloaded {process:.2f}%/100%", end="\r")  # hien thi tien trinh
            time.sleep(0.1)  # delay 0.1s de hien thi tien trinh (tai file be qua, co tram KB)
        print()

# ghep cac part lai
with open(f"./download/{file_name}", "wb") as merged_file:
    for i in range(4):
        part_path = f"./download/{file_name}.part{i+1}"
        with open(part_path, "rb") as part_file:
            merged_file.write(part_file.read())
        os.remove(part_path)  # xoa cac part tam sau khi tai xong
        
end_time = time.time() # end time

# kiem tra file da duoc tai du byte so voi file goc chua
merged_file_size = os.path.getsize(f"./download/{file_name}")
if merged_file_size == file_size:
    print(f"Down file thanh cong, tong thoi gian thuc hien: {end_time - start_time:.4f} s")
else:
    print("That bai cmnr, mang may tinh qua kinh khung.")

sock.close()
