import socket

def server_program():
    host = '127.0.0.1'
    port = 8001  

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))  # bind host address and port together
    server_socket.listen(2)
    print(f"Server listening on {host}:{port}")
    conn, address = server_socket.accept()  # accept new connection
    print("Connection from: " + str(address))
    while True:
        data = conn.recv(1024).decode()
        if not data or data.lower() == 'quit':
            print("Connection closed by cilent.")
            break
        
        print("from connected user: " + str(data))
        data = input(' -> ')
        if data.lower() == 'quit':
            conn.send(data.encode())
            print("Server shutting down.")
            break
        conn.send(data.encode())  # send data to the client

    conn.close()  # close the connection

if __name__ == '__main__':
    try:
        server_program()
    except KeyboardInterrupt:
        print("\nServer stopped.")