# Guia de Instalação On-Premise
## Sistema de Avaliações de Maturidade

Este guia fornece instruções completas para instalar o sistema em um servidor Ubuntu on-premise.

## Pré-requisitos

### Sistema Operacional
- Ubuntu 20.04 LTS ou superior
- Acesso root ou sudo
- Conexão com internet

### Dependências do Sistema
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python 3.11
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Instalar dependências de compilação
sudo apt install -y build-essential libssl-dev libffi-dev

# Instalar PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Instalar servidor web e supervisor
sudo apt install -y nginx supervisor

# Instalar Git
sudo apt install -y git curl
```

## Método 1: Instalação Manual (Recomendado)

### 1. Preparar o ambiente

```bash
# Criar diretório da aplicação
sudo mkdir -p /var/www/assessment
cd /var/www/assessment

# Clonar ou copiar arquivos do projeto
# (Substitua pela URL do seu repositório ou copie os arquivos manualmente)
git clone <URL_DO_REPOSITORIO> .
# OU
# Copie todos os arquivos do projeto para /var/www/assessment
```

### 2. Configurar PostgreSQL

```bash
# Acessar PostgreSQL como usuário postgres
sudo -u postgres psql

# Criar banco de dados e usuário
CREATE USER assessment_user WITH PASSWORD 'sua_senha_segura';
CREATE DATABASE assessment_db OWNER assessment_user;
GRANT ALL PRIVILEGES ON DATABASE assessment_db TO assessment_user;

# Sair do PostgreSQL
\q
```

### 3. Configurar a aplicação

```bash
# Navegar para o diretório da aplicação
cd /var/www/assessment

# Criar ambiente virtual
python3 -m venv venv

# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Criar arquivo de configuração de ambiente
cat > .env << 'EOF'
DATABASE_URL=postgresql://assessment_user:sua_senha_segura@localhost/assessment_db
SESSION_SECRET=sua_chave_secreta_aqui
FLASK_ENV=production
FLASK_DEBUG=False
EOF

# Inicializar banco de dados
python init_db.py
```

### 4. Configurar Nginx

```bash
# Criar configuração do Nginx
sudo tee /etc/nginx/sites-available/assessment << 'EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static {
        alias /var/www/assessment/static;
        expires 30d;
    }
    
    client_max_body_size 16M;
}
EOF

# Remover configuração padrão e habilitar o site
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -s /etc/nginx/sites-available/assessment /etc/nginx/sites-enabled/

# Testar configuração
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
```

### 5. Configurar Supervisor

```bash
# Criar configuração do Supervisor
sudo tee /etc/supervisor/conf.d/assessment.conf << 'EOF'
[program:assessment]
command=/var/www/assessment/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 wsgi:application
directory=/var/www/assessment
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/assessment.log
EOF

# Definir permissões
sudo chown -R www-data:www-data /var/www/assessment
sudo chmod -R 755 /var/www/assessment

# Recarregar configuração do Supervisor
sudo supervisorctl reread
sudo supervisorctl update

# Iniciar a aplicação
sudo supervisorctl start assessment
```

### 6. Verificar instalação

```bash
# Verificar status dos serviços
sudo supervisorctl status assessment
sudo systemctl status nginx

# Verificar logs
sudo tail -f /var/log/assessment.log

# Testar acesso
curl -I http://localhost
```

## Método 2: Instalação Automática (Script)

### Usar o script de deploy

```bash
# Tornar executável
chmod +x deploy.sh

# Executar instalação
sudo ./deploy.sh install

# Para atualizações futuras
sudo ./deploy.sh update

# Para verificar status
sudo ./deploy.sh status
```

## Configuração Avançada

### Configurar SSL (Opcional)

```bash
# Instalar Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obter certificado SSL (substitua example.com pelo seu domínio)
sudo certbot --nginx -d example.com

# Configurar renovação automática
sudo systemctl enable certbot.timer
```

### Configurar Firewall

```bash
# Instalar UFW
sudo apt install -y ufw

# Configurar regras
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'

# Ativar firewall
sudo ufw enable
```

### Configurar Backups

```bash
# Criar script de backup
sudo tee /usr/local/bin/backup-assessment.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/assessment"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup do banco de dados
sudo -u postgres pg_dump assessment_db > $BACKUP_DIR/db_backup_$DATE.sql

# Backup dos arquivos
tar -czf $BACKUP_DIR/files_backup_$DATE.tar.gz -C /var/www/assessment .

# Manter apenas os últimos 7 backups
find $BACKUP_DIR -type f -mtime +7 -delete
EOF

# Tornar executável
sudo chmod +x /usr/local/bin/backup-assessment.sh

# Adicionar ao cron (backup diário às 2h)
echo "0 2 * * * /usr/local/bin/backup-assessment.sh" | sudo crontab -
```

## Solução de Problemas

### Erro: "No module named 'app'"

```bash
# Verificar se está no diretório correto
cd /var/www/assessment

# Ativar ambiente virtual
source venv/bin/activate

# Usar o script de inicialização
python init_db.py
```

### Erro: "No module named 'main'"

```bash
# Verificar se o arquivo wsgi.py existe
ls -la wsgi.py

# Atualizar configuração do Supervisor
sudo supervisorctl stop assessment
sudo supervisorctl update
sudo supervisorctl start assessment
```

### Aplicação não inicia

```bash
# Verificar logs
sudo tail -f /var/log/assessment.log

# Verificar configuração do banco
sudo -u postgres psql -c "\l" | grep assessment

# Testar manualmente
cd /var/www/assessment
source venv/bin/activate
python wsgi.py
```

### Problemas de permissão

```bash
# Corrigir permissões
sudo chown -R www-data:www-data /var/www/assessment
sudo chmod -R 755 /var/www/assessment
sudo chmod +x /var/www/assessment/venv/bin/gunicorn
```

## Comandos Úteis

```bash
# Verificar status
sudo supervisorctl status assessment
sudo systemctl status nginx

# Reiniciar serviços
sudo supervisorctl restart assessment
sudo systemctl restart nginx

# Ver logs
sudo tail -f /var/log/assessment.log
sudo tail -f /var/log/nginx/error.log

# Atualizar aplicação
cd /var/www/assessment
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart assessment
```

## Informações de Acesso

Após a instalação bem-sucedida:

- **URL**: http://seu-servidor/
- **Login Admin**: admin@sistema.com
- **Senha Admin**: admin123

⚠️ **Importante**: Altere a senha padrão imediatamente após o primeiro login!

## Suporte

Para problemas ou dúvidas:
1. Verifique os logs do sistema
2. Consulte a seção de solução de problemas
3. Entre em contato com o suporte técnico

---

© Gruppen Serviços de Informática Ltda