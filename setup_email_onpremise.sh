#!/bin/bash
# Script simplificado para deployment de e-mail em ambiente on-premise
# Uso: sudo bash setup_email_onpremise.sh [usuario_db] [nome_db] [host_db] [porta_db]

echo "=========================================="
echo "SETUP E-MAIL - On-Premise"
echo "=========================================="

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Passo 1: Atualizar código
echo -e "${YELLOW}1. Atualizando código do Git...${NC}"
git pull origin main

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Código atualizado${NC}"
else
    echo -e "${RED}✗ Erro ao atualizar código${NC}"
    exit 1
fi

# Passo 2: Adicionar coluna (se não existir)
echo -e "${YELLOW}2. Adicionando coluna email_destinatarios...${NC}"

# Buscar credenciais do banco
DB_USER="${1:-assessment_user}"
DB_NAME="${2:-assessment_db}"
DB_HOST="${3:-localhost}"
DB_PORT="${4:-5432}"

echo "Usando: $DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"

# Executar SQL como usuário postgres (padrão on-premise)
sudo -u postgres psql -d "$DB_NAME" <<'EOF'
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
    echo -e "${GREEN}✓ Coluna criada/verificada com sucesso${NC}"
else
    echo -e "${RED}✗ Erro ao criar coluna${NC}"
    echo ""
    echo "Tente executar manualmente como usuário postgres:"
    echo "sudo -u postgres psql -d $DB_NAME"
    echo ""
    exit 1
fi

# Passo 3: Instalar MSAL
echo -e "${YELLOW}3. Instalando biblioteca MSAL (OAuth2)...${NC}"

# Tentar diferentes comandos pip
if command -v pip3 &> /dev/null; then
    pip3 install msal --quiet
elif command -v pip &> /dev/null; then
    pip install msal --quiet
else
    echo -e "${RED}✗ pip não encontrado${NC}"
    exit 1
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ MSAL instalado${NC}"
else
    echo -e "${YELLOW}⚠ Aviso: Erro ao instalar MSAL (pode já estar instalado)${NC}"
fi

# Passo 4: Reiniciar aplicação
echo -e "${YELLOW}4. Reiniciando aplicação...${NC}"

if command -v supervisorctl &> /dev/null; then
    sudo supervisorctl restart assessment
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Aplicação reiniciada via Supervisor${NC}"
    else
        echo -e "${YELLOW}⚠ Aviso: Erro ao reiniciar via Supervisor${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Supervisor não encontrado - reinicie manualmente${NC}"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "✓ SETUP CONCLUÍDO COM SUCESSO!"
echo "==========================================${NC}"
echo ""
echo "📋 Próximos passos:"
echo ""
echo "1. Acesse: http://seu-servidor/admin/parametros/smtp"
echo "   Configure o servidor SMTP"
echo ""
echo "2. Acesse: Assessments → Editar Tipo"
echo "   Adicione e-mails para receber notificações"
echo ""
echo "3. Teste criando um lead via assessment público"
echo ""
