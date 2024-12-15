import os
import socket
import hashlib
import struct

PACKET_SIZE = 1024

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def initialize_server():
    host = socket.gethostbyname(socket.gethostname())
    port = 10000
    buffer_size = 1024
    file_path = os.path.join(os.path.dirname(__file__), "ServerFiles")

    if not os.path.exists(file_path):
        os.mkdir(file_path)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))

    return server_socket, host, port, buffer_size, file_path

def write_text(file_path):
    file_list_path = os.path.join("text.txt")
    with open(file_list_path, "w") as file_list:
        for file_name in os.listdir(file_path):
            full_path = os.path.join(file_path, file_name)
            if os.path.isfile(full_path):
                file_size = os.path.getsize(full_path)
                file_list.write(f"{file_name} {file_size} bytes\n")

def send_file_list_to_client(server_socket, client_address, file_path):
    files = [f for f in os.listdir(file_path) if os.path.isfile(os.path.join(file_path, f))]
    file_list_str = "\t".join(files)
    server_socket.sendto(file_list_str.encode("utf-8"), client_address)

def send_packet(sock, addr, packet):
    while True:
        sock.sendto(packet, addr)
        try:
            sock.settimeout(0.5)
            ack, _ = sock.recvfrom(PACKET_SIZE)
            ack_num = struct.unpack('!I', ack)[0]
            if ack_num == struct.unpack('!I', packet[:4])[0]:
                break
        except socket.timeout:
            continue

def send_file(server_socket, client_address, file_name, buffer_size):
    if not os.path.exists(file_name):
        server_socket.sendto(b"ERROR: File not found", client_address)
        return

    file_size = os.path.getsize(file_name)
    with open(file_name, "rb") as file:
        checksum = hashlib.md5(file.read()).hexdigest()
        server_socket.sendto(f"CHECK {checksum}".encode("utf-8"), client_address)
        file.seek(0)

        seq_num = 0
        while chunk := file.read(buffer_size - 4):
            packet = struct.pack('!I', seq_num) + chunk
            send_packet(server_socket, client_address, packet)
            seq_num += 1

def retransmit_packet(server_socket, client_address, file_name, buffer_size, seq_num_retransmit):
    if not os.path.exists(file_name):
        return

    with open(file_name, "rb") as file:
        seq_num = 0
        while chunk := file.read(buffer_size - 4):
            if seq_num == seq_num_retransmit:
                packet = struct.pack("!I", seq_num_retransmit) + chunk
                send_packet(server_socket, client_address, packet)
                print(f"Retransmitted packet {seq_num} of file {file_name}")
                return
            seq_num += 1

def server_listen(server_socket, buffer_size, file_path):
    while True:
        try:
            data, client_address = server_socket.recvfrom(buffer_size)
            command = data.decode("utf-8").strip()

            if command == "LIST":
                send_file_list_to_client(server_socket, client_address, file_path)

            elif command.startswith("FILE"):
                file_name = command[5:].strip()
                full_path = os.path.join(file_path, file_name)
                send_file(server_socket, client_address, full_path, buffer_size)

            elif command.startswith("RETRANSMIT"):
                parts = command.split(" ")
                seq_num_retransmit = int(parts[1])
                filename = parts[2]
                full_path = os.path.join(file_path, filename)
                retransmit_packet(server_socket, client_address, full_path, buffer_size, seq_num_retransmit)

            else:
                print(f"Unknown command: {command}")

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    clear_screen()
    print("Starting UDP File Transfer Server...")

    server_socket, host, port, buffer_size, file_path = initialize_server()
    print(f"Server running on {host}:{port}")
    write_text(file_path)
    try:
        server_listen(server_socket, buffer_size, file_path)
    except KeyboardInterrupt:
        print("Server shutting down...")
        server_socket.close()