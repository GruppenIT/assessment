# Deploy On-Premise com Assessment Público

## 📋 Visão Geral

Este script atualiza o sistema de avaliações preservando **100% dos dados existentes** e aplica automaticamente a migração para a funcionalidade de **Assessment Público**.

## ✅ O Que é Preservado

- ✅ **Todos os Assessments** (em andamento e concluídos)
- ✅ **Todos os Clientes** cadastrados
- ✅ **Todos os Respondentes** e usuários
- ✅ **Todos os Projetos** configurados
- ✅ **Respostas e relatórios** existentes
- ✅ **Configurações do sistema**

## 🔒 Proteções de Segurança

### 1. Backup Automático
Antes de qualquer mudança, cria backup completo:
- Dump do banco PostgreSQL
- Código fonte completo
- Configurações do Supervisor
- Arquivo .env

**Local:** `/var/www/assessment_backups/backup_YYYYMMDD_HHMMSS/`

### 2. Detecção de Operações Destrutivas
- Verifica comandos `DROP TABLE`, `DROP COLUMN`, `db.drop_all()`
- Exige confirmação explícita se detectar operações perigosas
- Cancela deploy se você recusar

### 3. Rollback Automático
- Em caso de erro, restaura automaticamente:
  - Código anterior
  - Banco de dados
  - Configurações

## 🆕 O Que é Adicionado

### Novas Colunas (idempotente)
- `tipos_assessment.url_publica` - Habilita URL pública
- `respondentes.telefone` - Campo telefone
- `clientes.telefone` - Campo telefone

### Novas Tabelas (idempotente)
- `assessments_publicos` - Assessments anônimos
- `respostas_publicas` - Respostas públicas

### Novos Índices
- `idx_assessments_publicos_token` - Busca rápida por token
- `idx_respostas_publicas_assessment` - Performance
- `idx_respostas_publicas_pergunta` - Performance

## 📥 Como Usar

### Pré-requisitos
- Servidor Ubuntu/Debian
- PostgreSQL instalado
- Acesso root (sudo)
- Git configurado

### Execução

```bash
# 1. Copiar script para o servidor
scp deploy_onpremise_com_publico.sh usuario@servidor:/tmp/

# 2. Conectar ao servidor
ssh usuario@servidor

# 3. Executar como root
sudo bash /tmp/deploy_onpremise_com_publico.sh
```

### O Que o Script Faz

1. **Backup Completo** (tempo: ~30s)
   - Cria snapshot do sistema atual

2. **Verifica Segurança** (tempo: ~5s)
   - Detecta operações destrutivas
   - Solicita confirmação se necessário

3. **Para Serviços** (tempo: ~5s)
   - Para aplicação temporariamente

4. **Atualiza Código** (tempo: ~20s)
   - Git pull do repositório

5. **Atualiza Dependências** (tempo: ~1min)
   - Instala novos pacotes Python

6. **Aplica Migração SQL** (tempo: ~10s)
   - **Idempotente:** Pode rodar múltiplas vezes
   - Verifica se cada coluna/tabela existe antes de criar
   - Não quebra se já estiver aplicado

7. **Reinicia Serviços** (tempo: ~10s)
   - Supervisor e aplicação

8. **Verifica Funcionamento** (tempo: ~10s)
   - Testa endpoints
   - Confirma segurança

**Tempo Total:** ~3-5 minutos

## 📊 Saída Esperada

```
🚀 SISTEMA DE AVALIAÇÕES DE MATURIDADE - DEPLOY ON-PREMISE
=========================================================
⚠️  ESTE SCRIPT PRESERVA TODOS OS DADOS EXISTENTES
   • Projetos, Clientes, Usuários e Assessments são mantidos
   • Backup completo é criado antes da atualização
   • Migração de Assessment Público será aplicada

📋 Criando backup completo...
   ✅ Código fonte copiado
   ✅ Backup do banco criado
   ✅ Configuração Supervisor copiada
✅ Backup completo criado em: /var/www/assessment_backups/backup_20251011_143022

🔍 Verificando mudanças na estrutura do banco...

🛑 Parando serviços...
   ✅ Serviço assessment parado

📥 Atualizando código fonte...
   🔄 Atualizando código existente...
   ✅ Código atualizado

🐍 Configurando ambiente Python...
   📦 Instalando dependências...
   ✅ Ambiente Python configurado

💾 Configurando banco de dados...
   ℹ️  Banco de dados já contém dados, pulando inicialização
   📝 Executando migração SQL...
   ✅ Migração de Assessment Público aplicada com sucesso
   🔍 Verificando tabelas criadas...
   ✅ Tabela assessments_publicos confirmada
   ✅ Banco de dados configurado

⚙️  Configurando Supervisor...
   ✅ Supervisor configurado

🔐 Configurando permissões...
   ✅ Permissões configuradas

🔄 Iniciando serviços...
   ✅ Serviço assessment iniciado com sucesso

🔍 Verificando deployment...
   ✅ Aplicação respondendo corretamente (código 200)
   ✅ Proteção de segurança ativa (redirecionamento para login)

✅ DEPLOY CONCLUÍDO COM SUCESSO!

📊 Resumo:
   • Código atualizado do Git
   • Dados existentes preservados
   • Migração de Assessment Público aplicada
   • Sistema rodando na porta 8000

🔗 Funcionalidades disponíveis:
   • Assessments tradicionais (autenticados)
   • Assessments públicos (URLs compartilháveis)
   • Captura de leads e recomendações IA

💾 Backup criado em: /var/www/assessment_backups/backup_20251011_143022
```

## 🔧 Solução de Problemas

### Se o Deploy Falhar

1. **Rollback Automático**
   - O script restaura automaticamente o estado anterior
   - Verifica logs: `tail -f /var/log/assessment_deploy.log`

2. **Rollback Manual (se necessário)**
   ```bash
   # Restaurar banco de dados
   sudo -u postgres psql -d assessment_db < /var/www/assessment_backups/backup_TIMESTAMP/database_backup.sql
   
   # Restaurar código
   sudo rm -rf /var/www/assessment
   sudo cp -r /var/www/assessment_backups/backup_TIMESTAMP/code /var/www/assessment
   
   # Reiniciar serviços
   sudo supervisorctl restart assessment
   ```

### Verificar Migração Aplicada

```bash
# Verificar coluna url_publica
sudo -u postgres psql -d assessment_db -c "\d tipos_assessment"

# Verificar tabelas públicas
sudo -u postgres psql -d assessment_db -c "\dt assessments_publicos"
sudo -u postgres psql -d assessment_db -c "\dt respostas_publicas"
```

### Logs do Sistema

```bash
# Log do deploy
tail -f /var/log/assessment_deploy.log

# Log da aplicação
tail -f /var/log/assessment.log

# Log de erros
tail -f /var/log/assessment_error.log

# Status do serviço
sudo supervisorctl status assessment
```

## ⚡ Características Técnicas

### Idempotência
- ✅ Pode rodar múltiplas vezes sem problemas
- ✅ Verifica existência antes de criar
- ✅ Não duplica dados

### Performance
- ✅ Índices otimizados para busca rápida
- ✅ Foreign keys com CASCADE para integridade
- ✅ Constraints para validação de dados

### Segurança
- ✅ Detecção de operações destrutivas
- ✅ Backup automático pré-deploy
- ✅ Rollback em caso de erro
- ✅ Validação de estrutura pós-deploy

## 📝 Próximos Passos Após Deploy

1. **Testar Assessment Público**
   - Login como admin
   - Editar Tipo de Assessment
   - Marcar checkbox "URL Pública"
   - Copiar URL gerada
   - Testar em modo anônimo/mobile

2. **Verificar Leads Capturados**
   - Acessar dashboard admin
   - Verificar assessments públicos
   - Visualizar dados coletados

3. **Monitorar Logs**
   - Acompanhar uso da funcionalidade
   - Verificar recomendações IA geradas

## 🆘 Suporte

- **Log completo:** `/var/log/assessment_deploy.log`
- **Backups:** `/var/www/assessment_backups/`
- **Documentação:** `replit.md`
