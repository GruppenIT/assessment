#!/bin/bash
# Script para capturar logs de erro específicos da aplicação

echo "🔍 INVESTIGANDO ERRO REAL DA APLICAÇÃO"
echo "======================================"

cd /var/www/assessment

# 1. Verificar logs de erro em tempo real
echo "1. 📋 LOGS DE ERRO RECENTES:"
echo ""

# Verificar múltiplos locais de log
if [ -f "/var/log/assessment_error.log" ]; then
    echo "   📄 /var/log/assessment_error.log (últimas 30 linhas):"
    tail -30 /var/log/assessment_error.log
    echo ""
fi

if [ -f "/var/log/assessment.log" ]; then
    echo "   📄 /var/log/assessment.log (últimas 20 linhas):"
    tail -20 /var/log/assessment.log
    echo ""
fi

# Logs do supervisor
if [ -f "/var/log/supervisor/assessment-stdout.log" ]; then
    echo "   📄 Supervisor stdout (últimas 20 linhas):"
    tail -20 /var/log/supervisor/assessment-stdout.log
    echo ""
fi

if [ -f "/var/log/supervisor/assessment-stderr.log" ]; then
    echo "   📄 Supervisor stderr (últimas 20 linhas):"
    tail -20 /var/log/supervisor/assessment-stderr.log
    echo ""
fi

# 2. Fazer requisição que gera erro e capturar log
echo "2. 🔥 GERANDO ERRO PARA CAPTURAR LOG:"
echo ""

# Tentar fazer login como admin para reproduzir erro
echo "   Fazendo login como admin@sistema.com..."
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=admin@sistema.com&senha=admin123&csrf_token=test" \
  -v 2>&1 | head -20

echo ""
echo "   Aguardando logs de erro..."
sleep 2

# Verificar logs novamente após erro
echo ""
echo "3. 📋 LOGS APÓS TENTATIVA DE LOGIN:"
if [ -f "/var/log/assessment_error.log" ]; then
    echo "   📄 Novos erros:"
    tail -10 /var/log/assessment_error.log
fi

# 4. Testar importação específica da funcionalidade
echo ""
echo "4. 🧪 TESTE ESPECÍFICO DA NOVA FUNCIONALIDADE:"
source venv/bin/activate
python3 << 'EOF'
import sys
sys.path.append('/var/www/assessment')

try:
    from app import create_app
    app = create_app()
    
    with app.app_context():
        print("✅ App criado com sucesso")
        
        # Testar importação específica da nova funcionalidade
        from forms.cliente_forms import ResponenteForm
        print("✅ ResponenteForm importado")
        
        # Testar se o campo existe
        form = ResponenteForm()
        if hasattr(form, 'forcar_troca_senha'):
            print("✅ Campo forcar_troca_senha existe")
        else:
            print("❌ Campo forcar_troca_senha não existe")
        
        # Testar modelo Respondente
        from models.respondente import Respondente
        respondente = Respondente.query.first()
        if respondente and hasattr(respondente, 'forcar_troca_senha'):
            print(f"✅ Respondente tem campo: {respondente.forcar_troca_senha}")
        else:
            print("❌ Respondente não tem campo forcar_troca_senha")
        
        # Testar rota específica
        from routes.auth import auth_bp
        print("✅ Blueprint auth importado")
        
        # Testar se rota existe
        for rule in app.url_map.iter_rules():
            if 'troca-senha-obrigatoria' in rule.rule:
                print(f"✅ Rota encontrada: {rule.rule}")
                break
        else:
            print("❌ Rota troca-senha-obrigatoria não encontrada")

except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
EOF

echo ""
echo "======================================"
echo "🔍 INVESTIGAÇÃO CONCLUÍDA"
echo ""
echo "📞 PRÓXIMOS PASSOS:"
echo "   1. Analise os logs de erro acima"
echo "   2. Identifique a linha específica do erro"
echo "   3. Verifique se há conflito de importação"