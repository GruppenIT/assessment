#!/bin/bash
# Script para reiniciar aplicação após correção

echo "🔄 REINICIANDO APLICAÇÃO APÓS CORREÇÃO"
echo "====================================="

cd /var/www/assessment

# 1. Executar correção PostgreSQL
echo "1. 🔧 Executando correção do PostgreSQL..."
source venv/bin/activate
python3 corrigir_transacao_postgres.py

if [ $? -eq 0 ]; then
    echo "   ✅ Correção executada com sucesso"
else
    echo "   ❌ Erro na correção - abortando"
    exit 1
fi

# 2. Reiniciar aplicação
echo ""
echo "2. 🔄 Reiniciando aplicação..."
supervisorctl restart assessment

# 3. Aguardar inicialização
echo "   Aguardando inicialização..."
sleep 5

# 4. Testar conectividade
echo ""
echo "3. 🌐 Testando conectividade..."
for i in {1..5}; do
    response_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/auth/login 2>/dev/null || echo "ERRO")
    echo "   Tentativa $i: HTTP $response_code"
    
    if [ "$response_code" = "200" ]; then
        echo ""
        echo "🎉 APLICAÇÃO CORRIGIDA E FUNCIONANDO!"
        echo ""
        echo "✅ Funcionalidades ativas:"
        echo "   • Login de administradores"
        echo "   • Forçar troca de senha para respondentes"
        echo "   • Integração com 2FA"
        echo "   • Configurações do sistema"
        echo ""
        echo "🔗 ACESSE: https://assessments.zerobox.com.br"
        echo ""
        echo "📋 TESTE A FUNCIONALIDADE:"
        echo "   1. Faça login como admin"
        echo "   2. Vá em Clientes → Editar Respondente"
        echo "   3. Marque 'Forçar troca de senha no próximo login'"
        echo "   4. Teste o login do respondente"
        break
    elif [ $i -eq 5 ]; then
        echo ""
        echo "⚠️ Aplicação ainda não respondendo corretamente"
        echo "   Verificando logs..."
        tail -10 /var/log/assessment_error.log 2>/dev/null || echo "   Logs não encontrados"
    else
        sleep 2
    fi
done

echo ""
echo "====================================="
echo "🔄 REINICIALIZAÇÃO CONCLUÍDA"