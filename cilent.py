import socket

def client_program():
    host = '127.0.0.1'  # as both code is running on same pc
    port = 8001  # socket server port number

    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server
    print(f"Connected to server at {host}:{port}")
    
    message = input(" -> ")  # take input

    while message.lower().strip() != 'quit':
        client_socket.send(message.encode())  # send message
        data = client_socket.recv(1024).decode()  # receive response
        
        if (data == 'quit'):
            print("Connection closed by server.")
            break
        
        print('Received from server: ' + data)  # show in terminal

        message = input(" -> ")  # again take input
        
        if message == 'quit':
            print("Server shutting down.")
            break

    client_socket.send("quit".encode())  # send quit message to server
    client_socket.close()  # close the connection

if __name__ == '__main__':
    client_program()