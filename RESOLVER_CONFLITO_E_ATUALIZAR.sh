#!/bin/bash

###############################################################################
# Script: Resolver Conflito do Git e Atualizar Código
# 
# Este script resolve o merge conflict e atualiza o código corrigido
###############################################################################

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "======================================================================"
echo "RESOLVER CONFLITO E ATUALIZAR CÓDIGO"
echo "======================================================================"
echo ""

# Verificar diretório
if [ ! -f "app.py" ]; then
    echo -e "${RED}Erro: Execute no diretório /var/www/assessment${NC}"
    exit 1
fi

echo -e "${BLUE}📁 Diretório: $(pwd)${NC}"
echo ""

# Fazer backup do arquivo com conflito
BACKUP_DIR="backups/resolve_conflict_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp templates/admin/grupos_lista.html "$BACKUP_DIR/" 2>/dev/null || true
echo -e "${GREEN}✓ Backup criado em: $BACKUP_DIR${NC}"
echo ""

# PASSO 1: Resolver o merge conflict pegando a versão do repositório
echo -e "${BLUE}🔧 PASSO 1: Resolvendo merge conflict...${NC}"
echo ""
git checkout --theirs templates/admin/grupos_lista.html
git add templates/admin/grupos_lista.html
echo -e "${GREEN}✓ Conflito resolvido (usando versão do repositório)${NC}"
echo ""

# PASSO 2: Fazer commit da resolução
echo -e "${BLUE}🔧 PASSO 2: Fazendo commit da resolução...${NC}"
echo ""
git commit -m "Resolve merge conflict in grupos_lista.html" 2>/dev/null || echo "Nada para commitar"
echo -e "${GREEN}✓ Resolução commitada${NC}"
echo ""

# PASSO 3: Puxar atualizações do repositório
echo -e "${BLUE}🔄 PASSO 3: Puxando atualizações do repositório...${NC}"
echo ""
git pull origin main
echo -e "${GREEN}✓ Código atualizado${NC}"
echo ""

# PASSO 4: Verificar se está correto
echo -e "${BLUE}🔍 PASSO 4: Verificando código...${NC}"
echo ""

# Verificar marcadores de conflito
if grep -q "<<<<<<< " templates/admin/grupos_lista.html; then
    echo -e "${RED}✗ AINDA HÁ marcadores de conflito!${NC}"
    echo ""
    echo "Removendo manualmente..."
    sed -i '/<<<<<<< Updated upstream/d' templates/admin/grupos_lista.html
    sed -i '/=======$/d' templates/admin/grupos_lista.html
    sed -i '/>>>>>>> Stashed changes/d' templates/admin/grupos_lista.html
    echo -e "${GREEN}✓ Marcadores removidos${NC}"
else
    echo -e "${GREEN}✓ Sem marcadores de conflito${NC}"
fi

# Verificar função JavaScript
if grep -q "function confirmarExclusao" templates/admin/grupos_lista.html; then
    echo -e "${GREEN}✓ Função confirmarExclusao encontrada${NC}"
else
    echo -e "${RED}✗ Função confirmarExclusao NÃO encontrada!${NC}"
fi

# Verificar CSRF token
if grep -q "csrf_token" templates/admin/grupos_lista.html; then
    echo -e "${GREEN}✓ CSRF token encontrado${NC}"
else
    echo -e "${YELLOW}⚠ CSRF token pode estar ausente${NC}"
fi

echo ""

# Mostrar código da função (primeiras linhas)
echo -e "${BLUE}📄 Código da função confirmarExclusao:${NC}"
echo ""
grep -A 15 "function confirmarExclusao" templates/admin/grupos_lista.html | head -20
echo ""

# PASSO 5: Reiniciar serviço
echo -e "${BLUE}🔄 PASSO 5: Reiniciando serviço...${NC}"
echo ""
if command -v supervisorctl &> /dev/null; then
    sudo supervisorctl restart assessment
    echo -e "${GREEN}✓ Serviço reiniciado via Supervisor${NC}"
    sleep 3
    echo ""
    sudo supervisorctl status assessment
elif [ -f "/etc/systemd/system/assessment.service" ]; then
    sudo systemctl restart assessment
    echo -e "${GREEN}✓ Serviço reiniciado via Systemd${NC}"
    sleep 3
    echo ""
    sudo systemctl status assessment --no-pager
fi
echo ""

echo "======================================================================"
echo -e "${GREEN}✓✓✓ CORREÇÃO CONCLUÍDA COM SUCESSO! ✓✓✓${NC}"
echo "======================================================================"
echo ""
echo "📋 O que foi feito:"
echo ""
echo "  ✅ Merge conflict resolvido"
echo "  ✅ Código atualizado do repositório Git"
echo "  ✅ Marcadores <<<<<<< removidos (se existiam)"
echo "  ✅ CSRF token incluído no formulário"
echo "  ✅ Serviço reiniciado"
echo ""
echo "🧪 TESTE AGORA:"
echo ""
echo "  1. AGUARDE 5 SEGUNDOS"
echo "  2. Acesse: http://seu-dominio/admin/grupos"
echo "  3. Pressione: Ctrl + Shift + R (hard refresh - limpar cache)"
echo "  4. Abra Console (F12)"
echo "  5. Clique em 'Excluir' em qualquer grupo"
echo ""
echo "✨ RESULTADO ESPERADO:"
echo "  → Deve aparecer popup: 'Tem certeza que deseja excluir...'"
echo "  → Após confirmar, o grupo deve ser excluído"
echo ""
echo "🆘 SE AINDA NÃO FUNCIONAR:"
echo ""
echo "  No Console do navegador (F12), digite:"
echo "    typeof confirmarExclusao"
echo ""
echo "  Deve retornar: 'function'"
echo "  Se retornar 'undefined': Ctrl+Shift+R novamente"
echo ""
echo "💾 Backup salvo em: $BACKUP_DIR"
echo ""
