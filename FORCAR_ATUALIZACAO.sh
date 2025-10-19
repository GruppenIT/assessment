#!/bin/bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "======================================================================"
echo "FORÇAR ATUALIZAÇÃO DO CÓDIGO"
echo "======================================================================"
echo ""

if [ ! -f "app.py" ]; then
    echo -e "${RED}Erro: Execute no diretório /var/www/assessment${NC}"
    exit 1
fi

# Backup
BACKUP_DIR="backups/force_update_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp templates/admin/grupos_lista.html "$BACKUP_DIR/"
echo -e "${GREEN}✓ Backup: $BACKUP_DIR${NC}"
echo ""

# Configurar estratégia de merge
echo -e "${BLUE}🔧 Configurando Git...${NC}"
git config pull.rebase false
echo -e "${GREEN}✓ Git configurado${NC}"
echo ""

# Resetar para versão do repositório
echo -e "${BLUE}🔧 Resetando para versão remota...${NC}"
git fetch origin
git reset --hard origin/main
echo -e "${GREEN}✓ Código resetado para versão remota${NC}"
echo ""

# Mostrar conteúdo do arquivo
echo "======================================================================"
echo -e "${BLUE}📄 CONTEÚDO DO ARQUIVO (função JavaScript):${NC}"
echo "======================================================================"
echo ""
grep -A 20 "function confirmarExclusao" templates/admin/grupos_lista.html || echo -e "${RED}FUNÇÃO NÃO ENCONTRADA!${NC}"
echo ""
echo "======================================================================"
echo ""

# Verificar
echo -e "${BLUE}🔍 Verificações:${NC}"
echo ""

if grep -q "<<<<<<< " templates/admin/grupos_lista.html; then
    echo -e "${RED}✗ AINDA HÁ marcadores de conflito!${NC}"
else
    echo -e "${GREEN}✓ Sem marcadores de conflito${NC}"
fi

if grep -q "function confirmarExclusao" templates/admin/grupos_lista.html; then
    echo -e "${GREEN}✓ Função confirmarExclusao existe${NC}"
else
    echo -e "${RED}✗ Função confirmarExclusao NÃO existe!${NC}"
fi

if grep -q "csrf_token()" templates/admin/grupos_lista.html; then
    echo -e "${GREEN}✓ CSRF token existe${NC}"
else
    echo -e "${RED}✗ CSRF token NÃO existe!${NC}"
fi

if grep -q "onclick.*confirmarExclusao" templates/admin/grupos_lista.html; then
    echo -e "${GREEN}✓ Botão com onclick existe${NC}"
    echo ""
    echo "Código do botão:"
    grep -B 1 -A 3 "onclick.*confirmarExclusao" templates/admin/grupos_lista.html
else
    echo -e "${RED}✗ Botão com onclick NÃO existe!${NC}"
fi
echo ""

# Reiniciar
echo -e "${BLUE}🔄 Reiniciando serviço...${NC}"
if command -v supervisorctl &> /dev/null; then
    sudo supervisorctl restart assessment
    sleep 3
    sudo supervisorctl status assessment
else
    sudo systemctl restart assessment
    sleep 3
    sudo systemctl status assessment --no-pager
fi
echo ""

echo "======================================================================"
echo -e "${GREEN}✓✓✓ ATUALIZAÇÃO FORÇADA CONCLUÍDA! ✓✓✓${NC}"
echo "======================================================================"
echo ""
echo "🧪 TESTE NO NAVEGADOR (IMPORTANTE):"
echo ""
echo "  1. AGUARDE 10 SEGUNDOS antes de testar"
echo ""
echo "  2. Abra /admin/grupos em ABA ANÔNIMA ou:"
echo "     - Chrome: Ctrl+Shift+N"
echo "     - Firefox: Ctrl+Shift+P"
echo ""
echo "  3. OU limpe o cache:"
echo "     - Pressione F12"
echo "     - Clique com botão direito no ícone de reload"
echo "     - Selecione 'Empty Cache and Hard Reload'"
echo ""
echo "  4. Abra Console (F12) e digite:"
echo "     typeof confirmarExclusao"
echo ""
echo "     Deve retornar: 'function'"
echo ""
echo "  5. Se retornar 'undefined', o JavaScript não carregou"
echo "     Veja o código-fonte (Ctrl+U) e procure 'confirmarExclusao'"
echo ""
echo "  6. Clique em 'Excluir' e veja se aparece popup"
echo ""
echo "📋 SE AINDA NÃO APARECER O POPUP:"
echo ""
echo "  Envie para mim:"
echo "  - O que aparece ao digitar: typeof confirmarExclusao"
echo "  - Screenshot do Console (F12) após clicar em Excluir"
echo "  - Se há algum erro no Console"
echo ""
