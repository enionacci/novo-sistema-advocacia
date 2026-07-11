with open('backend/documentos/views.py', 'rb') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if b'"""' in line:
        print(f'L{i}: {line.decode("utf-8", errors="replace").rstrip()[:120]}')
