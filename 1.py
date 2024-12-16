import os
import socket
import hashlib
import struct

PACKET_SIZE = 1024  # Kích thước gói tin UDP

# Xóa màn hình console
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Khởi tạo máy chủ
def initialize_server():
    host = socket.gethostbyname(socket.gethostname())  # Lấy địa chỉ IP của máy chủ
    port = 10000  # Cổng của máy chủ
    buffer_size = 1024  # Kích thước bộ đệm
    file_path = os.path.join(os.path.dirname(__file__), "ServerFiles") # Đường dẫn thư mục chứa file

    # Tạo thư mục nếu chưa tồn tại
    if not os.path.exists(file_path):
        os.mkdir(file_path)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Tạo socket UDP
    server_socket.bind((host, port)) # Gán socket với địa chỉ và cổng

    return server_socket, host, port, buffer_size, file_path

# Ghi danh sách tệp vào file text.txt
def write_text(file_path):
    file_list_path = os.path.join("text.txt")
    with open(file_list_path, "w") as file_list:
        for file_name in os.listdir(file_path): # Duyệt qua các file trong thư mục
            full_path = os.path.join(file_path, file_name)
            if os.path.isfile(full_path): # Kiểm tra xem là file hay thư mục
                file_size = os.path.getsize(full_path) # Lấy kích thước file
                file_list.write(f"{file_name} {file_size} bytes\n") # Ghi tên file và kích thước vào file text.txt

# Gửi danh sách tệp cho máy khách
def send_file_list_to_client(server_socket, client_address, file_path):
    files = [f for f in os.listdir(file_path) if os.path.isfile(os.path.join(file_path, f))] # Lấy danh sách các file
    file_list_str = "\t".join(files) # Nối các tên file bằng tab
    server_socket.sendto(file_list_str.encode("utf-8"), client_address) # Gửi danh sách file cho client

# Gửi gói tin và chờ ACK
def send_packet(sock, addr, packet):
    while True:
        sock.sendto(packet, addr) # Gửi gói tin
        try:
            sock.settimeout(0.5) # Đặt timeout cho việc nhận ACK
            ack, _ = sock.recvfrom(PACKET_SIZE) # Nhận ACK
            ack_num = struct.unpack('!I', ack)[0] # Giải mã số thứ tự ACK
            if ack_num == struct.unpack('!I', packet[:4])[0]: # So sánh số thứ tự ACK với số thứ tự gói tin
                break # Thoát vòng lặp nếu ACK đúng
        except socket.timeout: # Nếu timeout
            continue # Gửi lại gói tin

# Gửi tệp cho máy khách
def send_file(server_socket, client_address, file_name, buffer_size):
    if not os.path.exists(file_name): # Kiểm tra file có tồn tại không
        server_socket.sendto(b"ERROR: File not found", client_address) # Gửi thông báo lỗi nếu file không tồn tại
        return

    file_size = os.path.getsize(file_name) # Lấy kích thước file
    with open(file_name, "rb") as file: # Mở file ở chế độ đọc nhị phân
        checksum = hashlib.md5(file.read()).hexdigest() # Tính checksum MD5 của file
        server_socket.sendto(f"CHECK {checksum}".encode("utf-8"), client_address) # Gửi checksum cho client
        file.seek(0) # Đặt con trỏ file về đầu

        seq_num = 0 # Khởi tạo số thứ tự gói tin
        while chunk := file.read(buffer_size - 4): # Đọc file từng chunk
            packet = struct.pack('!I', seq_num) + chunk # Đóng gói số thứ tự và dữ liệu
            send_packet(server_socket, client_address, packet) # Gửi gói tin
            seq_num += 1 # Tăng số thứ tự

# Gửi lại gói tin bị mất
def retransmit_packet(server_socket, client_address, file_name, buffer_size, seq_num_retransmit):
    if not os.path.exists(file_name):
        return

    with open(file_name, "rb") as file:
        seq_num = 0
        while chunk := file.read(buffer_size - 4):
            if seq_num == seq_num_retransmit: # Kiểm tra số thứ tự gói tin cần gửi lại
                packet = struct.pack("!I", seq_num_retransmit) + chunk # Đóng gói tin
                send_packet(server_socket, client_address, packet) # Gửi gói tin
                print(f"Retransmitted packet {seq_num} of file {file_name}") # In thông báo gửi lại gói tin
                return
            seq_num += 1

# Lắng nghe yêu cầu từ máy khách
def server_listen(server_socket, buffer_size, file_path):
    while True:
        try:
            data, client_address = server_socket.recvfrom(buffer_size) # Nhận dữ liệu từ client
            command = data.decode("utf-8").strip() # Giải mã lệnh

            if command == "LIST": # Xử lý lệnh LIST
                send_file_list_to_client(server_socket, client_address, file_path)

            elif command.startswith("FILE"): # Xử lý lệnh FILE
                file_name = command[5:].strip() # Lấy tên file
                full_path = os.path.join(file_path, file_name) # Lấy đường dẫn đầy đủ của file
                send_file(server_socket, client_address, full_path, buffer_size) # Gửi file

            elif command.startswith("RETRANSMIT"): # Xử lý lệnh RETRANSMIT
                parts = command.split(" ") # Tách lệnh thành các phần
                seq_num_retransmit = int(parts[1]) # Lấy số thứ tự gói tin cần gửi lại
                filename = parts[2] # Lấy tên file
                full_path = os.path.join(file_path, filename) # Lấy đường dẫn đầy đủ của file
                retransmit_packet(server_socket, client_address, full_path, buffer_size, seq_num_retransmit) # Gửi lại gói tin

            else: # Xử lý lệnh không xác định
                print(f"Unknown command: {command}")

        except Exception as e: # Xử lý lỗi
            print(f"Error: {e}")

# Hàm main
if __name__ == "__main__":
    clear_screen()
    print("Starting UDP File Transfer Server...")

    server_socket, host, port, buffer_size, file_path = initialize_server() # Khởi tạo máy chủ
    print(f"Server running on {host}:{port}")
    write_text(file_path) # Ghi danh sách tệp vào file text.txt
    try:
        server_listen(server_socket, buffer_size, file_path) # Lắng nghe yêu cầu từ client
    except KeyboardInterrupt: # Xử lý Ctrl+C
        print("Server shutting down...")
        server_socket.close() # Đóng socket