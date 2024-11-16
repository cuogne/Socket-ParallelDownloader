# read file json and input.txt, compare the content in input.txt with data.json

import json

# Open and read the JSON file
with open('data.json', 'r') as file:
    data = json.load(file)
      
with open("input.txt", "r") as input_file:
    input_files = [line.strip() for line in input_file.readlines()]
        
for file_info in data:
    if file_info['name'] in input_files:
        print(file_info['name'])

