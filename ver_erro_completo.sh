#!/bin/bash

echo "======================================================================"
echo "VERIFICANDO ERRO COMPLETO - Supervisor"
echo "======================================================================"
echo ""

# Verificar qual log está sendo usado
if [ -f "/var/log/supervisor/assessment-stderr.log" ]; then
    echo "LOG: /var/log/supervisor/assessment-stderr.log"
    echo ""
    echo "Últimas 100 linhas:"
    echo "----------------------------------------------------------------------"
    tail -100 /var/log/supervisor/assessment-stderr.log
    echo "----------------------------------------------------------------------"
elif [ -f "/var/log/supervisor/assessment.log" ]; then
    echo "LOG: /var/log/supervisor/assessment.log"
    echo ""
    tail -100 /var/log/supervisor/assessment.log
else
    echo "Procurando logs do Supervisor..."
    find /var/log -name "*assessment*" -type f 2>/dev/null
fi

echo ""
echo ""
echo "======================================================================"
echo "VERIFICANDO TEMPLATE - Últimas 20 linhas"
echo "======================================================================"
tail -20 /var/www/assessment/templates/admin/grupos_lista.html

echo ""
echo ""
echo "======================================================================"
echo "ACESSANDO A ROTA DIRETAMENTE"
echo "======================================================================"
echo "Vou tentar acessar /admin/grupos e mostrar o erro..."
echo ""

# Tentar fazer request local
curl -s http://localhost:5000/admin/grupos 2>&1 | head -50

echo ""
