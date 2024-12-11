import os
import sys
import time
import math

def cursor_demo():
    # Clear màn hình
    sys.stdout.write('\033[2J')
    sys.stdout.write('\033[H')  # Di chuyển con trỏ về đầu màn hình
    
    # In các dòng ban đầu
    # print("Dòng 1")
    # print("Dòng 2") 
    # print("Dòng 3")
    # print("Dòng 4")
    
    # Di chuyển con trỏ:
    time.sleep(1)
    sys.stdout.write(f'\033[4C hello')  # Phai 4 dòng
    
    time.sleep(5)
    sys.stdout.flush()
    
    time.sleep(1)
    sys.stdout.write('\033[2B')  # Xuống 2 dòng
    sys.stdout.flush()
    
    time.sleep(1)
    sys.stdout.write('\033[10A')  # Lene 10 ký tự
    sys.stdout.flush()
    
    time.sleep(1)
    sys.stdout.write('\033[5D')   # Trái 5 ký tự
    sys.stdout.flush()
    
    time.sleep(1)
    sys.stdout.write('\r')        # Về đầu dòng
    sys.stdout.flush()
    

# Các mã ANSI cơ bản:
# \033[H    - Di chuyển về đầu màn hình
# \033[2J   - Xóa màn hình
# \033[nA   - Di chuyển lên n dòng
# \033[nB   - Di chuyển xuống n dòng
# \033[nC   - Di chuyển phải n ký tự
# \033[nD   - Di chuyển trái n ký tự
# \033[2K   - Xóa dòng hiện tại
# \r        - Về đầu dòng
# \033[s    - Lưu vị trí con trỏ
# \033[u    - Khôi phục vị trí con trỏ đã lưu
# flush     - Đẩy dữ liệu

# cursor_demo()

# for i in range(4):
#     sys.stdout.write(f'\033[B hello{i}')
#     sys.stdout.flush()
#     time.sleep(1)
#     sys.stdout.write('\033[2K\r')
#     sys.stdout.flush()
# print("\nxin chao")

def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

data_size = os.path.getsize('./resources/background.jpg')
print(data_size // 4)
print(data_size - (data_size // 4)*3)

data_size = convert_size(data_size)
print(data_size)