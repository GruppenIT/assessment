#!/bin/bash

###############################################################################
# Script: Correção do Bug da Tabela no Auto-Refresh
# 
# Bug corrigido:
# - Ao selecionar modo tabela, o auto-refresh desformatava a tabela
# - Barra de progresso desaparecia
# - Badges estavam incorretos
#
# Solução:
# - JavaScript de atualização agora replica exatamente o HTML original
# - Mantém todas as classes CSS e formatação Bootstrap
#
# Data: 2025-10-17
###############################################################################

set -e

echo "======================================================================"
echo "Correção: Bug da Tabela no Auto-Refresh"
echo "======================================================================"
echo ""

# Cores
GREEN='\033[0;32m'
NC='\033[0m'

# Verificar diretório
if [ ! -f "app.py" ]; then
    echo "Erro: Execute no diretório raiz do projeto"
    exit 1
fi

echo "📁 Diretório: $(pwd)"
echo ""

# Criar backup
BACKUP_DIR="backups/bug_tabela_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp templates/admin/grupos_estatisticas.html "$BACKUP_DIR/"
echo -e "${GREEN}✓ Backup criado em: $BACKUP_DIR${NC}"
echo ""

# Puxar correção do Git
echo "🔄 Puxando correção do repositório..."
git pull origin main

echo ""
echo "🔄 Reiniciando serviço..."
if command -v supervisorctl &> /dev/null; then
    sudo supervisorctl restart assessment
    echo -e "${GREEN}✓ Serviço reiniciado via Supervisor${NC}"
elif [ -f "/etc/systemd/system/assessment.service" ]; then
    sudo systemctl restart assessment
    echo -e "${GREEN}✓ Serviço reiniciado via Systemd${NC}"
fi

echo ""
echo "======================================================================"
echo -e "${GREEN}✓ Bug da tabela corrigido!${NC}"
echo "======================================================================"
echo ""
echo "🐛 Bug corrigido:"
echo "   - Barra de progresso agora se mantém no auto-refresh"
echo "   - Formatação correta (h5, badges, cores)"
echo "   - Classes CSS preservadas"
echo ""
echo "🧪 Teste:"
echo "   1. Acesse /admin/grupos/<seu_grupo>"
echo "   2. Clique em 'Tabela'"
echo "   3. Aguarde o auto-refresh (5-10s)"
echo "   4. A barra de progresso deve se manter formatada"
echo ""
