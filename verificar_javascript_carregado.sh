#!/bin/bash

###############################################################################
# Verificar se JavaScript está sendo renderizado na página
###############################################################################

echo "======================================================================"
echo "Verificando Renderização do JavaScript"
echo "======================================================================"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "1. Estrutura do template:"
echo "---------------------------------------------------------------------"
tail -50 templates/admin/grupos_lista.html
echo "---------------------------------------------------------------------"
echo ""

echo "2. Verificando se {% endblock %} existe:"
if tail -5 templates/admin/grupos_lista.html | grep -q "{% endblock %}"; then
    echo -e "${GREEN}✓ {% endblock %} encontrado${NC}"
else
    echo -e "${RED}✗ {% endblock %} NÃO encontrado no final do arquivo!${NC}"
fi
echo ""

echo "3. Contando blocos:"
echo "   - {% block scripts %} = $(grep -c "{% block scripts %}" templates/admin/grupos_lista.html)"
echo "   - {% endblock %} = $(grep -c "{% endblock %}" templates/admin/grupos_lista.html)"
echo ""

echo "======================================================================"
echo "INSTRUÇÕES PARA VERIFICAR NO NAVEGADOR"
echo "======================================================================"
echo ""
echo -e "${YELLOW}FAÇA ISSO AGORA:${NC}"
echo ""
echo "1. No navegador, acesse: /admin/grupos"
echo "2. Clique com botão DIREITO na página"
echo "3. Escolha 'Ver código-fonte da página' ou 'View Page Source'"
echo "4. Pressione Ctrl+F e busque por: 'confirmarExclusao'"
echo ""
echo "   SE ENCONTRAR a função:"
echo "   ✓ O template está OK, o problema é no onclick"
echo ""
echo "   SE NÃO ENCONTRAR:"
echo "   ✗ O JavaScript não está sendo renderizado"
echo ""
echo "5. No Console (F12), digite e pressione Enter:"
echo "   typeof confirmarExclusao"
echo ""
echo "   SE retornar 'function':"
echo "   ✓ Função está definida, problema é no onclick do botão"
echo ""
echo "   SE retornar 'undefined':"
echo "   ✗ Função não foi carregada"
echo ""
