# Deploy - Fluxo Sem Atrito para Assessments Públicos

## 📋 O que esta atualização faz?

Esta atualização implementa um **fluxo sem atrito** para assessments públicos, melhorando significativamente a experiência do usuário:

### Antes (com atrito):
1. Usuário responde perguntas
2. Precisa preencher formulário completo (nome, email, telefone, empresa, cargo)
3. Só então vê o resultado
4. Pode imprimir

### Agora (sem atrito):
1. Usuário responde perguntas
2. **Vê resultado IMEDIATAMENTE** (sem preencher nada)
3. **Opcionalmente** pode solicitar envio por email (apenas email)
4. Lead é criado **SOMENTE** quando solicita envio

## 🎯 Benefícios

- ✅ **Maior taxa de conclusão**: Resultado imediato sem barreiras
- ✅ **Menos atrito**: Não precisa preencher formulário antes de ver resultado
- ✅ **Leads qualificados**: Apenas quem realmente quer receber por email fornece dados
- ✅ **Melhor UX**: Fluxo mais natural e menos intrusivo

## 🔧 Como Atualizar (On-Premise)

### Pré-requisitos

- Acesso SSH ao servidor
- Permissões sudo (para reiniciar serviços)
- PostgreSQL configurado
- Git instalado

### Passo a Passo

1. **Conecte ao servidor via SSH:**
   ```bash
   ssh usuario@servidor
   ```

2. **Navegue até o diretório do projeto:**
   ```bash
   cd /caminho/do/projeto
   ```

3. **Execute o script de deployment:**
   ```bash
   ./deploy_fluxo_sem_atrito.sh
   ```

### O que o script faz automaticamente:

1. ✅ Cria backup do banco de dados
2. ✅ Atualiza código do Git
3. ✅ Aplica migrações SQL necessárias
4. ✅ Reinicia a aplicação
5. ✅ Verifica integridade

## 📊 Migrações Aplicadas

O script aplica as seguintes alterações no banco de dados:

```sql
-- Permite que leads sejam criados apenas com email
ALTER TABLE leads ALTER COLUMN nome DROP NOT NULL;
ALTER TABLE leads ALTER COLUMN empresa DROP NOT NULL;
```

**Importante:** As colunas `telefone` e `cargo` já eram opcionais, então não precisam de alteração.

## 🔍 Verificação Pós-Deploy

Após executar o script, verifique:

1. **Aplicação rodando:**
   ```bash
   sudo supervisorctl status assessments
   # ou
   sudo systemctl status assessments.service
   ```

2. **Logs sem erros:**
   ```bash
   sudo tail -f /var/log/assessments/error.log
   ```

3. **Testar fluxo:**
   - Acesse um assessment público
   - Responda as perguntas
   - Verifique se resultado aparece automaticamente
   - Teste o botão de envio por email

## 📧 Configuração de Email (Opcional)

Para que o envio por email funcione, certifique-se de que:

1. **SMTP está configurado:**
   - Acesse: `/admin/parametros/smtp`
   - Configure servidor, porta, credenciais

2. **Destinatários configurados:**
   - Em cada tipo de assessment
   - Configure emails que receberão notificações de novos leads

## 🔄 Rollback (Se necessário)

Se precisar reverter a atualização:

1. **Restaurar backup:**
   ```bash
   psql $DATABASE_URL < backups/backup_antes_fluxo_sem_atrito_YYYYMMDD_HHMMSS.sql
   ```

2. **Reverter código:**
   ```bash
   git reset --hard HEAD~1
   ```

3. **Reiniciar aplicação:**
   ```bash
   sudo supervisorctl restart assessments
   ```

## 📝 Arquivos Modificados

- `models/lead.py` - Campos opcionais
- `forms/publico_forms.py` - Novo formulário de email
- `routes/publico.py` - Nova rota de envio de email
- `utils/email_utils.py` - Função de envio de resultado
- `templates/publico/resultado.html` - Modal de email
- `templates/emails/resultado_assessment.html` - Template de email

## 🆘 Troubleshooting

### Erro: "permission denied" ao executar script
```bash
chmod +x deploy_fluxo_sem_atrito.sh
```

### Erro: "DATABASE_URL not found"
```bash
# Carregue as variáveis de ambiente
source .env
# ou
export DATABASE_URL="postgresql://..."
```

### Erro ao conectar ao banco de dados
```bash
# Verifique se PostgreSQL está rodando
sudo systemctl status postgresql

# Teste conexão
psql $DATABASE_URL -c "SELECT 1"
```

### Aplicação não reinicia
```bash
# Supervisor
sudo supervisorctl restart assessments

# Systemd
sudo systemctl restart assessments.service

# Manual
pkill gunicorn
gunicorn --bind 0.0.0.0:5000 main:app
```

## 📞 Suporte

Se encontrar problemas durante o deployment:

1. Verifique os logs de erro
2. Consulte a documentação completa no `replit.md`
3. Restaure o backup se necessário

---

**Última atualização:** Outubro 2025  
**Versão:** 1.0 - Fluxo Sem Atrito
