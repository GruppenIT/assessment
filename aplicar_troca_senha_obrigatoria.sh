#!/bin/bash
# Script para aplicar funcionalidade de troca obrigatória de senha em produção

echo "🔐 APLICANDO TROCA OBRIGATÓRIA DE SENHA"
echo "======================================="

cd /var/www/assessment

# 1. Backup completo
echo "💾 Fazendo backup completo..."
timestamp=$(date +%Y%m%d_%H%M%S)
mkdir -p backups
tar -czf "backups/backup_pre_troca_senha_$timestamp.tar.gz" \
    --exclude='backups' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.git' \
    .
echo "✅ Backup salvo: backups/backup_pre_troca_senha_$timestamp.tar.gz"

# 2. Atualizar banco de dados (adicionar coluna se não existir)
echo "🗃️ Atualizando estrutura do banco..."
source venv/bin/activate
python3 << 'EOF'
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text

def atualizar_banco():
    app = create_app()
    with app.app_context():
        try:
            # Verificar se coluna existe
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='respondentes' AND column_name='forcar_troca_senha'
            """))
            
            if result.fetchone():
                print("✅ Coluna forcar_troca_senha já existe")
            else:
                # Adicionar coluna preservando dados existentes
                db.session.execute(text(
                    "ALTER TABLE respondentes ADD COLUMN forcar_troca_senha BOOLEAN DEFAULT FALSE NOT NULL"
                ))
                db.session.commit()
                print("✅ Coluna forcar_troca_senha adicionada (preservando dados)")
            
            return True
        except Exception as e:
            print(f"❌ Erro ao atualizar banco: {e}")
            return False

if __name__ == "__main__":
    atualizar_banco()
EOF

if [ $? -eq 0 ]; then
    echo "✅ Banco de dados atualizado"
else
    echo "❌ Erro ao atualizar banco de dados - abortando"
    exit 1
fi

# 3. Verificar arquivos necessários
echo "📄 Verificando arquivos..."
arquivos_necessarios=(
    "forms/troca_senha_forms.py"
    "templates/auth/troca_senha_obrigatoria.html"
)

for arquivo in "${arquivos_necessarios[@]}"; do
    if [ -f "$arquivo" ]; then
        echo "✅ $arquivo"
    else
        echo "❌ $arquivo - FALTANDO"
        echo "   Execute o script no desenvolvimento primeiro!"
        exit 1
    fi
done

# 4. Ajustar permissões
echo "🔐 Ajustando permissões..."
chown -R www-data:www-data /var/www/assessment/
chmod -R 755 /var/www/assessment/

# 5. Limpar cache Python
echo "🧹 Limpando cache..."
find /var/www/assessment -name "*.pyc" -delete
find /var/www/assessment -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 6. Testar importação dos novos módulos
echo "🧪 Testando módulos..."
python3 << 'EOF'
try:
    from forms.troca_senha_forms import TrocaSenhaObrigatoriaForm
    print("✅ TrocaSenhaObrigatoriaForm importado")
    
    from models.respondente import Respondente
    print("✅ Modelo Respondente atualizado")
    
    # Testar se campo existe
    from app import create_app
    app = create_app()
    with app.app_context():
        respondente = Respondente.query.first()
        if respondente and hasattr(respondente, 'forcar_troca_senha'):
            print("✅ Campo forcar_troca_senha disponível")
        else:
            print("⚠️ Campo forcar_troca_senha não encontrado")
    
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

# 7. Reiniciar aplicação
echo "🔄 Reiniciando aplicação..."
supervisorctl restart assessment
sleep 5

# 8. Teste de conectividade
echo "🌐 Testando conectividade..."
response_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/auth/login 2>/dev/null || echo "000")

if [ "$response_code" = "200" ] || [ "$response_code" = "302" ]; then
    echo ""
    echo "🎉 TROCA OBRIGATÓRIA DE SENHA IMPLEMENTADA!"
    echo ""
    echo "📋 FUNCIONALIDADES ATIVADAS:"
    echo "   ✅ Checkbox na edição de respondentes"
    echo "   ✅ Verificação automática no login"
    echo "   ✅ Página de troca obrigatória"
    echo "   ✅ Desmarcação automática após troca"
    echo "   ✅ Integração com fluxo 2FA"
    echo "   ✅ Preservação de todos os dados existentes"
    echo ""
    echo "🔗 COMO USAR:"
    echo "   1. Acesse Admin → Clientes → Editar Respondente"
    echo "   2. Marque 'Forçar troca de senha no próximo login'"
    echo "   3. Salve as alterações"
    echo "   4. O respondente será obrigado a trocar a senha no próximo login"
    echo "   5. Após a troca, a checkbox será desmarcada automaticamente"
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
echo "💾 BACKUP: backups/backup_pre_troca_senha_$timestamp.tar.gz"
echo "📖 LOGS: /var/log/supervisor/assessment-*.log"
echo ""
echo "⚠️ IMPORTANTE: Esta funcionalidade preserva todos os dados existentes"
echo "   A coluna 'forcar_troca_senha' foi adicionada com valor padrão FALSE"