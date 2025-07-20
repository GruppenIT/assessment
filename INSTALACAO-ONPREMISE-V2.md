# Instalação On-Premise - Sistema de Avaliações de Maturidade v2.0

Este documento descreve como instalar e configurar o Sistema de Avaliações de Maturidade em um servidor Ubuntu on-premise, incluindo todas as novas funcionalidades: gráficos radar, integração AI, versionamento de assessments, etc.

## 🆕 Novas Funcionalidades v2.0

- **Gráficos Radar**: Visualização gráfica em relatórios PDF usando matplotlib
- **Integração OpenAI**: Análises inteligentes e geração de conteúdo
- **Versionamento de Assessments**: Controle de versões com draft/published/archived
- **Portal do Cliente**: Dashboard para clientes visualizarem estatísticas
- **Timezone Brasil**: Suporte completo para GMT-3
- **Relatórios PDF Profissionais**: Estrutura formal com 9 seções
- **Gestão Avançada**: Drag-and-drop para perguntas, edição inline
- **Criptografia Avançada**: Segurança aprimorada

## Pré-requisitos

### Sistema Operacional
- Ubuntu 20.04 LTS ou superior
- Acesso root ou usuário com sudo
- **Mínimo 2GB RAM** (recomendado 4GB para matplotlib/numpy)
- **Espaço em disco**: 10GB livres

### Dependências do Sistema
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Dependências básicas
sudo apt install -y python3 python3-venv python3-dev python3-pip
sudo apt install -y postgresql postgresql-contrib
sudo apt install -y nginx supervisor
sudo apt install -y git curl wget unzip

# Dependências para matplotlib/numpy (NOVO)
sudo apt install -y build-essential pkg-config
sudo apt install -y libfreetype6-dev libpng-dev
sudo apt install -y python3-dev gcc g++

# Dependências para OpenAI/criptografia (NOVO)
sudo apt install -y libssl-dev libffi-dev
```

### PostgreSQL
```bash
# Configurar PostgreSQL
sudo -u postgres psql

CREATE USER assessment_user WITH PASSWORD 'sua_senha_segura';
CREATE DATABASE assessment_db OWNER assessment_user;
GRANT ALL PRIVILEGES ON DATABASE assessment_db TO assessment_user;
\q
```

## Configuração do Ambiente

### 1. Arquivo .env ATUALIZADO
Crie o arquivo `/home/suporte/.env` com as seguintes variáveis:

```bash
# Configurações do Flask
FLASK_SECRET_KEY=sua_chave_secreta_muito_segura_aqui
FLASK_ENV=production
FLASK_DEBUG=False

# Configurações do Banco de Dados
DATABASE_URL=postgresql://assessment_user:sua_senha@localhost/assessment_db

# Configurações de Timezone (NOVO)
TZ=America/Sao_Paulo
TIMEZONE=America/Sao_Paulo

# Configurações OpenAI (NOVO - OPCIONAL)
# OPENAI_API_KEY=sua_chave_openai_aqui

# Configurações de Segurança (NOVO)
SESSION_SECRET=outra_chave_secreta_para_sessoes

# Configurações para Matplotlib (NOVO)
MPLCONFIGDIR=/tmp/matplotlib
```

### 2. Configuração do Nginx ATUALIZADA
Crie `/etc/nginx/sites-available/assessment`:

```nginx
server {
    listen 80;
    server_name seu_dominio.com.br;  # ou IP do servidor

    # Aumentar timeouts para processamento de PDFs com gráficos
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    proxy_read_timeout 300;
    send_timeout 300;

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
        add_header Cache-Control "public, immutable";
    }

    # Upload de logos e arquivos (aumentado para PDFs grandes)
    client_max_body_size 100M;
}
```

### 3. Configuração do Supervisor ATUALIZADA
Crie `/etc/supervisor/conf.d/assessment.conf`:

```ini
[program:assessment]
command=/var/www/assessment/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 3 --timeout 300 --worker-class sync main:app
directory=/var/www/assessment
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/assessment.log
stderr_logfile=/var/log/supervisor/assessment_error.log
environment=PATH="/var/www/assessment/venv/bin",MPLCONFIGDIR="/tmp/matplotlib"
```

## Deploy da Aplicação

### Script Automatizado v2.0 ATUALIZADO (RECOMENDADO)
```bash
#!/bin/bash

# Script de Deploy Atualizado para Sistema v2.0
# Inclui todas as novas funcionalidades: AI, gráficos, versioning, etc.

# Reset banco
sudo -u postgres psql -c "DROP DATABASE IF EXISTS assessment_db;"
sudo -u postgres psql -c "CREATE DATABASE assessment_db OWNER assessment_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE assessment_db TO assessment_user;"

# Reset aplicação
cd /var/www
rm -fr assessment/

# Clone atualizado
git clone https://github.com/GruppenIT/assessment.git
cd /var/www/assessment

# Copiar .env
cp /home/suporte/.env ./

# Ambiente virtual com NOVAS DEPENDÊNCIAS
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Instalar dependências v2.0 (PODE DEMORAR para matplotlib/numpy)
echo "Instalando dependências v2.0 (matplotlib, numpy, openai, pytz)..."
pip install --timeout=300 -r requirements.txt

# Verificar instalação das novas dependências
echo "Verificando novas dependências..."
python -c "import matplotlib; print('✓ Matplotlib:', matplotlib.__version__)"
python -c "import numpy; print('✓ NumPy:', numpy.__version__)"
python -c "import openai; print('✓ OpenAI:', openai.__version__)"
python -c "import pytz; print('✓ PyTZ:', pytz.__version__)"

# Inicializar banco com nova estrutura
python init_db.py

# Nginx com configuração atualizada
sudo nginx -t
sudo systemctl restart nginx

# Permissões e diretórios especiais
sudo chown -R www-data:www-data /var/www/assessment
sudo chmod -R 755 /var/www/assessment

# Criar diretório para matplotlib (NOVO)
sudo mkdir -p /tmp/matplotlib
sudo chmod 777 /tmp/matplotlib

# Supervisor com configuração atualizada
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart assessment

echo "=== DEPLOY v2.0 CONCLUÍDO ==="
echo "Novas funcionalidades incluídas:"
echo "✓ Gráficos radar em PDFs"
echo "✓ Integração OpenAI"
echo "✓ Versionamento de assessments"
echo "✓ Portal do cliente"
echo "✓ Timezone Brasil"
echo "✓ Relatórios profissionais"
```

## Verificação da Instalação v2.0

### 1. Verificar Serviços
```bash
# Status básicos
sudo systemctl status postgresql nginx
sudo supervisorctl status assessment

# Logs detalhados
sudo tail -f /var/log/supervisor/assessment.log
sudo tail -f /var/log/supervisor/assessment_error.log

# Verificar novas dependências
cd /var/www/assessment
source venv/bin/activate
python -c "import matplotlib; print('Matplotlib:', matplotlib.__version__)"
python -c "import numpy; print('NumPy:', numpy.__version__)"
python -c "import openai; print('OpenAI:', openai.__version__)"
python -c "import pytz; print('PyTZ:', pytz.__version__)"
```

### 2. Teste de Funcionalidades v2.0
```bash
# Teste básico
curl http://localhost:5000

# Teste de geração de PDF (novo)
curl -I http://localhost:5000/admin/projetos

# Verificar matplotlib
python3 -c "import matplotlib.pyplot as plt; print('Matplotlib OK')"
```

### 3. Primeiro Acesso
1. Acesse `http://seu_servidor` no navegador
2. Vá para `/admin/login`
3. Credenciais padrão:
   - Usuário: `admin`
   - Senha: `admin123`

### 4. Testar Novas Funcionalidades
1. **Assessments com Versioning**: Criar novo assessment tipo
2. **Drag-and-Drop**: Reordenar perguntas
3. **Portal Cliente**: Verificar dashboard
4. **Gráfico Radar**: Gerar relatório PDF completo
5. **AI Integration**: Usar "Melhorar com IA" (se configurado)

## Troubleshooting v2.0

### Problemas Específicos das Novas Funcionalidades

1. **Erro ao Gerar Gráfico Radar**
```bash
# Verificar matplotlib
cd /var/www/assessment
source venv/bin/activate
python -c "import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt; print('OK')"

# Verificar diretório temporário
ls -la /tmp/matplotlib/
chmod 777 /tmp/matplotlib/
```

2. **Erro OpenAI (se configurado)**
```bash
# Verificar variável de ambiente
grep OPENAI_API_KEY /var/www/assessment/.env

# Testar conexão
cd /var/www/assessment
source venv/bin/activate
python -c "import openai; print('OpenAI disponível')"
```

3. **Problemas de Timezone**
```bash
# Verificar timezone do sistema
timedatectl status

# Verificar Python
python3 -c "import pytz; print(pytz.timezone('America/Sao_Paulo'))"
```

4. **Erro de Compilação (matplotlib/numpy)**
```bash
# Reinstalar dependências de compilação
sudo apt install -y python3-dev build-essential libfreetype6-dev libpng-dev
cd /var/www/assessment
source venv/bin/activate
pip install --upgrade --force-reinstall matplotlib numpy
```

5. **PDF Muito Lento**
```bash
# Aumentar timeout nginx
sudo nano /etc/nginx/sites-available/assessment
# Adicionar: proxy_read_timeout 600;

# Aumentar workers supervisor
sudo nano /etc/supervisor/conf.d/assessment.conf
# Modificar: --timeout 600

sudo systemctl reload nginx
sudo supervisorctl restart assessment
```

## Backup e Manutenção v2.0

### Backup Completo
```bash
#!/bin/bash
# backup-complete-v2.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/assessment"
mkdir -p $BACKUP_DIR

# Banco de dados
sudo -u postgres pg_dump assessment_db > $BACKUP_DIR/db_$DATE.sql

# Arquivos da aplicação
sudo tar -czf $BACKUP_DIR/app_$DATE.tar.gz -C /var/www assessment

# Uploads (logos, etc)
sudo tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz -C /var/www/assessment/static uploads

# .env
sudo cp /home/suporte/.env $BACKUP_DIR/env_$DATE

echo "Backup completo v2.0 em: $BACKUP_DIR"
```

### Monitoramento v2.0
```bash
# Script de monitoramento
#!/bin/bash
# monitor-v2.sh

echo "=== STATUS DO SISTEMA v2.0 ==="
echo "Data: $(date)"
echo ""

echo "=== SERVIÇOS ==="
systemctl status postgresql --no-pager -l | grep "Active:"
systemctl status nginx --no-pager -l | grep "Active:"
supervisorctl status assessment

echo ""
echo "=== RECURSOS ==="
df -h | grep -E "(Filesystem|/var|/tmp)"
free -h
top -bn1 | grep "load average"

echo ""
echo "=== DEPENDÊNCIAS v2.0 ==="
cd /var/www/assessment && source venv/bin/activate
python -c "import matplotlib; print('Matplotlib:', matplotlib.__version__)" 2>/dev/null || echo "Matplotlib: ERRO"
python -c "import numpy; print('NumPy:', numpy.__version__)" 2>/dev/null || echo "NumPy: ERRO"
python -c "import openai; print('OpenAI:', openai.__version__)" 2>/dev/null || echo "OpenAI: ERRO"

echo ""
echo "=== LOGS RECENTES ==="
tail -n 3 /var/log/supervisor/assessment.log
```

## Comandos de Diagnóstico v2.0
```bash
# Status completo
./monitor-v2.sh

# Logs em tempo real
sudo tail -f /var/log/supervisor/assessment.log /var/log/nginx/error.log

# Verificar dependências Python
cd /var/www/assessment && source venv/bin/activate && pip list | grep -E "(matplotlib|numpy|openai|pytz|reportlab)"

# Teste de performance
time curl -s http://localhost:5000/admin > /dev/null

# Verificar memória disponível
free -h && echo "Recomendado: 4GB+ para matplotlib"
```

## Performance v2.0

### Otimizações Recomendadas

1. **PostgreSQL**
```sql
-- /etc/postgresql/*/main/postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
```

2. **Sistema**
```bash
# Swappiness para SSDs
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf

# File descriptors
echo 'fs.file-max = 65536' | sudo tee -a /etc/sysctl.conf
```

## Segurança v2.0

### Configurações de Segurança Aprimoradas

1. **Firewall Atualizado**
```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw logging on
```

2. **Rate Limiting (Nginx)**
```nginx
# Adicionar ao server block
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/m;
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

location /admin/login {
    limit_req zone=login burst=3 nodelay;
    # ... resto da config
}
```

## Suporte e Atualizações

### Atualizações v2.0
```bash
# Backup antes da atualização
./backup-complete-v2.sh

# Atualização com script
./deploy-updated.sh

# Verificar funcionamento
./monitor-v2.sh
```

### Logs Importantes
- `/var/log/supervisor/assessment.log` - Aplicação principal
- `/var/log/supervisor/assessment_error.log` - Erros da aplicação
- `/var/log/nginx/access.log` - Acessos web
- `/var/log/nginx/error.log` - Erros web
- `/var/log/postgresql/postgresql-*.log` - Banco de dados

## Resumo das Principais Mudanças v2.0

1. **Dependências Adicionais**: matplotlib, numpy, openai, pytz
2. **Timeouts Aumentados**: Para processamento de PDFs com gráficos
3. **Diretório Matplotlib**: `/tmp/matplotlib` para gráficos temporários
4. **Configurações de Ambiente**: MPLCONFIGDIR, SESSION_SECRET
5. **Maior Uso de Memória**: Recomendado 4GB RAM
6. **Novos Recursos**: Gráficos, AI, versionamento, portal cliente

## Contato e Suporte

**Sistema de Avaliações de Maturidade v2.0**
- Documentação: GitHub do projeto
- Logs: Sempre consultar logs para diagnóstico
- Performance: Monitorar uso de CPU/RAM com matplotlib
- Backup: Manter backups regulares antes de atualizações

**Importante**: Esta versão inclui funcionalidades avançadas que requerem mais recursos do servidor. Monitore o desempenho e ajuste conforme necessário.