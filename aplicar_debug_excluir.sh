#!/bin/bash

###############################################################################
# Script: Aplicar Versão DEBUG do Botão Excluir
# 
# Adiciona logs detalhados no console para diagnosticar o problema
###############################################################################

set -e

echo "======================================================================"
echo "Aplicando Versão DEBUG do Botão Excluir"
echo "======================================================================"
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Verificar diretório
if [ ! -f "app.py" ]; then
    echo -e "${RED}Erro: Execute no diretório raiz (/var/www/assessment)${NC}"
    exit 1
fi

# Backup
BACKUP_DIR="backups/debug_excluir_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp templates/admin/grupos_lista.html "$BACKUP_DIR/"
echo -e "${GREEN}✓ Backup: $BACKUP_DIR${NC}"
echo ""

# Criar versão DEBUG do script
cat > /tmp/debug_script.js << 'EOF'
function confirmarExclusao(grupoNome, tipoId) {
    console.log('========================================');
    console.log('DEBUG: Função confirmarExclusao CHAMADA');
    console.log('Grupo:', grupoNome);
    console.log('Tipo ID:', tipoId);
    console.log('========================================');
    
    if (confirm(`Tem certeza que deseja excluir o grupo "${grupoNome}"?\n\nEsta ação é irreversível e excluirá TODOS os assessments públicos deste grupo!`)) {
        console.log('DEBUG: Usuário CONFIRMOU a exclusão');
        
        // Criar formulário
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/grupos/${encodeURIComponent(grupoNome)}/${tipoId}/delete`;
        
        console.log('DEBUG: Formulário criado');
        console.log('Action:', form.action);
        console.log('Method:', form.method);
        
        // Adicionar CSRF token
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrf_token';
        csrfInput.value = '{{ csrf_token() }}';
        form.appendChild(csrfInput);
        
        console.log('DEBUG: CSRF token adicionado');
        console.log('Token value:', csrfInput.value);
        
        document.body.appendChild(form);
        console.log('DEBUG: Formulário anexado ao body');
        console.log('DEBUG: Submetendo formulário...');
        
        form.submit();
        
        console.log('DEBUG: form.submit() executado');
    } else {
        console.log('DEBUG: Usuário CANCELOU a exclusão');
    }
}

// Testar se a função está acessível
console.log('DEBUG: Script carregado. Função confirmarExclusao disponível:', typeof confirmarExclusao);
EOF

echo "Atualizando template com versão DEBUG..."

# Substituir o bloco de scripts
sed -i.old '/{% block scripts %}/,/{% endblock %}/c\
{% block scripts %}\
<script>\
function confirmarExclusao(grupoNome, tipoId) {\
    console.log('\''========================================'\'');\
    console.log('\''DEBUG: Função confirmarExclusao CHAMADA'\'');\
    console.log('\''Grupo:'\'', grupoNome);\
    console.log('\''Tipo ID:'\'', tipoId);\
    console.log('\''========================================'\'');\
    \
    if (confirm(`Tem certeza que deseja excluir o grupo "${grupoNome}"?\\n\\nEsta ação é irreversível e excluirá TODOS os assessments públicos deste grupo!`)) {\
        console.log('\''DEBUG: Usuário CONFIRMOU a exclusão'\'');\
        \
        const form = document.createElement('\''form'\'');\
        form.method = '\''POST'\'';\
        form.action = `/admin/grupos/${encodeURIComponent(grupoNome)}/${tipoId}/delete`;\
        \
        console.log('\''DEBUG: Formulário criado'\'');\
        console.log('\''Action:'\'', form.action);\
        console.log('\''Method:'\'', form.method);\
        \
        const csrfInput = document.createElement('\''input'\'');\
        csrfInput.type = '\''hidden'\'';\
        csrfInput.name = '\''csrf_token'\'';\
        csrfInput.value = '\''{{ csrf_token() }}'\'';\
        form.appendChild(csrfInput);\
        \
        console.log('\''DEBUG: CSRF token adicionado'\'');\
        console.log('\''Token value:'\'', csrfInput.value);\
        \
        document.body.appendChild(form);\
        console.log('\''DEBUG: Formulário anexado ao body'\'');\
        console.log('\''DEBUG: Submetendo formulário...'\'');\
        \
        form.submit();\
        \
        console.log('\''DEBUG: form.submit() executado'\'');\
    } else {\
        console.log('\''DEBUG: Usuário CANCELOU a exclusão'\'');\
    }\
}\
\
console.log('\''DEBUG: Script carregado. Função confirmarExclusao disponível:'\'', typeof confirmarExclusao);\
</script>\
{% endblock %}' templates/admin/grupos_lista.html

echo -e "${GREEN}✓ Versão DEBUG aplicada${NC}"
echo ""

# Reiniciar
echo "Reiniciando serviço..."
if command -v supervisorctl &> /dev/null; then
    sudo supervisorctl restart assessment
elif [ -f "/etc/systemd/system/assessment.service" ]; then
    sudo systemctl restart assessment
fi

echo ""
echo "======================================================================"
echo -e "${GREEN}✓ Versão DEBUG ativada!${NC}"
echo "======================================================================"
echo ""
echo -e "${YELLOW}INSTRUÇÕES DE TESTE:${NC}"
echo ""
echo "1. Limpe o cache do navegador (Ctrl+Shift+R)"
echo "2. Acesse /admin/grupos"
echo "3. Abra o Console (F12 → aba Console)"
echo "4. Você deve ver: 'DEBUG: Script carregado...'"
echo "5. Clique em 'Excluir' em um grupo"
echo "6. Verifique as mensagens DEBUG no console"
echo ""
echo -e "${YELLOW}O que cada mensagem significa:${NC}"
echo ""
echo "✓ 'Script carregado' = JavaScript foi carregado"
echo "✓ 'Função CHAMADA' = Botão funcionou"
echo "✓ 'CONFIRMOU' = Usuário clicou OK"
echo "✓ 'Formulário criado' = Form gerado com sucesso"
echo "✓ 'form.submit()' = Tentou enviar"
echo ""
echo "Se você NÃO vir 'Script carregado' = problema no template"
echo "Se você NÃO vir 'Função CHAMADA' ao clicar = problema no onclick"
echo "Se você vir 'form.submit()' mas nada acontece = problema no servidor"
echo ""
