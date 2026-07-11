import sys
with open('backend/documentos/views.py', 'rb') as f:
    data = f.read()

# Conta ocorrências de """
count = data.count(b'"""')
print(f'Ocorrências de """ : {count}')
print(f'É par? {count % 2 == 0}')

# Tenta compilar
try:
    compile(data, 'views.py', 'exec')
    print('OK - compilação bem sucedida')
except SyntaxError as e:
    print(f'Erro: {e}')
    # Mostra contexto
    lines = data.split(b'\n')
    lineno = e.lineno
    if lineno:
        for i in range(max(0, lineno-3), min(len(lines), lineno+2)):
            marker = '>>>' if i == lineno-1 else '   '
            print(f'{marker} L{i+1}: {lines[i].decode('utf-8', errors='replace')[:100]}')
