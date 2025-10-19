#!/bin/bash

###############################################################################
# Script: Corrigir CSRF Token Literal no JavaScript
# 
# Problema: {{ csrf_token() }} não está sendo renderizado, fica literal
# Solução: Renderizar o token em uma variável JavaScript antes da função
###############################################################################

set -e

echo "======================================================================"
echo "Corrigindo CSRF Token Literal"
echo "======================================================================"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ ! -f "app.py" ]; then
    echo -e "${RED}Erro: Execute no diretório raiz (/var/www/assessment)${NC}"
    exit 1
fi

BACKUP_DIR="backups/csrf_literal_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp templates/admin/grupos_lista.html "$BACKUP_DIR/"
echo -e "${GREEN}✓ Backup: $BACKUP_DIR${NC}"
echo ""

echo "Aplicando correção..."

# Criar o novo bloco de scripts com CSRF token renderizado FORA da função
cat > /tmp/new_scripts_block.txt << 'ENDOFSCRIPT'
{% block scripts %}
<script>
// Renderizar CSRF token em variável JavaScript
const CSRF_TOKEN = '{{ csrf_token() }}';
console.log('DEBUG: CSRF Token carregado:', CSRF_TOKEN.substring(0, 20) + '...');

function confirmarExclusao(grupoNome, tipoId) {
    console.log('DEBUG: confirmarExclusao chamada');
    console.log('  - Grupo:', grupoNome);
    console.log('  - Tipo ID:', tipoId);
    
    if (confirm(`Tem certeza que deseja excluir o grupo "${grupoNome}"?\n\nEsta ação é irreversível e excluirá TODOS os assessments públicos deste grupo!`)) {
        console.log('DEBUG: Usuário confirmou exclusão');
        
        // Criar formulário
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/grupos/${encodeURIComponent(grupoNome)}/${tipoId}/delete`;
        
        console.log('DEBUG: Action URL:', form.action);
        
        // Adicionar CSRF token usando a variável renderizada
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrf_token';
        csrfInput.value = CSRF_TOKEN;  // Usar variável em vez de template literal
        form.appendChild(csrfInput);
        
        console.log('DEBUG: CSRF token adicionado ao form');
        
        document.body.appendChild(form);
        console.log('DEBUG: Submetendo formulário...');
        form.submit();
    } else {
        console.log('DEBUG: Usuário cancelou');
    }
}

console.log('DEBUG: Script carregado, função disponível:', typeof confirmarExclusao);
</script>
{% endblock %}
ENDOFSCRIPT

# Substituir o bloco completo
python3 << 'ENDOFPYTHON'
import re

# Ler o arquivo
with open('templates/admin/grupos_lista.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Ler o novo bloco
with open('/tmp/new_scripts_block.txt', 'r', encoding='utf-8') as f:
    new_block = f.read()

# Substituir o bloco de scripts
pattern = r'{% block scripts %}.*?{% endblock %}'
content = re.sub(pattern, new_block.strip(), content, flags=re.DOTALL)

# Salvar
with open('templates/admin/grupos_lista.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Template atualizado com sucesso")
ENDOFPYTHON

echo -e "${GREEN}✓ Correção aplicada${NC}"
echo ""

echo "Reiniciando serviço..."
if command -v supervisorctl &> /dev/null; then
    sudo supervisorctl restart assessment
    echo -e "${GREEN}✓ Reiniciado via Supervisor${NC}"
elif [ -f "/etc/systemd/system/assessment.service" ]; then
    sudo systemctl restart assessment
    echo -e "${GREEN}✓ Reiniciado via Systemd${NC}"
fi

echo ""
echo "======================================================================"
echo -e "${GREEN}✓ CSRF Token Corrigido!${NC}"
echo "======================================================================"
echo ""
echo -e "${YELLOW}TESTE AGORA:${NC}"
echo ""
echo "1. Limpe o cache do navegador (Ctrl+Shift+R)"
echo "2. Acesse /admin/grupos"
echo "3. Abra o Console (F12)"
echo "4. Você deve ver: 'DEBUG: CSRF Token carregado: ...' (com valor real)"
echo "5. Clique em 'Excluir'"
echo "6. Agora DEVE funcionar!"
echo ""
echo "💾 Backup: $BACKUP_DIR"
echo ""
