import os
import socket
import threading

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((socket.gethostname(), 9876))
sock.listen(5)
file_name = None
file_size = None
file_lock = threading.Lock()
print(f"Server started at {sock.getsockname()}")

def handle_client(client_sock, addr):
    global file_name, file_size
    try:
        # initial connection - send file info
        with file_lock:
            if file_name is None:
                file_name = input("File Name: ")
                file_size = os.path.getsize(file_name)  # get file size
            info = f"{file_name}|{file_size}"  # goi du lieu lai
            client_sock.send(info.encode())  # gui cho client
        
        # xu li de down tung phan
        while True:
            request = client_sock.recv(1024).decode().strip()
            # print(request) 12893-25786, 25786-38679,...
            if not request:
                break

            parts = request.split('-') # tach du lieu

            if len(parts) != 2:
                # client gui sai format {start}-{end}
                error_msg = "Invalid request format. Please send in the format start-end."
                client_sock.send(error_msg.encode()) # gui thong bao loi qua cho client
                continue # skip

            start_str, end_str = parts
            try:
                start, end = int(start_str), int(end_str)
                # start = 12893, end = 25786
            except ValueError:
                # sai khoang gia tri
                error_msg = "Invalid range values. Please send valid integers for start and end."
                client_sock.send(error_msg.encode())
                continue  # skip

            # process file download for the valid range
            with file_lock:
                with open(file_name, 'rb') as f:
                    f.seek(start) # mo file nhi phan tai vi tri start
                    remaining = end - start # phan con lai
                    while remaining > 0:
                        chunk_size = min(4096, remaining) # chunk nhan kich thuoc 4096 hoac phan con lai
                        data = f.read(chunk_size) # doc chunk_size byte
                        if not data:
                            break
                        client_sock.sendall(data)
                        remaining -= len(data)
            break

    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        client_sock.close()

def run():
    try:
        while True:
            client_sock, addr = sock.accept()
            print(f"Connected by {addr}")
            thread = threading.Thread(target=handle_client, args=(client_sock, addr))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("\nServer is shutting down...")
    finally:
        sock.close()

if __name__ == "__main__":
    run()
