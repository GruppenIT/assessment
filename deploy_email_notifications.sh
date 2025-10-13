#!/bin/bash
# Script de deployment para sistema de notificações por e-mail
# Data: 2025-10-13

set -e  # Parar em caso de erro

# Carregar variáveis de ambiente se existir arquivo .env
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "Variáveis de ambiente carregadas do .env"
fi

echo "=========================================="
echo "DEPLOYMENT: Sistema de Notificações E-mail"
echo "=========================================="

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}1. Atualizando código do repositório...${NC}"
git pull origin main

echo -e "${YELLOW}2. Adicionando coluna email_destinatarios na tabela assessment_tipos...${NC}"
psql -U "$PGUSER" -d "$PGDATABASE" -h "$PGHOST" -p "$PGPORT" <<'EOF'
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'assessment_tipos' 
        AND column_name = 'email_destinatarios'
    ) THEN
        ALTER TABLE assessment_tipos 
        ADD COLUMN email_destinatarios TEXT;
        
        COMMENT ON COLUMN assessment_tipos.email_destinatarios IS 
        'E-mails que receberão alertas de novos leads (separados por vírgula ou ponto-e-vírgula)';
        
        RAISE NOTICE 'Coluna email_destinatarios adicionada com sucesso';
    ELSE
        RAISE NOTICE 'Coluna email_destinatarios já existe';
    END IF;
END $$;
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Migração executada com sucesso${NC}"
else
    echo -e "${RED}✗ Erro na migração${NC}"
    exit 1
fi

echo -e "${YELLOW}3. Instalando dependência MSAL (para OAuth2 Microsoft 365)...${NC}"
pip install msal --quiet

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependência MSAL instalada${NC}"
else
    echo -e "${RED}✗ Erro ao instalar MSAL${NC}"
    exit 1
fi

echo -e "${YELLOW}4. Reiniciando aplicação...${NC}"
sudo supervisorctl restart assessment

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Aplicação reiniciada${NC}"
else
    echo -e "${RED}✗ Erro ao reiniciar aplicação${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=========================================="
echo "DEPLOYMENT CONCLUÍDO COM SUCESSO!"
echo "==========================================${NC}"
echo ""
echo "📋 Próximos passos:"
echo ""
echo "1. Acesse: /admin/parametros/smtp"
echo "   Configure o servidor SMTP com suas credenciais"
echo ""
echo "2. Acesse: Assessments → Editar Tipo"
echo "   Adicione e-mails que receberão alertas de novos leads"
echo ""
echo "3. Teste criando um lead via assessment público"
echo "   Os e-mails serão enviados automaticamente"
echo ""
echo "Obs: A tabela parametros_sistema já existe e suporta"
echo "     armazenar as configurações SMTP dinamicamente."
echo ""
