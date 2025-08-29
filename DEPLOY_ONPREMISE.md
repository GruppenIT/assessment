# COMANDO PARA APLICAR SEGURANÇA NA VM ON-PREMISE

## Comando Completo (Copie e Cole)

```bash
curl -sSL https://raw.githubusercontent.com/GruppenIT/assessment/refs/heads/main/deploy_security_onpremise.sh | sudo bash
```

## Alternativa com Download Local

Se preferir baixar e revisar antes de executar:

```bash
# Baixar o script
curl -O https://raw.githubusercontent.com/GruppenIT/assessment/refs/heads/main/deploy_security_onpremise.sh

# Revisar o conteúdo
cat deploy_security_onpremise.sh

# Dar permissão de execução e executar
chmod +x deploy_security_onpremise.sh
sudo bash deploy_security_onpremise.sh
```

## O que o Script Faz

1. **Backup**: Cria backup automático dos arquivos atuais
2. **Patches de Segurança**: Remove rotas inseguras e adiciona proteções
3. **Reinicialização**: Para e reinicia os serviços do assessment
4. **Verificação**: Testa se as proteções estão funcionando
5. **Logs**: Mostra status final e como monitorar

## Verificação Pós-Execução

Após executar, teste se a segurança está ativa:

```bash
# Deve retornar 302 (redirect para login)
curl -I http://localhost:8000/admin/dashboard

# Verificar status do serviço
sudo supervisorctl status assessment

# Monitorar logs em tempo real
sudo tail -f /var/log/assessment.log
```

## Rollback (Se Necessário)

O script cria backup automaticamente. Para reverter:

```bash
# Listar backups disponíveis
ls -la /var/www/assessment/backup_security_*

# Restaurar backup (substitua pela data correta)
sudo cp -r /var/www/assessment/backup_security_YYYYMMDD_HHMMSS/* /var/www/assessment/
sudo supervisorctl restart assessment
```