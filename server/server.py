import os
import json
import socket

DIRECTORY_PATH = "FileTest" # contain files for client download
JSON_FILE = "file.json" # file .json contain name and size of file

def generate_file_list():
    file_list = []
    
    for file_name in os.listdir(DIRECTORY_PATH):
        file_path = os.path.join(DIRECTORY_PATH, file_name)
        if os.path.isfile(file_path):
            file_size = os.path.getsize(file_path)  # file size
            file_list.append({"name": file_name, "size": f"{file_size} bytes"})
            
    # write in file .json
    with open(JSON_FILE, "w") as json_file:
        json.dump(file_list, json_file, indent=4)

def handle_client(client_socket):
    try:
        request = client_socket.recv(1024).decode()
        if request == "LIST":
            
            # send the list of files from file.json
            with open(JSON_FILE, "r") as json_file:
                file_data = json_file.read()
            client_socket.send(file_data.encode())
        elif request.startswith("DOWNLOAD:"):
            
            # get the file name from the request
            file_name = request.split(":")[1].strip()
            file_path = os.path.join(DIRECTORY_PATH, file_name)

            if os.path.exists(file_path):
                # send file data in chunks
                with open(file_path, "rb") as file:
                    while chunk := file.read(4096):
                        client_socket.send(chunk)
            else:
                client_socket.send(b"ERROR: File not found.")
                
        client_socket.close()
    except Exception as e:
        print(f"[SERVER] Error: {e}")

def start_server():
    
    generate_file_list()

    # create socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 8888))
    server.listen(5)
    print("[SERVER] Server is running on port 8888...")

    try:
        while True:
            client_socket, client_address = server.accept()
            print(f"[SERVER] Client connected: {client_address}")
            handle_client(client_socket)
    except KeyboardInterrupt:
        print("\n[SERVER] Server is shutting down...")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()
