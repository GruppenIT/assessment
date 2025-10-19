#!/bin/bash

###############################################################################
# Script: Diagnosticar Erro 500 na página /admin/grupos
###############################################################################

set -e

echo "======================================================================"
echo "DIAGNOSTICANDO ERRO 500"
echo "======================================================================"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}1. VERIFICANDO LOGS DE ERRO${NC}"
echo ""
if [ -f "/var/log/supervisor/assessment-stderr.log" ]; then
    echo "Últimas 50 linhas do log de erro:"
    echo "---------------------------------------------------------------------"
    tail -50 /var/log/supervisor/assessment-stderr.log
    echo "---------------------------------------------------------------------"
elif journalctl -u assessment -n 50 --no-pager &>/dev/null; then
    echo "Últimas 50 linhas do log (journalctl):"
    echo "---------------------------------------------------------------------"
    journalctl -u assessment -n 50 --no-pager
    echo "---------------------------------------------------------------------"
fi
echo ""

echo -e "${YELLOW}2. VERIFICANDO TEMPLATE grupos_lista.html${NC}"
echo ""
echo "Última linha do template:"
tail -5 templates/admin/grupos_lista.html
echo ""

echo -e "${YELLOW}3. CONTANDO BLOCOS NO TEMPLATE${NC}"
echo ""
echo "{% block extra_js %} = $(grep -c '{% block extra_js %}' templates/admin/grupos_lista.html 2>/dev/null || echo 0)"
echo "{% endblock %} = $(grep -c '{% endblock %}' templates/admin/grupos_lista.html 2>/dev/null || echo 0)"
echo ""

echo "======================================================================"
echo ""
echo -e "${RED}SE O ERRO PERSISTIR, EXECUTE:${NC}"
echo ""
echo "cd /var/www/assessment"
echo "# Restaurar o último backup:"
echo "ULTIMO_BACKUP=\$(ls -t backups/bloco_scripts_* 2>/dev/null | head -1)"
echo "if [ ! -z \"\$ULTIMO_BACKUP\" ]; then"
echo "  cp \"\$ULTIMO_BACKUP/grupos_lista.html\" templates/admin/"
echo "  sudo supervisorctl restart assessment"
echo "  echo 'Backup restaurado!'"
echo "fi"
echo ""
