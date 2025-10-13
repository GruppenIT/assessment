# 🔧 Correção do Deployment - Sistema de E-mail

## ❌ Erro Identificado

```
psql: error: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: 
FATAL: role "root" does not exist
```

## ✅ Correção Aplicada

O script `deploy_email_notifications.sh` foi corrigido para:
1. ✅ Usar as variáveis de ambiente corretas do PostgreSQL (`$PGUSER`, `$PGDATABASE`, `$PGHOST`, `$PGPORT`)
2. ✅ Carregar variáveis do arquivo `.env` se existir
3. ✅ Manter compatibilidade com ambiente on-premise

## 🚀 Como Executar a Correção

### Opção 1: Download Direto do GitHub (RECOMENDADO)

```bash
cd /var/www/assessment
curl -sSL https://raw.githubusercontent.com/GruppenIT/assessment/refs/heads/main/deploy_email_notifications.sh | sudo bash
```

### Opção 2: Executar Manualmente os Passos

Se preferir executar cada etapa separadamente:

#### 1. Atualizar código
```bash
cd /var/www/assessment
git pull origin main
```

#### 2. Adicionar coluna na tabela
```bash
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
```

#### 3. Instalar dependência MSAL
```bash
pip install msal
```

#### 4. Reiniciar aplicação
```bash
sudo supervisorctl restart assessment
```

## ✅ Verificação

### 1. Verificar se a coluna foi criada
```bash
psql -U "$PGUSER" -d "$PGDATABASE" -h "$PGHOST" -p "$PGPORT" -c "\d assessment_tipos"
```

Você deve ver a coluna `email_destinatarios` na lista.

### 2. Verificar se o MSAL foi instalado
```bash
pip show msal
```

### 3. Verificar se a aplicação está rodando
```bash
sudo supervisorctl status assessment
```

Status deve mostrar: `RUNNING`

### 4. Acessar interface SMTP
Acesse: `http://seu-servidor/admin/parametros/smtp`

## 📋 Próximos Passos Após a Correção

1. **Configurar SMTP** em `/admin/parametros/smtp`
   - Escolha entre autenticação básica ou OAuth2
   - Preencha os campos obrigatórios
   - Salve as configurações

2. **Configurar destinatários** em cada tipo de assessment
   - Vá em Assessments → Editar Tipo
   - Encontre "E-mails para Notificação de Leads"
   - Adicione os e-mails separados por vírgula

3. **Testar** criando um lead via assessment público
   - Responda um assessment com URL pública
   - Verifique se o e-mail foi recebido

## 🐛 Solução de Problemas

### Se as variáveis de ambiente não estiverem disponíveis:

```bash
# Verificar variáveis
echo "PGUSER=$PGUSER"
echo "PGDATABASE=$PGDATABASE"
echo "PGHOST=$PGHOST"
echo "PGPORT=$PGPORT"
```

Se alguma estiver vazia, carregue do arquivo .env:
```bash
cd /var/www/assessment
source .env
```

### Se o pip install msal falhar:

```bash
# Tentar com pip3
pip3 install msal

# Ou instalar como root
sudo pip install msal
```

### Se o Supervisor não reiniciar:

```bash
# Ver logs de erro
sudo supervisorctl tail -f assessment stderr

# Reiniciar forçadamente
sudo supervisorctl stop assessment
sudo supervisorctl start assessment
```

## 📞 Suporte

Se precisar de ajuda adicional:
1. Verifique os logs: `sudo supervisorctl tail -f assessment stdout`
2. Consulte o README completo: `README_EMAIL_NOTIFICATIONS.md`
3. Entre em contato com o suporte técnico

---

**Data da correção**: 13/10/2025  
**Versão do script**: 1.1 (corrigido)
