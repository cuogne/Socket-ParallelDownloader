# Cơ chế Truyền Dữ Liệu Tin Cậy (Reliable Data Transfer - RDT)

## 1. Giao Thức Stop-and-Wait ARQ

### Phía Gửi (Client):
```python
request = f"download {filename} {start} {end} {expected_packet}"
sock.sendto(request.encode(), server_address)

# Chờ phản hồi với thời gian timeout
data, _ = sock.recvfrom(BUFFER_SIZE)

# Gửi ACK sau khi nhận đúng gói tin
sock.sendto(f"ACK {packet_num}".encode(), server_address)
```

## 2. Các Cơ Chế Đảm Bảo Tin Cậy

### a. Đánh Số Gói Tin (Sequence Numbers)
- Theo dõi thứ tự gói tin.
- Kiểm tra tuần tự.
- Xử lý các gói tin đến sai thứ tự.

```python
expected_packet = 0  # Số thứ tự gói tin mong đợi
packet_num = int(packet_num.decode())  # Số thứ tự gói tin nhận được
if packet_num == expected_packet:  # Kiểm tra đúng thứ tự
    xử_lý_gói_tin()
    expected_packet += 1
```

### b. Timeout và Gửi Lại (Timeout & Retransmission)
- Số lần thử lại tối đa: 3
- Thời gian timeout: 5 giây
- Tăng thời gian chờ theo cấp số nhân.

```python
retries = 0
while retries < MAX_RETRIES:
    try:
        gửi_yêu_cầu()
        đợi_phản_hồi()
    except socket.timeout:
        retries += 1
        continue
```

### c. Phát Hiện Lỗi
- Kiểm tra số thứ tự gói tin.
- Xác thực kích thước file.
- Tính toán checksum (nếu cần).

## 3. Sơ Đồ Luồng Hoạt Động
```
Client                  Server
  |--- Yêu cầu(seq=n) --->|
  |                       |
  |<-- Dữ liệu(seq=n) ----|
  |                       |
  |---- ACK(seq=n) ------>|
```

## Triển Khai Phía Server

### 1. Cơ Chế Số Thứ Tự Gói Tin
- Client gửi `expected_packet` trong request.

```python
expected_packet = int(request[4])

# Server đánh số thứ tự cho gói tin
packet = f"{expected_packet:010d}|".encode() + chunk
```

### 2. Cơ Chế ACK và Timeout
```python
try:
    server_socket.settimeout(3)  # Cài đặt timeout 3 giây
    ack, _ = server_socket.recvfrom(BUFFER_SIZE)

    # Kiểm tra số thứ tự trong ACK
    if not ack.decode().strip() == f"ACK {expected_packet}":
        logging.warning(f"Invalid ACK from {client_address}")
        # Server sẽ gửi lại nếu client yêu cầu lại gói tin này
except socket.timeout:
    logging.warning(f"ACK timeout from {client_address}")
    # Server sẽ gửi lại nếu client yêu cầu lại gói tin này
```

### 3. Xử Lý Mất Gói Tin
- Khi client không nhận được gói tin hoặc nhận sai:
  - Client tiếp tục gửi request với `expected_packet` tương ứng.
  - Server xử lý request và gửi lại gói tin.
- Khi server không nhận được ACK:
  - Client sẽ gửi lại request trong lần tới.
  - Server sẽ gửi lại gói tin.

### 4. Cơ Chế Offset Đảm Bảo Đúng Vị Trí Dữ Liệu
```python
offset = expected_packet * chunk_size
if offset < end - start:
    f.seek(start + offset)
    chunk = f.read(min(chunk_size, end - (start + offset)))
```

## Quá Trình Truyền Dữ Liệu Tin Cậy
Khi xảy ra mất dữ liệu trong quá trình truyền:

- Client phát hiện mất dữ liệu qua số thứ tự gói tin.
- Client yêu cầu lại gói tin bị mất.
- Server gửi lại đúng gói tin đó.
- Quá trình này lặp lại cho đến khi truyền thành công.
