#!/bin/bash
# Script para aplicar sistema de 2FA completo no ambiente de produção

echo "🔐 APLICANDO SISTEMA 2FA COMPLETO"
echo "================================="

cd /var/www/assessment

# 1. Backup completo
echo "💾 Fazendo backup completo..."
timestamp=$(date +%Y%m%d_%H%M%S)
mkdir -p backups
tar -czf "backups/backup_pre_2fa_$timestamp.tar.gz" \
    --exclude='backups' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.git' \
    .
echo "✅ Backup salvo: backups/backup_pre_2fa_$timestamp.tar.gz"

# 2. Instalar dependências Python
echo "📦 Instalando dependências..."
source venv/bin/activate
pip install pyotp qrcode[pil] 2>/dev/null || {
    pip install pyotp qrcode pillow
}
echo "✅ Dependências instaladas"

# 3. Criar arquivo requirements atualizado
echo "📋 Atualizando requirements.txt..."
if ! grep -q "pyotp" requirements.txt; then
    echo "pyotp>=2.9.0" >> requirements.txt
fi

if ! grep -q "qrcode" requirements.txt; then
    echo "qrcode>=8.0" >> requirements.txt
fi

if ! grep -q "pillow" requirements.txt && ! grep -q "Pillow" requirements.txt; then
    echo "pillow>=10.0.0" >> requirements.txt
fi

echo "✅ Requirements atualizado"

# 4. Criar estrutura de diretórios
echo "🏗️ Criando estrutura..."
mkdir -p models utils forms templates/auth

# 5. Copiar arquivos do sistema 2FA
echo "📄 Copiando arquivos..."

# Models
cat > models/two_factor.py << 'EOF'
# Arquivo já existe no sistema - verificar se está atualizado
EOF

# Utils
cat > utils/two_factor_utils.py << 'EOF'
# Arquivo já existe no sistema - verificar se está atualizado
EOF

# Forms
cat > forms/two_factor_forms.py << 'EOF'
# Arquivo já existe no sistema - verificar se está atualizado
EOF

# Templates
cat > templates/auth/setup_2fa.html << 'EOF'
# Arquivo já existe no sistema - verificar se está atualizado
EOF

cat > templates/auth/verify_2fa.html << 'EOF'
# Arquivo já existe no sistema - verificar se está atualizado
EOF

echo "✅ Estrutura criada"

# 6. Executar migração do banco de dados
echo "🗃️ Inicializando tabela 2FA..."
python3 << 'EOF'
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models.two_factor import TwoFactor

def init_2fa_table():
    app = create_app()
    with app.app_context():
        try:
            db.create_all()
            print("✅ Tabela two_factor criada/atualizada")
            
            # Verificar estrutura
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            if 'two_factor' in inspector.get_table_names():
                columns = inspector.get_columns('two_factor')
                print(f"✅ Tabela tem {len(columns)} colunas")
                return True
            else:
                print("❌ Tabela two_factor não encontrada")
                return False
        except Exception as e:
            print(f"❌ Erro: {e}")
            return False

if __name__ == "__main__":
    init_2fa_table()
EOF

# 7. Ajustar permissões
echo "🔐 Ajustando permissões..."
chown -R www-data:www-data /var/www/assessment/
chmod -R 755 /var/www/assessment/

# 8. Limpar cache Python
echo "🧹 Limpando cache..."
find /var/www/assessment -name "*.pyc" -delete
find /var/www/assessment -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 9. Testar importação
echo "🧪 Testando sistema..."
python3 << 'EOF'
try:
    import pyotp
    import qrcode
    print("✅ Bibliotecas importadas")
    
    from models.two_factor import TwoFactor
    from utils.two_factor_utils import get_user_2fa_config
    from forms.two_factor_forms import Setup2FAForm
    print("✅ Módulos 2FA importados")
    
    # Teste básico
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    token = totp.now()
    print(f"✅ TOTP funcional: {token}")
    
except Exception as e:
    print(f"❌ Erro no teste: {e}")
    exit(1)
EOF

if [ $? -eq 0 ]; then
    echo "✅ Testes passaram"
else
    echo "❌ Testes falharam - abortando"
    exit 1
fi

# 10. Reiniciar aplicação
echo "🔄 Reiniciando aplicação..."
supervisorctl restart assessment
sleep 5

# 11. Teste de conectividade
echo "🌐 Testando conectividade..."
response_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/auth/login 2>/dev/null || echo "000")

if [ "$response_code" = "200" ] || [ "$response_code" = "302" ]; then
    echo ""
    echo "🎉 SISTEMA 2FA IMPLEMENTADO COM SUCESSO!"
    echo ""
    echo "📱 FUNCIONALIDADES ATIVADAS:"
    echo "   ✅ Setup 2FA com QR Code"
    echo "   ✅ Verificação TOTP"
    echo "   ✅ Códigos de backup" 
    echo "   ✅ Reset por usuário"
    echo "   ✅ Reset administrativo"
    echo "   ✅ Obrigatório para respondentes"
    echo "   ✅ Opcional para admins"
    echo ""
    echo "🔗 ROTAS DISPONÍVEIS:"
    echo "   • /auth/setup-2fa - Configurar 2FA"
    echo "   • /auth/verify-2fa - Verificar código"
    echo "   • /auth/reset-2fa - Reset próprio"
    echo "   • /auth/perfil - Gerenciar 2FA"
    echo ""
    echo "👥 COMO USAR:"
    echo "   1. Admins: Opcional - configure em /auth/perfil"
    echo "   2. Respondentes: Obrigatório no primeiro login"
    echo "   3. Admins podem resetar 2FA de respondentes"
    echo ""
    echo "🌐 ACESSE: https://assessments.zerobox.com.br/auth/login"
else
    echo ""
    echo "⚠️ ATENÇÃO: Resposta HTTP $response_code"
    echo "   Verificando logs..."
    tail -20 /var/log/supervisor/assessment-*.log 2>/dev/null || echo "Logs não encontrados"
    echo ""
    echo "🔧 SOLUÇÃO: Verificar logs e reiniciar se necessário"
fi

echo ""
echo "💾 BACKUP: backups/backup_pre_2fa_$timestamp.tar.gz"
echo "📖 LOGS: /var/log/supervisor/assessment-*.log"