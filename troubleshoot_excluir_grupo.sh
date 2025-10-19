#!/bin/bash

###############################################################################
# Script: Troubleshooting do Botão Excluir Grupo
# 
# Este script diagnostica por que o botão "Excluir" não está funcionando
###############################################################################

set -e

echo "======================================================================"
echo "TROUBLESHOOTING: Botão Excluir Grupo"
echo "======================================================================"
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 1. Verificar se o arquivo existe
echo -e "${BLUE}[1/6] Verificando arquivo do template...${NC}"
if [ -f "templates/admin/grupos_lista.html" ]; then
    echo -e "${GREEN}✓ Arquivo encontrado${NC}"
else
    echo -e "${RED}✗ Arquivo NÃO encontrado${NC}"
    exit 1
fi
echo ""

# 2. Verificar se a função JavaScript existe
echo -e "${BLUE}[2/6] Verificando função JavaScript confirmarExclusao...${NC}"
if grep -q "function confirmarExclusao" templates/admin/grupos_lista.html; then
    echo -e "${GREEN}✓ Função JavaScript encontrada${NC}"
    echo ""
    echo "Código da função:"
    grep -A 15 "function confirmarExclusao" templates/admin/grupos_lista.html
else
    echo -e "${RED}✗ Função JavaScript NÃO encontrada${NC}"
fi
echo ""

# 3. Verificar se tem CSRF token
echo -e "${BLUE}[3/6] Verificando CSRF token no JavaScript...${NC}"
if grep -q "csrf_token" templates/admin/grupos_lista.html; then
    echo -e "${GREEN}✓ CSRF token encontrado no código${NC}"
else
    echo -e "${RED}✗ CSRF token NÃO encontrado - ESTE É O PROBLEMA!${NC}"
fi
echo ""

# 4. Verificar se a rota está registrada
echo -e "${BLUE}[4/6] Verificando rota de exclusão em routes/admin.py...${NC}"
if grep -q "def excluir_grupo" routes/admin.py; then
    echo -e "${GREEN}✓ Função excluir_grupo encontrada${NC}"
    
    # Verificar se a rota está decorada corretamente
    if grep -B 3 "def excluir_grupo" routes/admin.py | grep -q "@admin_bp.route"; then
        echo -e "${GREEN}✓ Rota registrada corretamente${NC}"
        echo ""
        echo "Decorador da rota:"
        grep -B 3 "def excluir_grupo" routes/admin.py | grep "@admin_bp.route"
    else
        echo -e "${RED}✗ Rota NÃO está decorada${NC}"
    fi
else
    echo -e "${RED}✗ Função excluir_grupo NÃO encontrada${NC}"
fi
echo ""

# 5. Verificar sintaxe do onclick
echo -e "${BLUE}[5/6] Verificando sintaxe do onclick no botão...${NC}"
if grep -q "onclick='confirmarExclusao" templates/admin/grupos_lista.html; then
    echo -e "${GREEN}✓ Usando aspas simples (correto)${NC}"
    echo ""
    echo "Código do botão:"
    grep -A 3 "onclick='confirmarExclusao" templates/admin/grupos_lista.html
elif grep -q 'onclick="confirmarExclusao' templates/admin/grupos_lista.html; then
    echo -e "${YELLOW}⚠ Usando aspas duplas - pode causar problemas com JSON${NC}"
    echo ""
    echo "Código do botão:"
    grep -A 3 'onclick="confirmarExclusao' templates/admin/grupos_lista.html
else
    echo -e "${RED}✗ onclick NÃO encontrado${NC}"
fi
echo ""

# 6. Testar se o serviço está rodando
echo -e "${BLUE}[6/6] Verificando serviço...${NC}"
if systemctl is-active --quiet assessment 2>/dev/null; then
    echo -e "${GREEN}✓ Serviço assessment está ATIVO${NC}"
elif supervisorctl status assessment 2>/dev/null | grep -q RUNNING; then
    echo -e "${GREEN}✓ Serviço assessment está RUNNING (Supervisor)${NC}"
else
    echo -e "${YELLOW}⚠ Não foi possível verificar o status do serviço${NC}"
fi
echo ""

echo "======================================================================"
echo "DIAGNÓSTICO COMPLETO"
echo "======================================================================"
echo ""
echo -e "${YELLOW}PRÓXIMOS PASSOS:${NC}"
echo ""
echo "1. Abra o navegador e acesse /admin/grupos"
echo "2. Pressione F12 para abrir o Console do desenvolvedor"
echo "3. Clique no botão 'Excluir'"
echo "4. Verifique se aparece algum erro no Console"
echo ""
echo -e "${YELLOW}Erros comuns no Console:${NC}"
echo "  • 'confirmarExclusao is not defined' = função JavaScript não carregou"
echo "  • '403 Forbidden' ou 'CSRF' = problema com token CSRF"
echo "  • '404 Not Found' = rota não existe ou URL incorreta"
echo "  • Nenhum erro = JavaScript não está sendo executado"
echo ""
echo -e "${BLUE}Para ver os logs do servidor em tempo real:${NC}"
echo "  tail -f /var/log/supervisor/assessment-stderr.log"
echo "  # OU"
echo "  journalctl -u assessment -f"
echo ""
