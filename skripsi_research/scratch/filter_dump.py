with open('scratch/update4_sections_dump.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for line in lines:
    if any(k in line for k in ['[ELEMENT 149', '[ELEMENT 15', '[ELEMENT 16']):
        print(line[:150], end='' if line.endswith('\n') else '\n')
