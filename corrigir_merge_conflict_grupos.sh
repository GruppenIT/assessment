#!/bin/bash

###############################################################################
# Script: Correção de Merge Conflict - Botão Excluir Grupos
# 
# Problema identificado:
# - Arquivo templates/admin/grupos_lista.html tem marcadores de conflito do Git
# - Isso quebra o JavaScript e impede a função confirmarExclusao de funcionar
# - CSRF token está ausente no formulário dinâmico
###############################################################################

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "======================================================================"
echo "Correção: Merge Conflict - Botão Excluir Grupos"
echo "======================================================================"
echo ""

# Verificar diretório
if [ ! -f "app.py" ]; then
    echo -e "${RED}Erro: Execute no diretório raiz do projeto (/var/www/assessment)${NC}"
    exit 1
fi

echo -e "${BLUE}📁 Diretório: $(pwd)${NC}"
echo ""

# Fazer backup
BACKUP_DIR="backups/fix_merge_conflict_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp templates/admin/grupos_lista.html "$BACKUP_DIR/" 2>/dev/null || true
echo -e "${GREEN}✓ Backup criado em: $BACKUP_DIR${NC}"
echo ""

# Resolver conflito pegando a versão do repositório
echo -e "${BLUE}🔧 Resolvendo merge conflict...${NC}"
git checkout --theirs templates/admin/grupos_lista.html
git add templates/admin/grupos_lista.html
echo -e "${GREEN}✓ Merge conflict resolvido${NC}"
echo ""

# Puxar última versão do repositório
echo -e "${BLUE}🔄 Puxando última versão do repositório...${NC}"
git pull origin main
echo -e "${GREEN}✓ Código atualizado${NC}"
echo ""

# Verificar se a correção funcionou
echo -e "${BLUE}🔍 Verificando código...${NC}"
echo ""

if grep -q "<<<<<<< " templates/admin/grupos_lista.html; then
    echo -e "${RED}✗ AINDA HÁ marcadores de conflito no arquivo!${NC}"
    echo "Tentando corrigir manualmente..."
    
    # Remover marcadores de conflito manualmente
    sed -i '/<<<<<<< Updated upstream/d' templates/admin/grupos_lista.html
    sed -i '/=======$/d' templates/admin/grupos_lista.html
    sed -i '/>>>>>>> Stashed changes/d' templates/admin/grupos_lista.html
    
    echo -e "${GREEN}✓ Marcadores removidos${NC}"
else
    echo -e "${GREEN}✓ Sem marcadores de conflito${NC}"
fi

if grep -q "function confirmarExclusao" templates/admin/grupos_lista.html; then
    echo -e "${GREEN}✓ Função confirmarExclusao encontrada${NC}"
else
    echo -e "${RED}✗ Função confirmarExclusao NÃO encontrada!${NC}"
fi

if grep -q "csrf_token" templates/admin/grupos_lista.html; then
    echo -e "${GREEN}✓ CSRF token encontrado${NC}"
else
    echo -e "${YELLOW}⚠ CSRF token pode estar ausente${NC}"
fi
echo ""

# Reiniciar serviço
echo -e "${BLUE}🔄 Reiniciando serviço...${NC}"
if command -v supervisorctl &> /dev/null; then
    sudo supervisorctl restart assessment
    echo -e "${GREEN}✓ Serviço reiniciado via Supervisor${NC}"
    sleep 2
    echo ""
    echo "Status:"
    sudo supervisorctl status assessment
elif [ -f "/etc/systemd/system/assessment.service" ]; then
    sudo systemctl restart assessment
    echo -e "${GREEN}✓ Serviço reiniciado via Systemd${NC}"
    sleep 2
    echo ""
    echo "Status:"
    sudo systemctl status assessment --no-pager -l
fi
echo ""

echo "======================================================================"
echo -e "${GREEN}✓ Correção concluída!${NC}"
echo "======================================================================"
echo ""
echo "📋 O que foi corrigido:"
echo ""
echo "  ✅ Merge conflict resolvido"
echo "  ✅ Marcadores <<<<<<< removidos do JavaScript"
echo "  ✅ Código atualizado do repositório"
echo "  ✅ Serviço reiniciado"
echo ""
echo "🧪 TESTE AGORA:"
echo ""
echo "  1. Acesse: http://seu-dominio/admin/grupos"
echo "  2. Abra o Console (F12)"
echo "  3. Clique em 'Excluir' em qualquer grupo"
echo "  4. Deve aparecer popup de confirmação"
echo ""
echo "Se AINDA não funcionar:"
echo ""
echo "  1. No Console do navegador (F12), digite:"
echo "     typeof confirmarExclusao"
echo ""
echo "  2. Deve retornar: 'function'"
echo ""
echo "  3. Se retornar 'undefined', pressione Ctrl+Shift+R (hard refresh)"
echo ""
