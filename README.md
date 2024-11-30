# Socket - Transfer File with Python
> A project about Socket of Computer Networking in HCMUS

> Note: This product is currently in the testing phase and is not yet complete. 
- It will be updated in the future (this will be fixed to match the functionality of the project).

Current directory structure 
```
client/
├── dataClient/  
│   ├── 
│   ├── 
│   ├── 
│   ├── 
├── client.py
├── input.txt
server/
├── dataServer/
│   ├── 
│   ├── 
│   ├── 
│   ├── 
├── text.txt
├── server.py
.gitignore
README.md
```

- The `dataServer` directory contains the files that the client can download.
- The `text.txt` file stores information about the files in the `dataServer` directory.
- The `dataClient` folder is where the downloaded files from the server to the client will be saved.
- The `input.txt` file contains information about the files that the client needs to download and upload to the server. This file can have content added to it as needed, and the client will check and update it every 5 seconds.

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

_Have a nice day !!!_