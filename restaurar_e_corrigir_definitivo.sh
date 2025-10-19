#!/bin/bash

###############################################################################
# Script: Restaurar Backup e Aplicar Correção Definitiva
# 
# Este script:
# 1. Restaura o último backup funcional
# 2. Aplica a correção correta do bloco extra_js
###############################################################################

set -e

echo "======================================================================"
echo "Restaurar e Corrigir - DEFINITIVO"
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

echo -e "${YELLOW}PASSO 1: Encontrar e restaurar último backup FUNCIONAL${NC}"
echo ""

# Procurar o backup mais antigo (antes das correções com erro)
BACKUP_FUNCIONAL=$(ls -t backups/csrf_literal_*/grupos_lista.html 2>/dev/null | tail -1)

if [ -z "$BACKUP_FUNCIONAL" ]; then
    # Tentar outro backup
    BACKUP_FUNCIONAL=$(ls -t backups/debug_excluir_*/grupos_lista.html 2>/dev/null | tail -1)
fi

if [ -z "$BACKUP_FUNCIONAL" ]; then
    # Tentar outro backup
    BACKUP_FUNCIONAL=$(ls -t backups/excluir_*/grupos_lista.html 2>/dev/null | tail -1)
fi

if [ ! -z "$BACKUP_FUNCIONAL" ]; then
    echo "Restaurando backup: $BACKUP_FUNCIONAL"
    cp "$BACKUP_FUNCIONAL" templates/admin/grupos_lista.html
    echo -e "${GREEN}✓ Backup restaurado${NC}"
else
    echo -e "${RED}✗ Nenhum backup encontrado! Usando arquivo atual.${NC}"
fi
echo ""

echo -e "${YELLOW}PASSO 2: Criar backup do estado atual${NC}"
echo ""
BACKUP_DIR="backups/restauracao_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp templates/admin/grupos_lista.html "$BACKUP_DIR/"
echo -e "${GREEN}✓ Novo backup: $BACKUP_DIR${NC}"
echo ""

echo -e "${YELLOW}PASSO 3: Aplicar correção correta (Python)${NC}"
echo ""

python3 << 'ENDOFPYTHON'
import re

# Ler o arquivo
with open('templates/admin/grupos_lista.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Definir o bloco de scripts correto
new_script_block = """{% block extra_js %}
<script>
// Renderizar CSRF token em variável JavaScript
const CSRF_TOKEN = '{{ csrf_token() }}';
console.log('DEBUG: CSRF Token carregado:', CSRF_TOKEN.substring(0, 20) + '...');

function confirmarExclusao(grupoNome, tipoId) {
    console.log('DEBUG: confirmarExclusao chamada');
    console.log('  - Grupo:', grupoNome);
    console.log('  - Tipo ID:', tipoId);
    
    if (confirm(`Tem certeza que deseja excluir o grupo "${grupoNome}"?\\n\\nEsta ação é irreversível e excluirá TODOS os assessments públicos deste grupo!`)) {
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
{% endblock %}"""

# Remover qualquer bloco de scripts existente ({% block scripts %} ou {% block extra_js %})
# Procurar por qualquer variação
patterns = [
    r'{% block scripts %}.*?{% endblock %}',
    r'{% block extra_js %}.*?{% endblock %}'
]

for pattern in patterns:
    content = re.sub(pattern, '', content, flags=re.DOTALL)

# Adicionar o novo bloco no final, antes do fechamento
# Garantir que há apenas um
if not content.rstrip().endswith('{% endblock %}'):
    content = content.rstrip() + '\n\n' + new_script_block + '\n'
else:
    # Inserir antes do último {% endblock %}
    content = content.rstrip() + '\n\n' + new_script_block + '\n'

# Salvar
with open('templates/admin/grupos_lista.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Template corrigido com sucesso")
print("✓ Bloco extra_js aplicado")
ENDOFPYTHON

echo -e "${GREEN}✓ Correção aplicada${NC}"
echo ""

echo -e "${YELLOW}PASSO 4: Reiniciar serviço${NC}"
echo ""
if command -v supervisorctl &> /dev/null; then
    sudo supervisorctl restart assessment
    echo -e "${GREEN}✓ Reiniciado via Supervisor${NC}"
elif [ -f "/etc/systemd/system/assessment.service" ]; then
    sudo systemctl restart assessment
    echo -e "${GREEN}✓ Reiniciado via Systemd${NC}"
fi

echo ""
echo "======================================================================"
echo -e "${GREEN}✓ CORREÇÃO DEFINITIVA APLICADA!${NC}"
echo "======================================================================"
echo ""
echo -e "${YELLOW}TESTE AGORA:${NC}"
echo ""
echo "1. Limpe o cache (Ctrl+Shift+R)"
echo "2. Acesse /admin/grupos"
echo "3. A página DEVE carregar sem erro 500"
echo "4. Abra o Console (F12)"
echo "5. Você DEVE ver mensagens DEBUG"
echo "6. Clique em 'Excluir' - o diálogo DEVE aparecer"
echo ""
echo "💾 Backups preservados em: backups/"
echo ""
