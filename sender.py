import os
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # ipv4, tcp
sock.bind((socket.gethostname(), 9876)) # dang ki dia chi ip va port
sock.listen(1) # so ket noi client toi da
print("Host Name: ", sock.getsockname())

# chap nhan ket noi tu client
server, addr = sock.accept()

file_name = input("File Name: ") # nhap ten file can down
file_size = os.path.getsize(file_name)

infofile = f"{file_name}|{file_size}" # dong goi thong tin lai
server.send(infofile.encode())

try:
    with open(file_name, "rb") as file:
        chunk = 0 
        while chunk <= file_size:
            data = file.read(1024)
            if not data:
                break
            try:
                server.sendall(data)
                chunk += len(data)
            except socket.error:
                print("Connection lost with client")
                break
        
    print("File Sent Successfully")
except Exception as e:
    print(f"Error: {e}")
finally:
    sock.close()