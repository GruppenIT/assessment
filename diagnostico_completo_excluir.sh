#!/bin/bash

###############################################################################
# Diagnóstico Completo - Por que Excluir não funciona
###############################################################################

set -e

echo "======================================================================"
echo "DIAGNÓSTICO COMPLETO - Botão Excluir"
echo "======================================================================"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== 1. VERIFICANDO TEMPLATE ATUAL ===${NC}"
echo ""
echo "Bloco de scripts no template:"
echo "---------------------------------------------------------------------"
grep -A 40 "{% block scripts %}" templates/admin/grupos_lista.html
echo "---------------------------------------------------------------------"
echo ""

echo -e "${BLUE}=== 2. VERIFICANDO SE CSRF_TOKEN ESTÁ RENDERIZADO ===${NC}"
echo ""
if grep -q "const CSRF_TOKEN = '{{ csrf_token()" templates/admin/grupos_lista.html; then
    echo -e "${GREEN}✓ CSRF_TOKEN definido como constante (CORRETO)${NC}"
else
    echo -e "${RED}✗ CSRF_TOKEN NÃO encontrado como constante${NC}"
    if grep -q "csrf_token()" templates/admin/grupos_lista.html; then
        echo -e "${YELLOW}⚠ csrf_token() encontrado, mas pode estar dentro de string literal${NC}"
    fi
fi
echo ""

echo -e "${BLUE}=== 3. VERIFICANDO ROTA NO SERVIDOR ===${NC}"
echo ""
echo "Rota de exclusão registrada:"
grep -B 3 -A 20 "def excluir_grupo" routes/admin.py | head -25
echo ""

echo -e "${BLUE}=== 4. TESTANDO SE ROTA RESPONDE ===${NC}"
echo ""
echo "Digite o nome de um grupo que existe para testar (ou Enter para pular):"
read -r GRUPO_TESTE
if [ ! -z "$GRUPO_TESTE" ]; then
    echo "Digite o tipo_id deste grupo:"
    read -r TIPO_TESTE
    
    echo ""
    echo "Testando rota: /admin/grupos/$GRUPO_TESTE/$TIPO_TESTE/delete"
    echo ""
    
    # Tentar ver se a rota existe (sem fazer DELETE de verdade)
    flask routes 2>/dev/null | grep -i "grupos.*delete" || echo "Comando 'flask routes' não disponível"
fi
echo ""

echo -e "${BLUE}=== 5. VERIFICANDO LOGS RECENTES ===${NC}"
echo ""
echo "Últimas 20 linhas do log de erro:"
if [ -f "/var/log/supervisor/assessment-stderr.log" ]; then
    tail -20 /var/log/supervisor/assessment-stderr.log
elif journalctl -u assessment -n 20 --no-pager &>/dev/null; then
    journalctl -u assessment -n 20 --no-pager
else
    echo "Não foi possível acessar os logs"
fi
echo ""

echo -e "${BLUE}=== 6. VERIFICANDO SE APP ESTÁ RODANDO ===${NC}"
echo ""
if supervisorctl status assessment 2>/dev/null | grep -q RUNNING; then
    echo -e "${GREEN}✓ Serviço RUNNING (Supervisor)${NC}"
    supervisorctl status assessment
elif systemctl is-active --quiet assessment 2>/dev/null; then
    echo -e "${GREEN}✓ Serviço ACTIVE (Systemd)${NC}"
    systemctl status assessment --no-pager -l
else
    echo -e "${RED}✗ Serviço não encontrado ou não está rodando${NC}"
fi
echo ""

echo "======================================================================"
echo "PRÓXIMOS PASSOS"
echo "======================================================================"
echo ""
echo -e "${YELLOW}ENVIE PARA O DESENVOLVEDOR:${NC}"
echo ""
echo "1. A saída completa deste script"
echo ""
echo "2. Screenshot ou texto do Console do navegador (F12) mostrando:"
echo "   - Todas as mensagens DEBUG"
echo "   - Qualquer erro em vermelho"
echo ""
echo "3. Responda:"
echo "   - Ao clicar em Excluir, aparece o diálogo de confirmação?"
echo "   - Ao confirmar, a página recarrega ou não acontece nada?"
echo "   - Aparece alguma mensagem flash (verde/vermelha) no topo?"
echo ""
