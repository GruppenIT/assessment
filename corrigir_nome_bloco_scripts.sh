#!/bin/bash

###############################################################################
# Script: Corrigir Nome do Bloco de Scripts
# 
# Problema: Template usa {% block scripts %} mas base.html tem {% block extra_js %}
# Solução: Renomear para {% block extra_js %} no grupos_lista.html
###############################################################################

set -e

echo "======================================================================"
echo "Corrigindo Nome do Bloco de Scripts"
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

BACKUP_DIR="backups/bloco_scripts_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp templates/admin/grupos_lista.html "$BACKUP_DIR/"
echo -e "${GREEN}✓ Backup: $BACKUP_DIR${NC}"
echo ""

echo "Aplicando correção..."

# Substituir {% block scripts %} por {% block extra_js %}
sed -i 's/{% block scripts %}/{% block extra_js %}/g' templates/admin/grupos_lista.html

echo -e "${GREEN}✓ Bloco renomeado de 'scripts' para 'extra_js'${NC}"
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
echo -e "${GREEN}✓ Correção Aplicada com Sucesso!${NC}"
echo "======================================================================"
echo ""
echo -e "${YELLOW}TESTE AGORA:${NC}"
echo ""
echo "1. Limpe o cache do navegador (Ctrl+Shift+R)"
echo "2. Acesse /admin/grupos"
echo "3. Abra o Console (F12)"
echo "4. Você DEVE ver:"
echo "   DEBUG: CSRF Token carregado: ..."
echo "   DEBUG: Script carregado, função disponível: function"
echo ""
echo "5. Clique em 'Excluir'"
echo "6. AGORA o diálogo de confirmação DEVE aparecer!"
echo "7. Confirme e o grupo será excluído"
echo ""
echo "💾 Backup: $BACKUP_DIR"
echo ""
