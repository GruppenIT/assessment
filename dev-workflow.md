# Workflow de Desenvolvimento
## Sistema de Avaliações de Maturidade

Este documento descreve como trabalhar no desenvolvimento da aplicação usando Replit e sincronizar com seu servidor local.

## 🔄 Fluxo de Trabalho

### 1. Desenvolvimento no Replit
- Faça suas modificações e melhorias aqui no Replit
- Teste localmente usando o ambiente de desenvolvimento
- Valide todas as funcionalidades antes de fazer commit

### 2. Versionamento com Git
```bash
# Inicializar repositório (primeira vez)
git init
git add .
git commit -m "Initial commit - Sistema de Avaliações de Maturidade"

# Para atualizações subsequentes
git add .
git commit -m "Descrição das mudanças"
git push origin main
```

### 3. Deploy no Servidor
```bash
# No seu servidor Ubuntu
./deploy.sh update
```

## 📋 Setup Inicial

### No Replit (já configurado):
- ✅ Código fonte completo
- ✅ Estrutura MVC implementada
- ✅ Sistema de assessments funcionando
- ✅ Interface administrativa
- ✅ Importação CSV
- ✅ Geração de relatórios

### No seu servidor:
1. **Configurar repositório Git remoto** (GitHub, GitLab, etc.)
2. **Executar setup inicial**:
   ```bash
   # Clonar este projeto
   git clone https://replit.com/seu-projeto.git
   
   # Ou copiar arquivos manualmente e inicializar
   mkdir assessment-system
   cd assessment-system
   # Copiar todos os arquivos do Replit
   git init
   git remote add origin https://github.com/seuusuario/assessment-system.git
   ```

3. **Configurar ambiente de produção**:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh install
   ```

## 🛠️ Comandos Úteis

### No Replit:
```bash
# Testar aplicação
python main.py

# Verificar banco de dados
python -c "from app import app, db; app.app_context().push(); print('Tables:', db.metadata.tables.keys())"

# Commit e push das mudanças
git add .
git commit -m "Sua mensagem de commit"
git push origin main
```

### No Servidor:
```bash
# Atualizar aplicação
./deploy.sh update

# Verificar status
./deploy.sh status

# Criar backup
./deploy.sh backup

# Ver logs em tempo real
sudo tail -f /var/log/assessment.log

# Reiniciar serviços manualmente
sudo supervisorctl restart assessment
sudo systemctl reload nginx
```

## 📝 Convenções de Commit

Use mensagens descritivas nos commits:

- `feat: nova funcionalidade de relatórios avançados`
- `fix: correção no formulário de respondentes`
- `refactor: reorganização do código de importação CSV`
- `docs: atualização da documentação`
- `style: melhorias na interface do admin`

## 🔧 Debugging

### Problemas Comuns:

1. **Erro de banco de dados**:
   ```bash
   # No servidor
   sudo -u postgres psql
   \c assessment_db
   \dt  # Verificar tabelas
   ```

2. **Aplicação não inicia**:
   ```bash
   sudo supervisorctl status assessment
   sudo tail -f /var/log/assessment.log
   ```

3. **Nginx não serve arquivos**:
   ```bash
   sudo nginx -t
   sudo systemctl status nginx
   ```

## 📊 Monitoramento

### Logs importantes:
- Aplicação: `/var/log/assessment.log`
- Nginx: `/var/log/nginx/access.log` e `/var/log/nginx/error.log`
- PostgreSQL: `/var/log/postgresql/`

### Comandos de monitoramento:
```bash
# Uso de recursos
htop

# Espaço em disco
df -h

# Status geral
systemctl status assessment nginx postgresql
```

## 🚀 Deploy Automatizado

Para automatizar ainda mais, você pode criar um webhook que faz deploy automático quando há push no repositório:

```bash
# Criar script webhook (opcional)
cat > /var/www/webhook-deploy.py << EOF
#!/usr/bin/env python3
from flask import Flask, request
import subprocess
import os

app = Flask(__name__)

@app.route('/deploy', methods=['POST'])
def deploy():
    if request.json and request.json.get('ref') == 'refs/heads/main':
        try:
            result = subprocess.run(['/var/www/assessment/deploy.sh', 'update'], 
                                  capture_output=True, text=True)
            return f"Deploy executado: {result.stdout}", 200
        except Exception as e:
            return f"Erro no deploy: {str(e)}", 500
    return "Nothing to deploy", 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9000)
EOF
```

Este workflow permite que você:
1. Desenvolva no Replit com ambiente completo
2. Teste localmente antes do deploy
3. Faça commits organizados
4. Deploy automático no servidor
5. Monitore a aplicação em produção

É uma solução completa para desenvolvimento contínuo!