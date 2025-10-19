#!/bin/bash

###############################################################################
# Script: Correção do Botão Excluir Grupo
# 
# Problema: Botão "Excluir" não funciona por falta de CSRF token no formulário
# Solução: Adicionar csrf_token ao formulário gerado via JavaScript
# 
# Data: 2025-10-19
###############################################################################

set -e

echo "======================================================================"
echo "Corrigindo Botão Excluir Grupo (CSRF Token)"
echo "======================================================================"
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Verificar se está no diretório correto
if [ ! -f "app.py" ]; then
    echo -e "${RED}Erro: Execute este script no diretório raiz do projeto (/var/www/assessment)${NC}"
    exit 1
fi

echo "📁 Diretório: $(pwd)"
echo ""

# Criar backup
BACKUP_DIR="backups/excluir_grupo_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp templates/admin/grupos_lista.html "$BACKUP_DIR/" 2>/dev/null || true
echo -e "${GREEN}✓ Backup criado em: $BACKUP_DIR${NC}"
echo ""

# Puxar mudanças do Git
echo "🔄 Puxando mudanças do repositório..."
git stash 2>/dev/null || true
git pull origin main
echo -e "${GREEN}✓ Código atualizado${NC}"
echo ""

# Reiniciar serviço
echo "🔄 Reiniciando serviço..."
if command -v supervisorctl &> /dev/null; then
    sudo supervisorctl restart assessment
    echo -e "${GREEN}✓ Serviço reiniciado via Supervisor${NC}"
elif [ -f "/etc/systemd/system/assessment.service" ]; then
    sudo systemctl restart assessment
    echo -e "${GREEN}✓ Serviço reiniciado via Systemd${NC}"
else
    echo -e "${YELLOW}⚠ Execute manualmente: sudo systemctl restart assessment${NC}"
fi

echo ""
echo "======================================================================"
echo -e "${GREEN}✓ Botão Excluir corrigido com sucesso!${NC}"
echo "======================================================================"
echo ""
echo "📝 O que foi corrigido:"
echo ""
echo "✅ Adicionado CSRF token no formulário de exclusão"
echo "✅ Botão 'Excluir' agora funciona corretamente"
echo ""
echo "🧪 Como testar:"
echo ""
echo "1. Acesse /admin/grupos"
echo "2. Clique em 'Excluir' em um grupo específico (não nos GERAIS)"
echo "3. Confirme a exclusão no diálogo"
echo "4. O grupo será removido com todos seus assessments"
echo ""
echo "💾 Backup salvo em: $BACKUP_DIR"
echo ""
