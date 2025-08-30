#!/bin/bash
# Script para verificar logs do sistema após erro de deploy

echo "📋 VERIFICANDO LOGS DO SISTEMA"
echo "==============================="

# 1. Logs do Supervisor
echo "1. 🔧 LOGS DO SUPERVISOR:"
echo "   Últimas 20 linhas dos logs do assessment:"
if [ -f "/var/log/supervisor/assessment-stdout.log" ]; then
    echo "   📄 assessment-stdout.log:"
    tail -20 /var/log/supervisor/assessment-stdout.log
    echo ""
fi

if [ -f "/var/log/supervisor/assessment-stderr.log" ]; then
    echo "   📄 assessment-stderr.log:"
    tail -20 /var/log/supervisor/assessment-stderr.log
    echo ""
fi

if [ -f "/var/log/supervisor/supervisord.log" ]; then
    echo "   📄 supervisord.log (últimas 10 linhas):"
    tail -10 /var/log/supervisor/supervisord.log
    echo ""
fi

# 2. Status do Supervisor
echo "2. ⚙️ STATUS DO SUPERVISOR:"
supervisorctl status
echo ""

# 3. Verificar processo Python
echo "3. 🐍 PROCESSOS PYTHON:"
ps aux | grep -E "(python|gunicorn|assessment)" | grep -v grep
echo ""

# 4. Verificar porta 8000
echo "4. 🌐 VERIFICAR PORTA 8000:"
netstat -tulpn | grep :8000 || echo "   ⚠️ Porta 8000 não está sendo utilizada"
echo ""

# 5. Teste de conectividade local
echo "5. 🔌 TESTE DE CONECTIVIDADE:"
response_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/auth/login 2>/dev/null || echo "ERRO")
echo "   HTTP Response: $response_code"

if [ "$response_code" != "200" ] && [ "$response_code" != "302" ]; then
    echo "   ❌ Aplicação não está respondendo corretamente"
else
    echo "   ✅ Aplicação respondendo"
fi
echo ""

# 6. Verificar arquivo de configuração do Supervisor
echo "6. ⚙️ CONFIGURAÇÃO DO SUPERVISOR:"
if [ -f "/etc/supervisor/conf.d/assessment.conf" ]; then
    echo "   📄 /etc/supervisor/conf.d/assessment.conf:"
    cat /etc/supervisor/conf.d/assessment.conf
else
    echo "   ❌ Arquivo de configuração não encontrado"
fi
echo ""

# 7. Verificar variáveis de ambiente (sem mostrar senhas)
echo "7. 🔐 VARIÁVEIS DE AMBIENTE (resumo):"
cd /var/www/assessment
if [ -f ".env" ]; then
    echo "   ✅ Arquivo .env existe"
    echo "   📊 Variáveis definidas:"
    grep -E "^[A-Z_]+" .env | cut -d'=' -f1 | sort
else
    echo "   ⚠️ Arquivo .env não encontrado"
fi
echo ""

# 8. Verificar permissões
echo "8. 🔐 VERIFICAR PERMISSÕES:"
ls -la /var/www/assessment/ | head -10
echo ""

# 9. Verificar espaço em disco
echo "9. 💾 ESPAÇO EM DISCO:"
df -h /var/www/
echo ""

# 10. Teste manual de importação Python
echo "10. 🧪 TESTE DE IMPORTAÇÃO PYTHON:"
cd /var/www/assessment
source venv/bin/activate
python3 -c "
import sys
sys.path.append('/var/www/assessment')
try:
    from app import create_app
    print('✅ app importado com sucesso')
    app = create_app()
    print('✅ app criado com sucesso')
except Exception as e:
    print(f'❌ Erro: {e}')
    import traceback
    traceback.print_exc()
" 2>&1

echo ""
echo "==============================="
echo "📋 VERIFICAÇÃO DE LOGS CONCLUÍDA"
echo ""
echo "📞 PRÓXIMOS PASSOS:"
echo "   1. Analise os logs acima"
echo "   2. Execute: sudo python3 /var/www/assessment/diagnostico_erro_deploy.py"
echo "   3. Se necessário, execute: supervisorctl restart assessment"