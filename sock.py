import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((socket.gethostname(), 9876))

print(f"Server started at {server.getsockname()}")

server.close()