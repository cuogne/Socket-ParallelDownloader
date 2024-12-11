# Socket - Transfer File with Python
> A project about Socket of Computer Networking in HCMUS

> Note: This product is currently in the testing phase and is not yet complete. 
- It will be updated in the future (this will be fixed to match the functionality of the project).

Current directory structure 
```
client/
├── data/  
│   ├── 
│   ├── 
│   ├── 
│   ├── 
├── client.py
├── input.txt
server/
├── resources/
│   ├── 
│   ├── 
│   ├── 
│   ├── 
├── text.txt
├── server.py
.gitignore
README.md
```

- The `resources` directory contains the files (Storage)
- The `text.txt` file stores the information of the files that the client needs to download to the server.
- The `data` folder is where the downloaded files from the server to the client will be saved.
- The `input.txt` file contains information about the files that the client needs to download and upload to the server. This file can have content added to it as needed, and the client will check and update it every 5 seconds.

> [COMPLETED] You can open file `input.txt` and add file name that you want to download from server to client. It will be updated every 5 seconds. But you run server first and then run client.

# Run test
1. Open the terminal and paste the following command:

```zsh
git clone https://github.com/cuogne/Socket-TransferFile.git
```

2. If you haven't installed Python yet, please install it using the following command:

> If you have already installed it, you can skip this step and go to step 3

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

3. Open the folder and navigate to the `server` directory:

```zsh
cd server
```

4. Run the server with the command:

```zsh
python3 server.py
```

5. Open another terminal and navigate to the `client` directory:

```zsh
cd client
```

6. Run the client with the command:
```zsh
python3 client.py
```

7. Open the `input.txt` file in `client` folder and add the file name you want to download from the server to the client. You will be able to see the file name you just added in `input.txt` after 5 seconds and then the client will download file.

_Have a nice day !!!_