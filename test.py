import sys
import time

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

# cursor_demo()

for i in range(6):
    sys.stdout.write(f'\033[{i}C hello')
    