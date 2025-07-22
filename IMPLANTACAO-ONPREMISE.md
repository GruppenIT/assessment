# Sistema de Avaliações de Maturidade - Implantação On-Premise

Documentação completa para instalação e configuração do sistema em servidores Ubuntu on-premise.

## Visão Geral

Este sistema é uma aplicação web Flask para avaliações de maturidade em cibersegurança, compliance e outras áreas. Suporta múltiplos clientes, respondentes colaborativos, versionamento de assessments e relatórios profissionais em PDF.

### Características Técnicas

- **Backend**: Flask (Python 3.11+)
- **Banco de dados**: PostgreSQL
- **Servidor web**: Nginx + Gunicorn
- **Processo**: Supervisor
- **Frontend**: Bootstrap 5, JavaScript vanilla
- **Relatórios**: PDF com gráficos radar

## Pré-requisitos

### Sistema Operacional
- Ubuntu 20.04 LTS ou superior
- 4GB RAM mínimo (8GB recomendado)
- 20GB espaço em disco
- Acesso root ou sudo

### Dependências do Sistema
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Dependências principais
sudo apt install -y python3 python3-pip python3-venv python3-dev
sudo apt install -y postgresql postgresql-contrib
sudo apt install -y nginx supervisor git curl

# Dependências para gráficos e matplotlib
sudo apt install -y build-essential pkg-config
sudo apt install -y libfreetype6-dev libpng-dev
sudo apt install -y libssl-dev libffi-dev
```

## Instalação

### 1. Preparar PostgreSQL

```bash
# Configurar PostgreSQL
sudo -u postgres psql << EOF
CREATE USER assessment_user WITH PASSWORD 'SuaSenhaSegura123!';
CREATE DATABASE assessment_db OWNER assessment_user;
GRANT ALL PRIVILEGES ON DATABASE assessment_db TO assessment_user;
\q
EOF

# Configurar autenticação
sudo nano /etc/postgresql/*/main/pg_hba.conf
# Adicionar linha: local assessment_db assessment_user md5

sudo systemctl restart postgresql
```

### 2. Preparar Aplicação

```bash
# Criar diretório e usuário
sudo mkdir -p /var/www/assessment
sudo chown -R www-data:www-data /var/www/assessment

# Clonar repositório (ajuste a URL)
cd /var/www
sudo git clone [URL_DO_REPOSITORIO] assessment
sudo chown -R www-data:www-data assessment

# Configurar ambiente Python
cd /var/www/assessment
sudo -u www-data python3 -m venv venv
sudo -u www-data venv/bin/pip install --upgrade pip
sudo -u www-data venv/bin/pip install -r requirements.txt
```

### 3. Configurar Ambiente

Criar arquivo `/var/www/assessment/.env`:

```bash
# Configurações Flask
FLASK_SECRET_KEY=SuaChaveSecretaMuitoSeguraAqui123!@#
SESSION_SECRET=OutraChaveSecretaParaSessoes456$%^
FLASK_ENV=production
FLASK_DEBUG=False

# Banco de dados
DATABASE_URL=postgresql://assessment_user:SuaSenhaSegura123!@localhost/assessment_db

# Timezone
TZ=America/Sao_Paulo
TIMEZONE=America/Sao_Paulo

# Matplotlib (para gráficos)
MPLCONFIGDIR=/tmp/matplotlib

# OpenAI (opcional - para recursos AI)
# OPENAI_API_KEY=sua_chave_openai_aqui
```

### 4. Configurar Supervisor

Criar `/etc/supervisor/conf.d/assessment.conf`:

```ini
[program:assessment]
command=/var/www/assessment/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 300 --worker-class sync main:app
directory=/var/www/assessment
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/assessment.log
stderr_logfile=/var/log/assessment_error.log
environment=DATABASE_URL="postgresql://assessment_user:SuaSenhaSegura123!@localhost/assessment_db",SESSION_SECRET="OutraChaveSecretaParaSessoes456$%^",FLASK_SECRET_KEY="SuaChaveSecretaMuitoSeguraAqui123!@#",FLASK_ENV="production",TZ="America/Sao_Paulo",MPLCONFIGDIR="/tmp/matplotlib"
```

### 5. Configurar Nginx

Criar `/etc/nginx/sites-available/assessment`:

```nginx
server {
    listen 80;
    server_name seu-dominio.com.br;
    
    client_max_body_size 16M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    location /static {
        alias /var/www/assessment/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Ativar site:
```bash
sudo ln -s /etc/nginx/sites-available/assessment /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### 6. Inicializar Sistema

```bash
# Executar script de instalação
cd /var/www/assessment
sudo -u www-data bash -c "source venv/bin/activate && python instalar_sistema.py"

# Iniciar serviços
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start assessment

# Verificar status
sudo supervisorctl status assessment
sudo systemctl status nginx
```

## Verificação da Instalação

Após a instalação, execute:

```bash
cd /var/www/assessment
sudo -u www-data bash -c "source venv/bin/activate && python verificar_instalacao.py"
```

## Acesso Inicial

- **URL**: http://seu-servidor (ou IP do servidor)
- **Login administrativo**: admin@sistema.com
- **Senha padrão**: admin123

**IMPORTANTE**: Altere a senha padrão no primeiro acesso!

## SSL/HTTPS (Recomendado)

Para configurar SSL com Let's Encrypt:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d seu-dominio.com.br
sudo systemctl reload nginx
```

## Manutenção

### Logs do Sistema
- Aplicação: `/var/log/assessment.log`
- Erros: `/var/log/assessment_error.log`
- Nginx: `/var/log/nginx/access.log` e `/var/log/nginx/error.log`

### Comandos Úteis
```bash
# Reiniciar aplicação
sudo supervisorctl restart assessment

# Verificar logs em tempo real
sudo tail -f /var/log/assessment.log

# Status dos serviços
sudo systemctl status postgresql nginx supervisor

# Backup do banco
pg_dump -h localhost -U assessment_user assessment_db > backup_$(date +%Y%m%d).sql
```

## Atualizações

Para atualizar o sistema, utilize:

```bash
cd /var/www/assessment
sudo bash atualizar_sistema.sh
```

## Solução de Problemas

### Problema: Aplicação não inicia
1. Verificar logs: `sudo tail -f /var/log/assessment_error.log`
2. Testar configuração: `sudo -u www-data venv/bin/python -c "from app import create_app; create_app()"`
3. Verificar permissões: `sudo chown -R www-data:www-data /var/www/assessment`

### Problema: Erro de banco de dados
1. Verificar PostgreSQL: `sudo systemctl status postgresql`
2. Testar conexão: `psql -h localhost -U assessment_user assessment_db`
3. Executar migrations: `sudo -u www-data bash -c "source venv/bin/activate && python migrar_banco.py"`

### Problema: Erro 502 (Bad Gateway)
1. Verificar Gunicorn: `sudo supervisorctl status assessment`
2. Verificar porta: `sudo netstat -tlnp | grep 8000`
3. Reiniciar serviços: `sudo supervisorctl restart assessment`

## Contato e Suporte

Para suporte técnico ou dúvidas sobre a instalação, entre em contato com a equipe de desenvolvimento.

---

**Versão da documentação**: 1.0  
**Data**: $(date +"%d/%m/%Y")  
**Compatibilidade**: Ubuntu 20.04+ / Python 3.11+ / PostgreSQL 12+