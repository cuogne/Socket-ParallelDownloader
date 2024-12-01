import socket
import threading
import os
import signal
import sys
from concurrent.futures import ThreadPoolExecutor

class FileDownloader:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.num_connections = 4
        self.running = True
        
        # Handle Ctrl+C
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        print("\nStopping downloads...")
        self.running = False
        sys.exit(0)

    def download_chunk(self, filename, start_byte, chunk_size, part_num):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            
            request = f"GET {filename}:{start_byte}:{chunk_size}\n"
            sock.send(request.encode())
            
            chunk_filename = f"{filename}.part{part_num}"
            received_size = 0
            
            # Print initial status lines only for first part
            if part_num == 1:
                # Clear previous lines first
                print("\033[2J\033[H", end='')  # Clear screen and move to top
                for i in range(self.num_connections):
                    print(f" Downloading {filename} part {i+1} .... 0%")
                # Move cursor back up
                print(f"\033[{self.num_connections}A", end='')
            
            with open(chunk_filename, 'wb') as f:
                while self.running and received_size < chunk_size:
                    data = sock.recv(8192)
                    if not data:
                        break
                    f.write(data)
                    received_size += len(data)
                    
                    # Calculate and update progress
                    progress = (received_size / chunk_size) * 100
                    
                    # Move cursor to correct line and update
                    print(f"\033[{part_num-1}B", end='')  # Move down to part line
                    print(f"\r Downloading {filename} part {part_num} .... {progress:.1f}%", end='')
                    print(f"\033[{part_num-1}A", end='')  # Move back up
                    sys.stdout.flush()
            
            sock.close()
            return chunk_filename
                    
        except Exception as e:
            print(f"Error downloading chunk {part_num}: {str(e)}")
            return None



    def merge_chunks(self, filename, chunk_files):
        print(f"\nMerging chunks for {filename}...")
        
        # Get original file size
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.host, self.port))
        sock.send(f"SIZE {filename}\n".encode())
        original_size = int(sock.recv(1024).decode())
        sock.close()
        
        # Merge chunks
        with open(filename, 'wb') as outfile:
            for chunk_file in chunk_files:
                if chunk_file and os.path.exists(chunk_file):
                    with open(chunk_file, 'rb') as infile:
                        outfile.write(infile.read())
                    os.remove(chunk_file)  # Clean up chunk file
        
        # Verify file size
        final_size = os.path.getsize(filename)
        if final_size == original_size:
            print(f"File {filename} downloaded successfully! Size verified: {final_size} bytes")
        else:
            print(f"Warning: File size mismatch! Original: {original_size} bytes, Downloaded: {final_size} bytes")

    def download_file(self, filename):
        try:
            # Get file size from server
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            sock.send(f"SIZE {filename}\n".encode())
            file_size = int(sock.recv(1024).decode())
            sock.close()

            chunk_size = file_size // self.num_connections
            chunks = []
            
            # Create thread pool for parallel downloads
            with ThreadPoolExecutor(max_workers=self.num_connections) as executor:
                futures = []
                for i in range(self.num_connections):
                    start_byte = i * chunk_size
                    # Adjust last chunk size to include remaining bytes
                    if i == self.num_connections - 1:
                        current_chunk_size = file_size - start_byte
                    else:
                        current_chunk_size = chunk_size
                    
                    future = executor.submit(
                        self.download_chunk,
                        filename,
                        start_byte,
                        current_chunk_size,
                        i + 1
                    )
                    futures.append(future)
                
                # Wait for all chunks to complete
                chunks = [f.result() for f in futures]
            
            # Merge chunks into final file
            self.merge_chunks(filename, chunks)
            
        except Exception as e:
            print(f"Error downloading file {filename}: {str(e)}")

    def start(self):
        try:
            # Read input.txt for file list
            with open('input.txt', 'r') as f:
                files = f.read().splitlines()
            
            # Download files sequentially
            for filename in files:
                if not self.running:
                    break
                print(f"\nStarting download of {filename}")
                self.download_file(filename.strip())
                
        except FileNotFoundError:
            print("input.txt not found!")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    downloader = FileDownloader()
    downloader.start()