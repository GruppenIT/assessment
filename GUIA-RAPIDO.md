# 🚀 Guia Rápido - Deploy e Desenvolvimento

## ⚡ Setup Inicial (Primeira vez)

### 1. No seu servidor Ubuntu:
```bash
# Baixar os arquivos do Replit
# (Copie todos os arquivos do projeto para seu servidor)

# Dar permissões aos scripts
chmod +x deploy.sh setup-git.sh generate-requirements.py

# Configurar Git
./setup-git.sh
# (Digite seu nome e email quando solicitado)

# Criar repositório no GitHub/GitLab e conectar
git remote add origin https://github.com/seuusuario/assessment-system.git
git push -u origin main

# Deploy inicial
./deploy.sh install
```

### 2. Configurar variáveis de ambiente:
```bash
# Editar arquivo .env no servidor
nano /var/www/assessment/.env

# Adicionar:
DATABASE_URL=postgresql://usuario:senha@localhost/assessment_db
SESSION_SECRET=chave_muito_secreta_aqui_123456789
FLASK_ENV=production
```

## 🔄 Fluxo de Trabalho Diário

### 1. Desenvolver no Replit:
- Faça suas modificações aqui
- Teste as funcionalidades
- Quando estiver satisfeito, copie os arquivos para seu servidor

### 2. Atualizar no servidor:
```bash
# Navegar para diretório da aplicação
cd /var/www/assessment

# Adicionar mudanças
git add .
git commit -m "Descrição das mudanças"
git push origin main

# Fazer deploy
./deploy.sh update
```

### 3. Verificar se está funcionando:
```bash
# Verificar status
./deploy.sh status

# Ver logs em tempo real
sudo tail -f /var/log/assessment.log
```

## 🛠️ Comandos Úteis

```bash
# Parar aplicação
sudo supervisorctl stop assessment

# Iniciar aplicação  
sudo supervisorctl start assessment

# Reiniciar aplicação
sudo supervisorctl restart assessment

# Verificar status de todos os serviços
sudo supervisorctl status

# Recarregar Nginx
sudo systemctl reload nginx

# Criar backup manual
./deploy.sh backup

# Ver logs detalhados
sudo journalctl -u supervisor -f
```

## 📁 Estrutura de Arquivos

```
/var/www/assessment/
├── app.py              # Aplicação principal
├── main.py             # Ponto de entrada
├── config.py           # Configurações
├── requirements.txt    # Dependências Python
├── deploy.sh          # Script de deploy
├── models/            # Modelos do banco
├── routes/            # Rotas da aplicação
├── templates/         # Templates HTML
├── static/            # Arquivos estáticos
├── forms/             # Formulários
├── utils/             # Utilitários
├── venv/              # Ambiente virtual
└── .env               # Variáveis de ambiente
```

## 🔍 Troubleshooting

### Aplicação não inicia:
```bash
# Verificar logs
sudo tail -20 /var/log/assessment.log

# Verificar processo
sudo supervisorctl status assessment

# Reiniciar tudo
sudo supervisorctl restart assessment
sudo systemctl reload nginx
```

### Erro de banco:
```bash
# Conectar ao PostgreSQL
sudo -u postgres psql assessment_db

# Verificar tabelas
\dt

# Sair
\q
```

### Permissões:
```bash
# Corrigir permissões
sudo chown -R www-data:www-data /var/www/assessment
sudo chmod -R 755 /var/www/assessment
```

## 📞 Suporte

Se algo não funcionar:
1. Verifique os logs: `sudo tail -f /var/log/assessment.log`
2. Verifique o status: `./deploy.sh status`
3. Tente reiniciar: `sudo supervisorctl restart assessment`

## 🎯 Próximos Passos Sugeridos

1. **Configurar HTTPS**: Use certbot para SSL
2. **Backup automático**: Configure cron para backups diários
3. **Monitoramento**: Configure alertas de sistema
4. **Logs centralizados**: Implementar rotação de logs

---

**Sistema desenvolvido por Gruppen Serviços de Informática Ltda**