# ⚡ Guia Rápido - Setup E-mail (On-Premise)

## 🚨 Problema Identificado

As variáveis de ambiente PostgreSQL não estão disponíveis quando executado com `sudo`, causando erro:
```
FATAL: role "root" does not exist
```

## ✅ Solução: Script Alternativo

Criamos `setup_email_onpremise.sh` que **não depende de variáveis de ambiente** e usa o usuário `postgres` do sistema.

## 🚀 Execução (Recomendado)

### Opção 1: Download e execução direta

```bash
cd /var/www/assessment
curl -sSL https://raw.githubusercontent.com/GruppenIT/assessment/refs/heads/main/setup_email_onpremise.sh | sudo bash
```

### Opção 2: Executar localmente

```bash
cd /var/www/assessment
git pull origin main
sudo bash setup_email_onpremise.sh
```

### Opção 3: Com parâmetros personalizados

Se seu banco usa credenciais diferentes:

```bash
sudo bash setup_email_onpremise.sh [usuario_db] [nome_db] [host] [porta]

# Exemplo:
sudo bash setup_email_onpremise.sh assessment_user assessment_db localhost 5432
```

## 📋 O que o script faz:

1. ✅ Atualiza código do Git
2. ✅ Cria coluna `email_destinatarios` (como usuário postgres)
3. ✅ Instala biblioteca MSAL (OAuth2)
4. ✅ Reinicia aplicação via Supervisor

## 🔧 Execução Manual (se o script falhar)

Se preferir executar passo a passo:

### 1. Atualizar código
```bash
cd /var/www/assessment
git pull origin main
```

### 2. Adicionar coluna no banco
```bash
sudo -u postgres psql -d assessment_db <<'EOF'
ALTER TABLE assessment_tipos 
ADD COLUMN IF NOT EXISTS email_destinatarios TEXT;
EOF
```

### 3. Instalar MSAL
```bash
pip3 install msal
```

### 4. Reiniciar aplicação
```bash
sudo supervisorctl restart assessment
```

## ✅ Verificação

### 1. Verificar se a coluna foi criada
```bash
sudo -u postgres psql -d assessment_db -c "\d assessment_tipos" | grep email_destinatarios
```

Deve retornar: `email_destinatarios | text`

### 2. Verificar MSAL instalado
```bash
pip3 show msal | head -3
```

### 3. Verificar aplicação rodando
```bash
sudo supervisorctl status assessment
```

Deve mostrar: `RUNNING`

### 4. Testar acesso à interface
```bash
curl -I http://localhost:5000/admin/parametros/smtp
```

Deve retornar: `HTTP/1.1 200 OK` ou redirecionamento 302/303

## 🎯 Configuração Pós-Instalação

### 1. Configurar SMTP

Acesse: `http://seu-servidor/admin/parametros/smtp`

**Autenticação Básica:**
- Servidor SMTP: `smtp.gmail.com`
- Porta: `587`
- Usuário: seu e-mail
- Senha: senha de aplicativo
- Remetente: seu e-mail
- Nome: "Assessments"

**OAuth2 Microsoft 365:**
- Servidor: `gruppen-com-br.mail.protection.outlook.com`
- Porta: `587`
- Client ID: do Azure AD
- Client Secret: do Azure AD
- Refresh Token: token OAuth2
- Tenant ID: ID do tenant
- Remetente: e-mail Microsoft
- Nome: "Assessments"

### 2. Configurar Destinatários

Em cada tipo de assessment:
1. Vá em **Assessments → Editar Tipo**
2. Campo: **"E-mails para Notificação de Leads"**
3. Adicione e-mails separados por vírgula:
   ```
   comercial@gruppen.com.br, vendas@gruppen.com.br
   ```

### 3. Testar

1. Acesse um assessment público
2. Responda as perguntas
3. Preencha dados de contato
4. Verifique se o e-mail foi recebido

## 🐛 Troubleshooting

### Erro: "peer authentication failed"

Edite `/etc/postgresql/*/main/pg_hba.conf`:
```
# Mudar de:
local   all   postgres   peer

# Para:
local   all   postgres   trust
```

Reinicie PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### Erro: "pip3: command not found"

Instale pip:
```bash
sudo apt update
sudo apt install python3-pip -y
```

### Erro: "supervisorctl: command not found"

Reinicie manualmente:
```bash
# Encontrar processo
ps aux | grep gunicorn

# Matar processo
sudo kill -HUP [PID]

# Ou reiniciar serviço
sudo systemctl restart assessment
```

### E-mail não chega

1. Verificar logs:
```bash
sudo supervisorctl tail -f assessment stdout | grep -i email
```

2. Testar SMTP manualmente:
```bash
python3 -c "
from utils.email_utils import EmailSender
sender = EmailSender()
print(sender.enviar_email(['teste@example.com'], 'Teste', '<h1>Teste</h1>'))
"
```

## 📞 Suporte

- Documentação completa: `README_EMAIL_NOTIFICATIONS.md`
- Logs: `sudo supervisorctl tail -f assessment`
- Contato: suporte técnico

---

**Última atualização**: 13/10/2025  
**Versão**: 1.2 (on-premise fix)
