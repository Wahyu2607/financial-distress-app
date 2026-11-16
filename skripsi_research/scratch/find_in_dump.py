with open('scratch/update4_sections_dump.txt', 'r', encoding='utf-8') as f:
    text = f.read()

print("Length of file:", len(text))
for line in text.split('\n'):
    if '4.2.10' in line or 'Validasi Ahli' in line:
        print(line)
