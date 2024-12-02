# This file is used for sending the file over socket
import os
import socket
import time

# tao socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # ipv4, tcp
sock.bind((socket.gethostname(), 9876)) # dang ki dia chi ip va port
sock.listen(5) # so ket noi client toi da
print("Host Name: ", sock.getsockname())

# chap nhan ket noi tu client
server, addr = sock.accept()

# nhap file can down
file_name = input("File Name:")
file_size = os.path.getsize(file_name) # lay kich thuoc tep

infofile = f"{file_name}|{file_size}" # goi du lieu lai
server.send(infofile.encode()) # gui cho client

# mo file va gui du lieu
with open(file_name, "rb") as file:
    chunk = 0
    
    start_time = time.time()

    while chunk <= file_size:
        data = file.read(1024)
        if not (data):
            break
        server.sendall(data) # gui sendall de dam bao gui het du lieu
        chunk += len(data)

    end_time = time.time()

print("Gui duoc roi, thoi gian gui: ", end_time - start_time)

sock.close()