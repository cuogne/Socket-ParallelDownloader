import os
import socket
import hashlib
import struct

HOST = '127.0.0.1'
PACKET_SIZE = 1024

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def initialize_client():
    server_port = 10000
    client_port = 10001
    file_path = os.path.join(os.path.dirname(__file__), "ClientFiles")
    if not os.path.exists(file_path):
        os.mkdir(file_path)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind((socket.gethostbyname(socket.gethostname()), client_port))
    return client_socket, (socket.gethostname(), server_port), file_path

def request_file_list(client_socket, server_address):
    client_socket.sendto(b"LIST", server_address)
    data, _ = client_socket.recvfrom(PACKET_SIZE)
    file_list = data.decode("utf-8").split("\t")
    print("Available files:")
    for file_name in file_list:
        print(file_name)

def send_ack(sock, addr, seq_num):
    ack = struct.pack('!I', seq_num)
    sock.sendto(ack, addr)

def request_file(client_socket, server_address, file_name, save_path):
    client_socket.sendto(f"FILE {file_name}".encode("utf-8"), server_address)
    checksum_data, _ = client_socket.recvfrom(PACKET_SIZE)
    checksum = checksum_data.decode("utf-8")[6:]

    with open(save_path, "wb") as file:
        total_received = 0
        expected_seq_num = 0
        received_packets = {}

        while True:
            try:
                client_socket.settimeout(2)
                packet, _ = client_socket.recvfrom(PACKET_SIZE)

                if len(packet) < 4:
                    continue

                seq_num = struct.unpack('!I', packet[:4])[0]
                data = packet[4:]

                if seq_num == expected_seq_num:
                    file.write(data)
                    total_received += len(data)
                    print(f"Received {total_received} bytes, Packet: {seq_num}", end='\r')
                    send_ack(client_socket, server_address, seq_num)
                    expected_seq_num += 1

                    while expected_seq_num in received_packets:
                        data = received_packets.pop(expected_seq_num)
                        file.write(data)
                        total_received += len(data)
                        send_ack(client_socket, server_address, expected_seq_num)
                        expected_seq_num += 1
                elif seq_num > expected_seq_num:
                    received_packets[seq_num] = data
                else:
                    send_ack(client_socket, server_address, seq_num)

                if total_received == int(os.path.getsize(os.path.join(os.path.dirname(__file__), "ServerFiles", file_name))):
                    break

                if (seq_num - expected_seq_num) >= 4 and expected_seq_num not in received_packets:
                    client_socket.sendto(f"RETRANSMIT {expected_seq_num} {file_name}".encode("utf-8"), server_address)
                    print(f"Request to retransmit packet {expected_seq_num}")

            except socket.timeout:
                if expected_seq_num not in received_packets and expected_seq_num < int(os.path.getsize(os.path.join(os.path.dirname(__file__), "ServerFiles", file_name))):
                    client_socket.sendto(f"RETRANSMIT {expected_seq_num} {file_name}".encode("utf-8"), server_address)
                    print(f"Request to retransmit packet {expected_seq_num}")

    local_checksum = hashlib.md5(open(save_path, "rb").read()).hexdigest()

    if checksum == local_checksum:
        print(f"\nFile {file_name} downloaded successfully.")
    else:
        print(f"\nChecksum mismatch. File transfer failed. Expected {checksum} got {local_checksum}")

def download_files_from_list(client_socket, server_address, file_path):
    input_file_path = "input.txt"
    try:
        with open(input_file_path, "r") as f:
            files_to_download = [line.strip() for line in f]
    except FileNotFoundError:
        print("Error: input.txt not found.")
        return

    for file_name in files_to_download:
        save_path = os.path.join(file_path, file_name)
        print(f"Downloading: {file_name}")
        request_file(client_socket, server_address, file_name, save_path)

if __name__ == "__main__":
    clear_screen()
    print("Starting UDP File Transfer Client...")

    client_socket, server_address, file_path = initialize_client()
    while True:
        command = input("Enter command (list/download/close): ")
        if command == "list":
            request_file_list(client_socket, server_address)
        elif command == "download":
            download_files_from_list(client_socket, server_address, file_path)
        elif command == "close":
            print("Closing client...")
            client_socket.close()
            break
        else:
            print("Invalid command.")