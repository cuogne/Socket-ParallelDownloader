import os

data_size = os.path.getsize("./avt.jpeg")

print(data_size)

part_size = data_size // 4
last_part_size = data_size - (part_size * 3)

print(part_size, last_part_size)

for i in range(4):
    start = i * part_size + 1 if i != 0 else 0
    end = (i + 1) * part_size if i != 3 else data_size
    
    print(start, end)