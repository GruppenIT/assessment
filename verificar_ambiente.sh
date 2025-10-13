#!/bin/bash
# Script para verificar o ambiente Python e configurações

echo "🔍 VERIFICAÇÃO DO AMBIENTE"
echo "======================================"
echo ""

# 1. Verificar ambiente virtual
echo "1. Procurando ambiente virtual Python..."
if [ -d "venv" ]; then
    echo "   ✓ Encontrado: venv/"
    PYTHON_CMD="venv/bin/python"
elif [ -d ".venv" ]; then
    echo "   ✓ Encontrado: .venv/"
    PYTHON_CMD=".venv/bin/python"
elif [ -d "env" ]; then
    echo "   ✓ Encontrado: env/"
    PYTHON_CMD="env/bin/python"
else
    echo "   ⚠ Nenhum ambiente virtual encontrado"
    PYTHON_CMD="python3"
fi

echo ""

# 2. Verificar supervisor config
echo "2. Verificando configuração do Supervisor..."
if [ -f "/etc/supervisor/conf.d/assessment.conf" ]; then
    echo "   ✓ Arquivo encontrado: /etc/supervisor/conf.d/assessment.conf"
    echo ""
    echo "   Comando de execução:"
    grep -E "^command=" /etc/supervisor/conf.d/assessment.conf | sed 's/command=/   → /'
    echo ""
    echo "   Diretório:"
    grep -E "^directory=" /etc/supervisor/conf.d/assessment.conf | sed 's/directory=/   → /'
else
    echo "   ⚠ Arquivo supervisor não encontrado"
fi

echo ""

# 3. Verificar módulos Python
echo "3. Verificando módulos Python instalados..."

echo "   Testando Flask..."
$PYTHON_CMD -c "import flask; print(f'   ✓ Flask {flask.__version__}')" 2>/dev/null || echo "   ✗ Flask não instalado"

echo "   Testando SQLAlchemy..."
$PYTHON_CMD -c "import sqlalchemy; print(f'   ✓ SQLAlchemy {sqlalchemy.__version__}')" 2>/dev/null || echo "   ✗ SQLAlchemy não instalado"

echo "   Testando MSAL..."
$PYTHON_CMD -c "import msal; print(f'   ✓ MSAL {msal.__version__}')" 2>/dev/null || echo "   ✗ MSAL não instalado"

echo ""

# 4. Verificar banco de dados
echo "4. Verificando banco de dados..."

if [ -f ".env" ]; then
    echo "   ✓ Arquivo .env encontrado"
    
    # Carregar variáveis
    export $(cat .env | grep -v '^#' | xargs)
    
    if [ ! -z "$PGDATABASE" ]; then
        echo "   ✓ Banco: $PGDATABASE"
        
        # Verificar coluna email_destinatarios
        echo ""
        echo "   Verificando coluna email_destinatarios..."
        sudo -u postgres psql -d "$PGDATABASE" -c "\d assessment_tipos" 2>/dev/null | grep email_destinatarios > /dev/null
        
        if [ $? -eq 0 ]; then
            echo "   ✓ Coluna email_destinatarios existe"
        else
            echo "   ✗ Coluna email_destinatarios NÃO existe"
            echo "   Execute: sudo -u postgres psql -d $PGDATABASE -c 'ALTER TABLE assessment_tipos ADD COLUMN email_destinatarios TEXT;'"
        fi
    fi
else
    echo "   ⚠ Arquivo .env não encontrado"
fi

echo ""

# 5. Verificar configurações SMTP
echo "5. Verificando configurações SMTP no banco..."

if [ ! -z "$PGDATABASE" ]; then
    SMTP_COUNT=$(sudo -u postgres psql -d "$PGDATABASE" -t -c "SELECT COUNT(*) FROM parametros_sistema WHERE chave LIKE 'smtp_%';" 2>/dev/null | tr -d ' ')
    
    if [ ! -z "$SMTP_COUNT" ] && [ "$SMTP_COUNT" -gt 0 ]; then
        echo "   ✓ Encontradas $SMTP_COUNT configurações SMTP"
    else
        echo "   ⚠ Nenhuma configuração SMTP encontrada"
        echo "   Configure em: /admin/parametros/smtp"
    fi
fi

echo ""

# 6. Verificar tipos com destinatários
echo "6. Verificando tipos de assessment com destinatários..."

if [ ! -z "$PGDATABASE" ]; then
    sudo -u postgres psql -d "$PGDATABASE" -c "
        SELECT 
            nome, 
            CASE 
                WHEN email_destinatarios IS NULL OR email_destinatarios = '' THEN '✗ SEM destinatários'
                ELSE '✓ COM destinatários: ' || email_destinatarios
            END as status
        FROM assessment_tipos 
        WHERE url_publica = true
        ORDER BY nome;
    " 2>/dev/null || echo "   ⚠ Erro ao consultar banco"
else
    echo "   ⚠ Banco não disponível"
fi

echo ""
echo "======================================"
echo ""

# Sugestão de comando
echo "Para testar envio de e-mail, use:"
echo ""
echo "   bash teste_email_simples.sh"
echo ""
echo "Ou execute manualmente:"
echo "   $PYTHON_CMD diagnostico_email.py"
echo ""
