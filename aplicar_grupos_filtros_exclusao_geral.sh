#!/bin/bash

###############################################################################
# Script: Grupos - Filtros, Exclusão e Grupo Geral
# 
# Funcionalidades implementadas:
# 
# 1. FILTROS NA PÁGINA /admin/grupos:
#    - Filtrar por tipo de assessment (dropdown)
#    - Filtrar por nome da tag (campo de busca com ILIKE)
#    - Botão "Limpar Filtros" quando há filtros ativos
# 
# 2. EXCLUSÃO DE GRUPOS:
#    - Botão "Excluir" para grupos específicos (não disponível para grupo geral)
#    - Confirmação JavaScript antes da exclusão
#    - Exclui TODOS os assessments públicos do grupo (cascata: respostas + leads)
#    - Rota POST: /admin/grupos/<tag>/<tipo_id>/delete
# 
# 3. GRUPO "GERAL" PARA CADA TIPO:
#    - Mostra estatísticas de TODAS as respostas de um tipo
#    - Aparece no topo da lista com ícone 📊
#    - URLs especiais: /admin/grupos/geral/<tipo_id>
#    - API: /admin/grupos/geral/<tipo_id>/api (auto-refresh)
#    - Não pode ser excluído
# 
# LÓGICA DO GRUPO GERAL:
#    - Responder SEM ?group= → alimenta APENAS grupo geral
#    - Responder COM ?group=xyz → alimenta grupo geral + grupo específico xyz
# 
# Data: 2025-10-19
###############################################################################

set -e

echo "======================================================================"
echo "Aplicando: Grupos - Filtros, Exclusão e Grupo Geral"
echo "======================================================================"
echo ""

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Verificar diretório
if [ ! -f "app.py" ]; then
    echo -e "${RED}Erro: Execute no diretório raiz do projeto${NC}"
    exit 1
fi

echo "📁 Diretório: $(pwd)"
echo ""

# Criar backup
BACKUP_DIR="backups/grupos_filtros_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp routes/admin.py "$BACKUP_DIR/"
cp templates/admin/grupos_lista.html "$BACKUP_DIR/"
cp templates/admin/grupos_estatisticas.html "$BACKUP_DIR/"
echo -e "${GREEN}✓ Backup criado em: $BACKUP_DIR${NC}"
echo ""

# Puxar correção do Git
echo "🔄 Puxando mudanças do repositório..."
git pull origin main

echo ""
echo "🔄 Reiniciando serviço..."
if command -v supervisorctl &> /dev/null; then
    sudo supervisorctl restart assessment
    echo -e "${GREEN}✓ Serviço reiniciado via Supervisor${NC}"
elif [ -f "/etc/systemd/system/assessment.service" ]; then
    sudo systemctl restart assessment
    echo -e "${GREEN}✓ Serviço reiniciado via Systemd${NC}"
fi

echo ""
echo "======================================================================"
echo -e "${GREEN}✓ Grupos com Filtros, Exclusão e Grupo Geral implementado!${NC}"
echo "======================================================================"
echo ""
echo "📝 Funcionalidades adicionadas:"
echo ""
echo -e "${BLUE}1. FILTROS:${NC}"
echo "   ✅ Dropdown para filtrar por tipo de assessment"
echo "   ✅ Campo de busca para filtrar por tag/grupo"
echo "   ✅ Botão 'Limpar Filtros' quando há filtros ativos"
echo "   ✅ Preservação dos filtros na URL"
echo ""
echo -e "${BLUE}2. EXCLUSÃO DE GRUPOS:${NC}"
echo "   ✅ Botão 'Excluir' para grupos específicos"
echo "   ✅ Confirmação antes de excluir"
echo "   ✅ Exclui todos os assessments do grupo (+ respostas + leads)"
echo "   ✅ Grupo geral NÃO pode ser excluído"
echo ""
echo -e "${BLUE}3. GRUPO GERAL:${NC}"
echo "   ✅ Um grupo geral para cada tipo de assessment"
echo "   ✅ Mostra TODAS as respostas do tipo (com ou sem tag)"
echo "   ✅ Ícone especial 📊 GERAL"
echo "   ✅ URL: /admin/grupos/geral/<tipo_id>"
echo "   ✅ Auto-refresh funcional"
echo ""
echo "💾 Backup salvo em: $BACKUP_DIR"
echo ""
echo "🧪 Como testar:"
echo ""
echo "1. FILTROS:"
echo "   - Acesse /admin/grupos"
echo "   - Use o dropdown para filtrar por tipo"
echo "   - Digite parte de uma tag no campo de busca"
echo "   - Clique em 'Filtrar'"
echo ""
echo "2. GRUPO GERAL:"
echo "   - Você verá grupos '📊 GERAL' no topo para cada tipo"
echo "   - Clique em 'Ver Estatísticas' para ver TODAS as respostas"
echo "   - Auto-refresh funcionará normalmente"
echo ""
echo "3. EXCLUSÃO:"
echo "   - Para grupos específicos, clique em 'Excluir'"
echo "   - Confirme a exclusão"
echo "   - Todos os assessments daquele grupo serão removidos"
echo ""
echo "📊 Exemplos:"
echo "   • Grupo GERAL (Tipo: Cybersecurity) → Todas as respostas de cybersecurity"
echo "   • Grupo 'linkedin' (Tipo: Cybersecurity) → Apenas /public/3?group=linkedin"
echo "   • Grupo 'linkedin' (Tipo: LGPD) → Apenas /public/7?group=linkedin"
echo ""
