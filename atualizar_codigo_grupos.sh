#!/bin/bash

###############################################################################
# Script: Atualização Rápida - Código de Grupos
# 
# Atualiza apenas os arquivos relacionados à funcionalidade de grupos
###############################################################################

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "======================================================================"
echo "Atualização Rápida: Código de Grupos"
echo "======================================================================"
echo ""

# Verificar diretório
if [ ! -f "app.py" ]; then
    echo -e "${RED}Erro: Execute no diretório raiz do projeto (/var/www/assessment)${NC}"
    exit 1
fi

echo -e "${BLUE}📁 Diretório: $(pwd)${NC}"
echo ""

# Fazer backup
BACKUP_DIR="backups/update_grupos_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp routes/admin.py "$BACKUP_DIR/" 2>/dev/null || true
cp templates/admin/grupos_lista.html "$BACKUP_DIR/" 2>/dev/null || true
cp templates/admin/grupos_estatisticas.html "$BACKUP_DIR/" 2>/dev/null || true
echo -e "${GREEN}✓ Backup criado em: $BACKUP_DIR${NC}"
echo ""

# Verificar status atual
echo -e "${BLUE}📊 Status do Git:${NC}"
git status
echo ""

# Salvar mudanças locais
echo -e "${BLUE}💾 Salvando mudanças locais (se houver)...${NC}"
git stash
echo ""

# Puxar atualizações
echo -e "${BLUE}🔄 Puxando atualizações do repositório...${NC}"
git pull origin main
echo ""

# Restaurar mudanças locais (se houver)
echo -e "${BLUE}📥 Restaurando mudanças locais...${NC}"
git stash pop 2>/dev/null || echo "Nenhuma mudança local para restaurar"
echo ""

# Mostrar arquivos atualizados
echo -e "${BLUE}📝 Arquivos importantes:${NC}"
echo ""

echo "1. routes/admin.py - Última modificação:"
ls -lh routes/admin.py
echo ""

echo "2. templates/admin/grupos_lista.html - Última modificação:"
ls -lh templates/admin/grupos_lista.html
echo ""

echo "3. templates/admin/grupos_estatisticas.html - Última modificação:"
ls -lh templates/admin/grupos_estatisticas.html
echo ""

# Verificar se a função existe
echo -e "${BLUE}🔍 Verificando código...${NC}"
echo ""

if grep -q "def excluir_grupo" routes/admin.py; then
    echo -e "${GREEN}✓ Rota excluir_grupo encontrada em routes/admin.py${NC}"
else
    echo -e "${RED}✗ Rota excluir_grupo NÃO encontrada em routes/admin.py${NC}"
fi

if grep -q "function confirmarExclusao" templates/admin/grupos_lista.html; then
    echo -e "${GREEN}✓ Função confirmarExclusao encontrada em grupos_lista.html${NC}"
else
    echo -e "${RED}✗ Função confirmarExclusao NÃO encontrada em grupos_lista.html${NC}"
fi

if grep -q "onclick.*confirmarExclusao" templates/admin/grupos_lista.html; then
    echo -e "${GREEN}✓ Botão com onclick encontrado em grupos_lista.html${NC}"
    echo ""
    echo "Código do botão:"
    grep -A 2 "onclick.*confirmarExclusao" templates/admin/grupos_lista.html
else
    echo -e "${RED}✗ Botão com onclick NÃO encontrado em grupos_lista.html${NC}"
fi
echo ""

# Reiniciar serviço
echo -e "${BLUE}🔄 Reiniciando serviço...${NC}"
if command -v supervisorctl &> /dev/null; then
    sudo supervisorctl restart assessment
    echo -e "${GREEN}✓ Serviço reiniciado via Supervisor${NC}"
    echo ""
    echo "Status:"
    sudo supervisorctl status assessment
elif [ -f "/etc/systemd/system/assessment.service" ]; then
    sudo systemctl restart assessment
    echo -e "${GREEN}✓ Serviço reiniciado via Systemd${NC}"
    echo ""
    echo "Status:"
    sudo systemctl status assessment --no-pager -l
fi
echo ""

echo "======================================================================"
echo -e "${GREEN}✓ Atualização concluída!${NC}"
echo "======================================================================"
echo ""
echo "📋 Próximos passos:"
echo ""
echo "1. Aguarde 5 segundos para o serviço iniciar completamente"
echo "2. Acesse http://seu-dominio/admin/grupos"
echo "3. Abra o Console do Navegador (F12)"
echo "4. Clique no botão 'Excluir' de um grupo"
echo "5. Observe se aparece o popup de confirmação"
echo ""
echo "Se AINDA não funcionar, execute:"
echo "  ./troubleshoot_excluir_grupo.sh"
echo ""
