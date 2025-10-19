#!/bin/bash

###############################################################################
# Script: Auto-Refresh nas Estatísticas de Grupos
# 
# Funcionalidades adicionadas:
# 1. Rota API: /admin/grupos/<grupo>/api (retorna JSON)
# 2. Auto-refresh a cada 5 segundos via AJAX
# 3. Atualiza estatísticas, gráficos e tabela sem recarregar página
# 4. Mantém tipo de visualização selecionado (barras, radar, tabela)
# 5. Inclui rótulos de valores nos gráficos de barras
#
# Data: 2025-10-17
###############################################################################

set -e  # Parar em caso de erro

echo "======================================================================"
echo "Aplicar Auto-Refresh nas Estatísticas de Grupos (5 segundos)"
echo "======================================================================"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detectar diretório do projeto
if [ -f "app.py" ]; then
    PROJECT_DIR=$(pwd)
else
    echo -e "${RED}Erro: Execute este script no diretório raiz do projeto (onde está o app.py)${NC}"
    exit 1
fi

echo "📁 Diretório do projeto: $PROJECT_DIR"
echo ""

# Criar backup
BACKUP_DIR="backups/autorefresh_grupos_$(date +%Y%m%d_%H%M%S)"
echo "💾 Criando backup em: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"
cp routes/admin.py "$BACKUP_DIR/" 2>/dev/null || true
cp templates/admin/grupos_estatisticas.html "$BACKUP_DIR/" 2>/dev/null || true
echo -e "${GREEN}✓ Backup criado${NC}"
echo ""

echo "🔄 Puxando últimas atualizações do repositório..."
git pull origin main

echo ""
echo "🔄 Reiniciando serviço..."
if command -v supervisorctl &> /dev/null; then
    sudo supervisorctl restart assessment
    echo -e "${GREEN}✓ Serviço reiniciado via Supervisor${NC}"
elif [ -f "/etc/systemd/system/assessment.service" ]; then
    sudo systemctl restart assessment
    echo -e "${GREEN}✓ Serviço reiniciado via Systemd${NC}"
else
    echo -e "${YELLOW}⚠ Serviço não detectado. Reinicie manualmente:${NC}"
    echo "   sudo supervisorctl restart assessment"
    echo "   ou"
    echo "   sudo systemctl restart assessment"
fi

echo ""
echo "======================================================================"
echo -e "${GREEN}✓ Auto-Refresh aplicado com sucesso!${NC}"
echo "======================================================================"
echo ""
echo "📝 Funcionalidades adicionadas:"
echo "   ✅ Rota API: /admin/grupos/<grupo>/api"
echo "   ✅ Auto-refresh a cada 5 segundos (AJAX)"
echo "   ✅ Atualiza estatísticas em tempo real"
echo "   ✅ Atualiza gráficos automaticamente"
echo "   ✅ Atualiza tabela automaticamente"
echo "   ✅ Mantém visualização selecionada"
echo "   ✅ Rótulos de valores nas barras"
echo ""
echo "💾 Backup salvo em: $BACKUP_DIR"
echo ""
echo "🧪 Como testar:"
echo "   1. Acesse /admin/grupos e clique em qualquer grupo"
echo "   2. Deixe a página aberta"
echo "   3. A cada 5 segundos, os dados são atualizados automaticamente"
echo "   4. Novos assessments aparecem sem recarregar a página"
echo "   5. Selecione barras horizontais/verticais/radar - mantém ao atualizar"
echo ""
echo "💡 Dica: Abra o Console do Navegador (F12) para ver logs de atualização"
echo ""
