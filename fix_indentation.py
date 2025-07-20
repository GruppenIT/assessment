#!/usr/bin/env python3
"""Script para corrigir a identação da função estatisticas"""

# Ler o arquivo
with open('routes/projeto.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Encontrar o início da função estatisticas
lines = content.split('\n')
start_func = None
end_func = None

for i, line in enumerate(lines):
    if 'def estatisticas(projeto_id):' in line:
        start_func = i
        continue
    
    if start_func is not None and line.startswith('def ') and not line.startswith('    '):
        end_func = i
        break

if start_func is None:
    print("Função estatisticas não encontrada")
    exit(1)

if end_func is None:
    # Função vai até o final do arquivo
    end_func = len(lines)

print(f"Função encontrada: linhas {start_func+1} a {end_func}")

# Corrigir identação: tudo dentro da função deve ter pelo menos 4 espaços
# Dentro do try deve ter 8 espaços
# Dentro do except deve ter 8 espaços
fixed_lines = []

# Copiar linhas antes da função
for i in range(start_func):
    fixed_lines.append(lines[i])

# Processar a função
in_try_block = False
in_except_block = False

for i in range(start_func, end_func):
    line = lines[i]
    
    if i == start_func:
        # Linha da definição da função
        fixed_lines.append(line)
        continue
    
    if '"""' in line and not line.strip().startswith('"""'):
        # Docstring - manter identação da função
        fixed_lines.append('    ' + line.strip())
        continue
    
    if line.strip() == '':
        # Linha vazia
        fixed_lines.append('')
        continue
        
    if line.strip().startswith('try:'):
        in_try_block = True
        fixed_lines.append('    try:')
        continue
        
    if line.strip().startswith('except'):
        in_try_block = False
        in_except_block = True
        fixed_lines.append('    except Exception as e:')
        continue
        
    # Determinar identação baseada no contexto
    if in_try_block:
        # Dentro do try: identação base de 8 espaços
        if line.strip():
            # Contar identação atual para preservar estrutura interna
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= 4:
                # Reidentar para dentro do try
                fixed_lines.append('        ' + line.strip())
            else:
                # Preservar identação relativa mas garantir mínimo do try
                extra_indent = current_indent - 4
                fixed_lines.append('        ' + ' ' * extra_indent + line.strip())
        else:
            fixed_lines.append('')
    elif in_except_block:
        # Dentro do except: identação de 8 espaços
        if line.strip():
            fixed_lines.append('        ' + line.strip())
        else:
            fixed_lines.append('')
    else:
        # Fora do try/except: identação normal da função (4 espaços)
        if line.strip():
            fixed_lines.append('    ' + line.strip())
        else:
            fixed_lines.append('')

# Copiar linhas depois da função
for i in range(end_func, len(lines)):
    fixed_lines.append(lines[i])

# Salvar o arquivo corrigido
with open('routes/projeto.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(fixed_lines))

print("Identação corrigida com sucesso!")