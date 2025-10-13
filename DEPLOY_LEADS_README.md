# Deployment do Sistema de Leads - Guia Completo

## 📋 Sobre o Sistema de Leads

O sistema de leads gerencia automaticamente os contatos gerados a partir de assessments públicos, permitindo:

- **Captura automática**: Leads criados quando alguém responde um assessment público
- **Gestão completa**: Status, prioridades, atribuição a usuários, comentários
- **Histórico detalhado**: Timeline completa de todas as interações
- **Análise de pontuação**: Visualização das pontuações do assessment respondido
- **Funil de vendas**: Acompanhamento desde "Novo" até "Ganho/Perdido"

## 🚀 Como Fazer o Deployment

### Pré-requisitos

- Acesso root ou sudo ao servidor
- Aplicação já instalada em `/var/www/assessment`
- PostgreSQL rodando
- Supervisor configurado

### Passo a Passo

1. **Fazer upload do script para o servidor:**

```bash
# Copie o arquivo deploy_onpremise_com_leads.sh para o servidor
scp deploy_onpremise_com_leads.sh root@seu-servidor:/tmp/
```

2. **Dar permissão de execução:**

```bash
ssh root@seu-servidor
chmod +x /tmp/deploy_onpremise_com_leads.sh
```

3. **Executar o deployment:**

```bash
sudo /tmp/deploy_onpremise_com_leads.sh
```

4. **Confirmar quando solicitado:**

```
Deseja continuar com o deployment? (s/N): s
```

### O Que o Script Faz

O script executa as seguintes etapas automaticamente:

1. ✅ **Backup Completo** - Cria backup do banco antes de qualquer mudança
2. ✅ **Parar Aplicação** - Para o serviço de forma segura
3. ✅ **Atualizar Código** - Faz git pull das últimas mudanças
4. ✅ **Criar Tabelas** - Adiciona tabelas `leads` e `leads_historico`
5. ✅ **Criar Índices** - Otimiza performance com índices apropriados
6. ✅ **Verificar Estrutura** - Valida que tudo foi criado corretamente
7. ✅ **Atualizar Dependências** - Instala novos pacotes Python se necessário
8. ✅ **Reiniciar Aplicação** - Inicia o serviço novamente
9. ✅ **Verificação Final** - Checa logs por erros

### Segurança e Rollback

- **Zero perda de dados**: Todos os dados existentes são preservados
- **Backup automático**: Criado antes de qualquer mudança
- **Rollback automático**: Em caso de erro, restaura o backup
- **Operações idempotentes**: Pode ser executado múltiplas vezes sem problemas

### Localização dos Arquivos

Após o deployment, os seguintes arquivos estarão disponíveis:

```
/var/www/assessment/backups/
├── backup_pre_leads_YYYYMMDD_HHMMSS.sql     # Backup do banco
└── deploy_leads_YYYYMMDD_HHMMSS.log         # Log do deployment
```

## 📊 Estrutura do Banco de Dados

### Tabela: `leads`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | SERIAL | ID único do lead |
| assessment_publico_id | INTEGER | Assessment que gerou o lead |
| nome | VARCHAR(200) | Nome completo |
| email | VARCHAR(200) | Email de contato |
| telefone | VARCHAR(20) | Telefone (opcional) |
| cargo | VARCHAR(100) | Cargo na empresa |
| empresa | VARCHAR(200) | Nome da empresa |
| tipo_assessment_nome | VARCHAR(200) | Tipo de assessment respondido |
| pontuacao_geral | FLOAT | Pontuação geral (0-100) |
| pontuacoes_dominios | JSON | Pontuações por domínio |
| status | VARCHAR(50) | Status do lead |
| prioridade | VARCHAR(20) | Prioridade (baixa/media/alta) |
| comentarios | TEXT | Comentários do admin |
| data_criacao | TIMESTAMP | Data de criação |
| data_atualizacao | TIMESTAMP | Última atualização |
| atribuido_a_id | INTEGER | Usuário responsável |

### Tabela: `leads_historico`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | SERIAL | ID único |
| lead_id | INTEGER | Lead relacionado |
| usuario_id | INTEGER | Usuário que fez a ação |
| acao | VARCHAR(100) | Tipo de ação |
| detalhes | TEXT | Detalhes da ação |
| data_registro | TIMESTAMP | Data do registro |

### Status Disponíveis

- `novo` - Lead recém criado
- `contatado` - Primeiro contato realizado
- `qualificado` - Lead qualificado como oportunidade
- `proposta` - Proposta enviada
- `negociacao` - Em negociação
- `ganho` - Venda fechada
- `perdido` - Oportunidade perdida

## 🎯 Como Usar o Sistema

### 1. Acessar Dashboard de Leads

Após o deployment, acesse:

```
https://assessments.zerobox.com.br/admin/leads
```

### 2. Gerar Leads de Teste

Para gerar um lead de teste:

1. Acesse um assessment público: `https://assessments.zerobox.com.br/public/1`
2. Responda as perguntas
3. Preencha os dados do respondente
4. Um lead será criado automaticamente

### 3. Gerenciar Leads

No dashboard de leads você pode:

- **Filtrar** por status, prioridade ou buscar por nome/email/empresa
- **Visualizar estatísticas** de conversão
- **Acessar detalhes** de cada lead
- **Atualizar status** e prioridade
- **Adicionar comentários** e notas
- **Atribuir** leads a usuários específicos
- **Ver histórico** completo de interações

### 4. Detalhes do Lead

Na página de detalhes de cada lead:

- **Informações completas** do respondente
- **Pontuações do assessment** (geral e por domínio)
- **Link para resultado** completo do assessment
- **Timeline de interações** com histórico visual
- **Formulário de atualização** de status/prioridade
- **Adição rápida de comentários**

## 🔧 Troubleshooting

### Erro: "Não foi possível detectar as credenciais do banco"

**Solução:** Verifique se o arquivo `.env` existe ou se as variáveis estão no supervisor:

```bash
cat /var/www/assessment/.env
# OU
cat /etc/supervisor/conf.d/assessment.conf
```

### Erro: "Aplicação não está rodando"

**Solução:** Verifique os logs:

```bash
sudo supervisorctl tail assessment stderr
```

### Erro: "Tabelas já existem"

**Não é um problema!** O script é idempotente e pode ser executado múltiplas vezes.

### Restaurar Backup Manualmente

Se necessário, restaure o backup:

```bash
# Listar backups disponíveis
ls -lah /var/www/assessment/backups/backup_pre_leads_*

# Restaurar um backup específico
sudo -u postgres psql -d assessment_db < /var/www/assessment/backups/backup_pre_leads_YYYYMMDD_HHMMSS.sql
```

## 📈 Integrações

### Criação Automática de Leads

Leads são criados automaticamente quando:

1. Um usuário acessa um assessment público (URL pública ativada)
2. Responde todas as perguntas
3. Preenche os dados do respondente
4. Conclui o assessment

O sistema captura:
- Dados pessoais e profissionais
- Pontuação geral e por domínio
- Tipo de assessment respondido
- Data e hora da resposta

### Fluxo de Dados

```
Assessment Público → Respostas → Dados Respondente → Lead Criado → Dashboard Admin
```

## 🎨 Personalização

### Adicionar Novos Status

Edite o arquivo `forms/lead_forms.py`:

```python
status = SelectField('Status', 
    choices=[
        ('novo', 'Novo'),
        ('contatado', 'Contatado'),
        # Adicione novos status aqui
        ('seu_status', 'Seu Status'),
    ])
```

### Campos Personalizados

Para adicionar campos ao lead, edite `models/lead.py` e crie uma migração.

## 📝 Logs e Monitoramento

### Verificar Logs da Aplicação

```bash
# Ver logs em tempo real
sudo supervisorctl tail -f assessment stderr

# Ver últimas 100 linhas
sudo supervisorctl tail assessment stderr | tail -100
```

### Verificar Logs do Deployment

```bash
# Listar logs de deployment
ls -lah /var/www/assessment/backups/*.log

# Ver último deployment
tail -50 /var/www/assessment/backups/deploy_leads_*.log | tail -1
```

## ✅ Checklist Pós-Deployment

- [ ] Aplicação rodando sem erros
- [ ] Dashboard de leads acessível
- [ ] Tabelas criadas no banco de dados
- [ ] Assessment público gerando leads
- [ ] Filtros e busca funcionando
- [ ] Atualização de status funcionando
- [ ] Histórico sendo registrado
- [ ] Backup criado com sucesso

## 🆘 Suporte

Em caso de problemas:

1. Verifique o log do deployment em `/var/www/assessment/backups/`
2. Verifique os logs da aplicação com `supervisorctl tail assessment stderr`
3. Verifique se as tabelas foram criadas: `SELECT * FROM leads LIMIT 1;`
4. Teste criar um lead manualmente respondendo um assessment público

---

**Versão:** 1.0  
**Data:** 2025-10-11  
**Compatibilidade:** PostgreSQL 12+, Python 3.10+
