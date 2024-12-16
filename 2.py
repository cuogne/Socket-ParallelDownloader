import os
import socket
import hashlib
import struct

HOST = '127.0.0.1'  # Địa chỉ IP của máy chủ
PACKET_SIZE = 1024 # Kích thước gói tin

# Xóa màn hình console
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Khởi tạo máy khách
def initialize_client():
    server_port = 10000 # Cổng của máy chủ
    client_port = 10001 # Cổng của máy khách
    file_path = os.path.join(os.path.dirname(__file__), "ClientFiles") # Đường dẫn thư mục lưu file
    if not os.path.exists(file_path): # Tạo thư mục nếu chưa tồn tại
        os.mkdir(file_path)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Tạo socket UDP
    client_socket.bind((socket.gethostbyname(socket.gethostname()), client_port)) # Gán socket với địa chỉ và cổng
    return client_socket, (socket.gethostname(), server_port), file_path

# Yêu cầu danh sách tệp từ máy chủ
def request_file_list_from_server(client_socket, server_address):
    client_socket.sendto(b"LIST", server_address) # Gửi lệnh LIST
    data, _ = client_socket.recvfrom(PACKET_SIZE) # Nhận danh sách file
    file_list = data.decode("utf-8").split("\t") # Tách danh sách file
    print("Available files:")
    for file_name in file_list: # In danh sách file
        print(file_name)

# Gửi ACK
def send_ack(sock, addr, seq_num):
    ack = struct.pack('!I', seq_num) # Đóng gói số thứ tự ACK
    sock.sendto(ack, addr) # Gửi ACK


# Yêu cầu tải tệp từ máy chủ
def request_download_file(client_socket, server_address, file_name, save_path):
    client_socket.sendto(f"FILE {file_name}".encode("utf-8"), server_address) # Gửi lệnh FILE
    checksum_data, _ = client_socket.recvfrom(PACKET_SIZE) # Nhận checksum
    checksum = checksum_data.decode("utf-8")[6:] # Tách checksum


    with open(save_path, "wb") as file: # Mở file để ghi
        total_received = 0 # Khởi tạo tổng số byte đã nhận
        expected_seq_num = 0 # Khởi tạo số thứ tự gói tin mong đợi
        received_packets = {} # Lưu trữ các gói tin nhận được không đúng thứ tự

        while True:
            try:
                client_socket.settimeout(2) # Đặt timeout
                packet, _ = client_socket.recvfrom(PACKET_SIZE) # Nhận gói tin

                if len(packet) < 4: # Kiểm tra kích thước gói tin
                    continue

                seq_num = struct.unpack('!I', packet[:4])[0] # Giải mã số thứ tự gói tin
                data = packet[4:] # Tách dữ liệu

                if seq_num == expected_seq_num: # Nếu gói tin đúng thứ tự
                    file.write(data) # Ghi dữ liệu vào file
                    total_received += len(data) # Cập nhật tổng số byte đã nhận
                    print(f"Received {total_received} bytes, Packet: {seq_num}", end='\r') # In tiến trình
                    send_ack(client_socket, server_address, seq_num) # Gửi ACK
                    expected_seq_num += 1 # Cập nhật số thứ tự gói tin mong đợi

                    # Kiểm tra xem có gói tin nào đã nhận được trước đó nhưng chưa đúng thứ tự không
                    while expected_seq_num in received_packets:
                        data = received_packets.pop(expected_seq_num)
                        file.write(data)
                        total_received += len(data)
                        send_ack(client_socket, server_address, expected_seq_num)
                        expected_seq_num += 1

                elif seq_num > expected_seq_num: # Nếu gói tin nhận được có số thứ tự lớn hơn mong đợi
                    received_packets[seq_num] = data # Lưu gói tin vào bộ nhớ đệm

                else: # Nếu gói tin nhận được có số thứ tự nhỏ hơn mong đợi (gói tin trùng lặp)
                    send_ack(client_socket, server_address, seq_num) # Gửi lại ACK

                if total_received == int(os.path.getsize(os.path.join(os.path.dirname(__file__), "ServerFiles", file_name))): # Kiểm tra xem đã nhận đủ dữ liệu chưa
                    break

                if (seq_num - expected_seq_num) >= 4 and expected_seq_num not in received_packets: # Nếu mất gói tin
                    client_socket.sendto(f"RETRANSMIT {expected_seq_num} {file_name}".encode("utf-8"), server_address) # Gửi yêu cầu gửi lại gói tin
                    print(f"Request to retransmit packet {expected_seq_num}")

            except socket.timeout: # Nếu timeout
                if expected_seq_num not in received_packets and expected_seq_num < int(os.path.getsize(os.path.join(os.path.dirname(__file__), "ServerFiles", file_name))): # Nếu gói tin bị mất
                    client_socket.sendto(f"RETRANSMIT {expected_seq_num} {file_name}".encode("utf-8"), server_address) # Gửi yêu cầu gửi lại gói tin
                    print(f"Request to retransmit packet {expected_seq_num}")


    local_checksum = hashlib.md5(open(save_path, "rb").read()).hexdigest() # Tính checksum của file đã tải

    if checksum == local_checksum: # So sánh checksum
        print(f"\nFile {file_name} downloaded successfully.") # In thông báo thành công
    else:
        print(f"\nChecksum mismatch. File transfer failed. Expected {checksum} got {local_checksum}") # In thông báo lỗi checksum

# Tải file từ danh sách trong file input.txt
def download_files_from_list(client_socket, server_address, file_path):
    input_file_path = "input.txt"
    try:
        with open(input_file_path, "r") as f: # Mở file input.txt
            files_to_download = [line.strip() for line in f if line.strip()] # Đọc danh sách file cần tải, bỏ qua dòng trống
    except FileNotFoundError:
        print("Error: input.txt not found.") # In thông báo lỗi nếu không tìm thấy file input.txt
        return

    # Yêu cầu danh sách tệp từ máy chủ để kiểm tra tệp hợp lệ
    client_socket.sendto(b"LIST", server_address)
    data, _ = client_socket.recvfrom(PACKET_SIZE)
    allowed_files = data.decode("utf-8").split("\t")

    for file_name in files_to_download: # Duyệt qua danh sách file
        if file_name not in allowed_files:
            print(f"Error: {file_name} is not allowed to download.") # In thông báo lỗi nếu file không nằm trong danh sách cho phép
            continue
        save_path = os.path.join(file_path, file_name) # Tạo đường dẫn lưu file
        print(f"Downloading: {file_name}")
        request_download_file(client_socket, server_address, file_name, save_path) # Tải file

# Hàm main
if __name__ == "__main__":
    clear_screen()
    print("Starting UDP File Transfer Client...")

    client_socket, server_address, file_path = initialize_client() # Khởi tạo client
    while True:
        request_file_list_from_server(client_socket, server_address)
        command = input("Enter command (download/close): ") # Nhập lệnh
        if command == "download": # Xử lý lệnh download
            download_files_from_list(client_socket, server_address, file_path)
        elif command == "close": # Xử lý lệnh close
            print("Closing client...")
            client_socket.close() # Đóng socket
            break
        else: # Xử lý lệnh không hợp lệ
            print("Invalid command.")