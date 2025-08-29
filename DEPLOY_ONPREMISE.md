# Deploy On-Premise - Sistema de Avaliações de Maturidade

## 🚀 Script Unificado de Deploy

Este script atualiza automaticamente sua instalação on-premise com o código mais recente do Git, preservando todos os dados existentes.

### ✅ Dados Preservados
- **Projetos** - Todos os projetos criados
- **Clientes** - Cadastro completo de clientes
- **Usuários** - Contas de administradores
- **Assessments** - Avaliações em andamento e finalizadas
- **Configurações** - Configurações do sistema

### 🔒 Recursos de Segurança
- Backup completo automático antes da atualização
- Verificação de mudanças destrutivas no banco
- Aplicação automática de correções de segurança
- Middleware de autenticação obrigatória

## 📥 Instalação/Atualização

### Método 1: Execução Direta (Recomendado)
```bash
curl -sSL https://raw.githubusercontent.com/GruppenIT/assessment/refs/heads/main/deploy_onpremise_unified.sh | sudo bash
```

### Método 2: Download e Execução
```bash
curl -O https://raw.githubusercontent.com/GruppenIT/assessment/refs/heads/main/deploy_onpremise_unified.sh
chmod +x deploy_onpremise_unified.sh
sudo ./deploy_onpremise_unified.sh
```

### Método 3: Clone do Repositório
```bash
git clone https://github.com/GruppenIT/assessment.git
cd assessment
sudo ./deploy_onpremise_unified.sh
```

## ⚠️ Alertas de Segurança

O script verifica automaticamente por:

- **Operações destrutivas**: DROP TABLE, ALTER TABLE DROP COLUMN
- **Mudanças estruturais**: Novas colunas NOT NULL
- **Conflitos de dados**: Alterações que podem causar perda de dados

Se detectadas, o script solicitará confirmação antes de prosseguir.

## 📋 O Que o Script Faz

1. **Backup Completo**
   - Código fonte atual
   - Banco de dados PostgreSQL
   - Configurações do Supervisor
   - Arquivos de ambiente (.env)

2. **Atualização de Código**
   - Baixa última versão do Git
   - Atualiza dependências Python
   - Aplica correções de segurança

3. **Configuração do Sistema**
   - Configura ambiente virtual Python
   - Atualiza configuração do Supervisor
   - Define permissões corretas

4. **Verificações de Segurança**
   - Aplica middleware de autenticação
   - Remove rotas de auto-login
   - Testa proteção de rotas

## 📊 Após a Instalação

### Verificar Status
```bash
sudo supervisorctl status assessment
```

### Ver Logs
```bash
sudo tail -f /var/log/assessment.log
```

### Reiniciar Serviço
```bash
sudo supervisorctl restart assessment
```

### Testar Aplicação
```bash
curl -I http://localhost:8000/auth/login
# Deve retornar: HTTP/1.1 200 OK

curl -I http://localhost:8000/admin/dashboard
# Deve retornar: HTTP/1.1 302 FOUND (redirect para login)
```

## 🔄 Atualizações Futuras

Para atualizar o sistema sempre que houver mudanças no código:

```bash
curl -sSL https://raw.githubusercontent.com/GruppenIT/assessment/refs/heads/main/deploy_onpremise_unified.sh | sudo bash
```

O script pode ser executado quantas vezes for necessário - sempre preservará os dados existentes.

## 🆘 Recuperação em Caso de Problema

### Localizar Backup
Os backups ficam em `/var/www/assessment_backups/backup_YYYYMMDD_HHMMSS/`

### Restaurar Código
```bash
sudo cp -r /var/www/assessment_backups/backup_YYYYMMDD_HHMMSS/code/* /var/www/assessment/
sudo supervisorctl restart assessment
```

### Restaurar Banco de Dados
```bash
sudo -u postgres psql assessment_db < /var/www/assessment_backups/backup_YYYYMMDD_HHMMSS/database_backup.sql
```

## 📞 Suporte

Em caso de problemas:

1. Verifique logs: `/var/log/assessment.log`
2. Status do serviço: `sudo supervisorctl status assessment`
3. Banco de dados: `sudo -u postgres psql -d assessment_db -c "\dt"`

## 🔧 Configurações Avançadas

### Porta Personalizada
Para usar porta diferente de 8000, edite:
```bash
sudo nano /etc/supervisor/conf.d/assessment.conf
# Alterar --bind 0.0.0.0:8000 para porta desejada
sudo supervisorctl restart assessment
```

### Logs Personalizados
```bash
sudo nano /etc/supervisor/conf.d/assessment.conf
# Alterar caminhos stderr_logfile e stdout_logfile
sudo supervisorctl restart assessment
```

### Configurações de Produção
O script já inclui:
- 3 workers Gunicorn
- Timeout de 120 segundos
- Keep-alive otimizado
- Reload automático
- Max requests com jitter