# Socket - Transfer File with Python
> A project about Socket of Computer Networking in HCMUS

> Note: This product is currently in the testing phase and is not yet complete. 
It will be updated in the future.

Current directory structure 
```
client/
├── DownloadTest/  
│   ├── 
│   ├── 
│   ├── 
│   ├── 
├── client.py
├── input.txt
server/
├── FileTest/
│   ├── 
│   ├── 
│   ├── 
│   ├── 
├── file.json
├── server.py
.gitignore
README.md
```

- The `FileTest` directory contains the files that the client needs to download.
- The `file.json` file stores information about the files in the `FileTest` directory, including:
    + File name
    + File size (KB)
- It will be updated each time the server runs (this will be fixed in the future to match the functionality of the project).
- The `DownloadTest` folder is where the downloaded files from the server to the client will be saved.

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