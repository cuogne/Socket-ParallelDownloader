# Socket - MultiThreaded File Transfer with Python using TCP and UDP.
> A project about Socket of Subject CSC10008 - Computer Networking in HCMUS

## Introduction to The Project
- This project is about transferring files between the server and the client using sockets and multithreading in Python using TCP and UDP. 
- The server will store the files in the `resources` directory, server will also store the information of the files that client can download from server to client in the `text.txt` file.

- The client connects to the server and receives the list of files from the server `(text.txt)`, displaying them on the screen.

- The client will download the requested files listed in the `input.txt` file sequentially. These files will be compared with the list of available files sent from the server. The downloaded files from server to client will be stored in the `data` directory. You can open file `input.txt` and add file name that you want to download from server to client. It will be updated every 5 seconds (if client and server is running).

- For each file to be downloaded, the client will open 4 parallel connections to the server to start downloading parts of the file (max 4 connections to the server). The file size can be divided by 4 to request the server to send each chunk to each connection. On the client screen, the download progress percentage (from 0-100%) will be displayed based on the progress of downloading the parts of the file being downloaded.

- After downloading all parts of a file, the client needs to concatenate the downloaded parts into a complete file. This can be verified by checking the total file size and successfully opening the file.

- When the client completes the download, you can press "Ctrl + C" to terminate the program in client.

## Current directory structure 
```
TCP/
├── client/  
│   ├── data/
│   │   ├── arya.gif
│   │   ├── jinx.png
│   │   ├── ...
│   │   ├── ...
│   ├── client.py
│   ├── input.txt
├── server/  
│   ├── resources/
│   │   ├── arya.gif
│   │   ├── jinx.png
│   │   ├── background.jpg
│   │   ├── ...
│   ├── server.py
│   ├── text.txt
UDP/
├── client/  
│   ├── downloads/
│   │   ├── arya.gif
│   │   ├── background.jpg
│   │   ├── ...
│   │   ├── ...
│   ├── checklog_client.log
│   ├── client.py
│   ├── input.txt
├── server/  
│   ├── dataServer/
│   │   ├── arya.gif
│   │   ├── avt.jpeg
│   │   ├── background.jpg
│   │   ├── ...
│   ├── server.py
│   ├── text.txt
.gitignore
README.md
```
## TCP - Transmission Control Protocol
- The `resources` directory contains the files
- The `text.txt` file stores the information of the files that the client can download from the server.
- The `data` folder is where the downloaded files from the server to the client will be saved.
- The `input.txt` file contains information about the files that the client needs to download and upload to the server. This file can have content added to it as needed, and the client will check and update it every 5 seconds.

## UDP - User Datagram Protocol
- The `dataServer` directory contains the files that the client can download from the server.
- The `text.txt` file stores the information of the files that the client can download from the server.
- The `downloads` folder is where the downloaded files from the server to the client will be saved.
- The `input.txt` file contains information about the files that the client needs to download and upload to the server. This file can have content added to it as needed, and the client will check and update it every 5 seconds.
- The `checklog_client.log` file contains the log information of the client. It used to check the client's status and the download status of the files.

## Requirements

### TCP

> [COMPLETED] Multiple clients can get a list of files from the Server and ctrl-c

> [COMPLETED] Displays percent download chunks of the file (but if the terminal is too small, it may not display correctly, maybe fixed in the future)

> [COMPLETED] Scan the input.txt file once every 5 seconds

> [COMPLETED] Many clients can successfully download all chunks from the server.

> [COMPLETED] The downloaded file must be correct and have enough capacity

### UDP

> [COMPLETED] UDP successfully downloads 1 chunk with rdt (reliable data transfer) mechanism

> [COMPLETED] UDP successfully downloads all chunks with rdt (reliable data transfer) mechanism

More information with the rdt (reliable data transfer) mechanism i used in the UDP project, you can check it out [here](/rdt.txt)

## Run test
### 1. Open the terminal and paste the following command:

```zsh
git clone https://github.com/cuogne/Socket-TransferFile.git
```

### 2. If you haven't installed Python yet, please install it using the following command:

> If you have already installed it, you can skip this step and go to [step 3](#3-open-the-folder-and-choose-the-protocol-you-want-to-run-tcpudp)

On macOS:
```zsh
brew install python3
```

On Windows:
```powershell
winget install --id Python.Python.3 --source winget
```

Or you can download it from the python homepage: [click here](https://www.python.org/downloads/)

You can check this python version by command:

```terminal
python3 --version
```

### 3. Open the folder and choose the protocol you want to run (TCP/UDP):

```zsh
cd TCP
```

```zsh
cd UDP
```

> Notes: The steps below are similar for both TCP and UDP

### 4. Navigate to the `server` directory:

```zsh
cd server
```

### 5. Run the server with the command:

```zsh
python3 server.py
```

You can see the server is running with host, port information and waiting for the client to connect.

### 6. Open another terminal and navigate to the `client` directory:

```zsh
cd client
```

### 7. Run the client with the command:
```zsh
python3 client.py
```

- TCP:
    + You can enter the IP address of the server and press Enter, and you will see the list of files that the client can download from the server and you can press enter to start download, the client will start downloading the files.
- UDP:
    + You will see the list of files that the client can download from the server and you can press enter to start download, the client will start downloading the files.

- Open the `input.txt` file in `client` folder and add the file name you want to download from the server to the client. You will be able to see the file name you just added in `input.txt` after 5 seconds and then the client will download file. After downloading the file, you can check the `data` folder to see the downloaded file and press "Ctrl + C" to terminate the program.

With UDP, you can check the `checklog_client.log` file to see the log information of the client.

_Have a nice day !!!_