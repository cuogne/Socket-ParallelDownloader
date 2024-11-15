import socket
import json
import os

# directory to save downloaded files
DOWNLOAD_DIRECTORY = "DownloadTest"

def fetch_file_list():
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("127.0.0.1", 8888))
        client.send("LIST".encode())

        data = client.recv(8192).decode()  # receive JSON data from server
        client.close()

        return json.loads(data)  # return the file list as a list
    except Exception as e:
        print(f"[CLIENT] Error fetching file list: {e}")
        return []

def download_file(file_name):
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("127.0.0.1", 8888))
        client.send(f"DOWNLOAD:{file_name}".encode())

        if not os.path.exists(DOWNLOAD_DIRECTORY):
            os.makedirs(DOWNLOAD_DIRECTORY) # create dir if doesn't exist

        output_file = os.path.join(DOWNLOAD_DIRECTORY, file_name)

        # receive data and write to file
        with open(output_file, "wb") as file:
            while True:
                chunk = client.recv(4096)  # receive chunk by chunk
                if not chunk:
                    break
                if chunk.startswith(b"ERROR:"):
                    print(chunk.decode())  # display error from server
                    return
                file.write(chunk)

        print(f"[CLIENT] File {file_name} has been downloaded successfully.")
        client.close()
    except Exception as e:
        print(f"[CLIENT] Error downloading {file_name}: {e}")

if __name__ == "__main__":
    file_list = fetch_file_list()

    if not file_list:
        print("[CLIENT] No files to download.")
    else:
        print(f"[CLIENT] File list from the server:")
        for file_info in file_list:
            print(f"- {file_info['name']} ({file_info['size']})")

        for file_info in file_list:
            download_file(file_info['name'])
