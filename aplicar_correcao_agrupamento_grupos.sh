#!/bin/bash

###############################################################################
# Script: Correção Conceitual do Agrupamento de Grupos
# 
# MUDANÇA CONCEITUAL IMPORTANTE:
# ===============================
# 
# ANTES:
#   Grupos eram agrupados apenas pela TAG do parâmetro ?group=nome
#   Problema: /public/3?group=teste e /public/7?group=teste apareciam juntos
# 
# DEPOIS:
#   Grupos são agrupados pela DUPLA (TAG + TIPO_ASSESSMENT_ID)
#   Solução: /public/3?group=teste e /public/7?group=teste são grupos SEPARADOS
# 
# Isso permite análises mais precisas por campanha + tipo de assessment!
#
# Mudanças implementadas:
# 1. Rota /admin/grupos agora agrupa por (grupo, tipo_assessment_id)
# 2. Template grupos_lista.html mostra coluna "Tipo de Assessment"
# 3. URLs mudaram de /grupos/<nome> para /grupos/<nome>/<tipo_id>
# 4. API endpoint agora requer tipo_id: /grupos/<nome>/<tipo_id>/api
# 5. Função calcular_estatisticas_grupo() filtra por ambos os parâmetros
#
# Data: 2025-10-19
###############################################################################

set -e

echo "======================================================================"
echo "Aplicando Correção Conceitual do Agrupamento de Grupos"
echo "======================================================================"
echo ""

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Verificar diretório
if [ ! -f "app.py" ]; then
    echo -e "${RED}Erro: Execute no diretório raiz do projeto${NC}"
    exit 1
fi

echo "📁 Diretório: $(pwd)"
echo ""

# Criar backup
BACKUP_DIR="backups/agrupamento_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp routes/admin.py "$BACKUP_DIR/"
cp templates/admin/grupos_lista.html "$BACKUP_DIR/"
cp templates/admin/grupos_estatisticas.html "$BACKUP_DIR/"
echo -e "${GREEN}✓ Backup criado em: $BACKUP_DIR${NC}"
echo ""

# Puxar correção do Git
echo "🔄 Puxando correção do repositório..."
git pull origin main

echo ""
echo -e "${YELLOW}⚠️  IMPORTANTE: Mudança de URL${NC}"
echo ""
echo "As URLs antigas não funcionarão mais:"
echo "  ❌ /admin/grupos/teste"
echo ""
echo "Novas URLs incluem o tipo de assessment:"
echo "  ✅ /admin/grupos/teste/3"
echo "  ✅ /admin/grupos/teste/7"
echo ""
echo "Bookmarks antigos precisam ser atualizados!"
echo ""

# Reiniciar serviço
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
echo -e "${GREEN}✓ Correção conceitual aplicada com sucesso!${NC}"
echo "======================================================================"
echo ""
echo "📝 Mudanças aplicadas:"
echo "   ✅ Agrupamento por (TAG + TIPO_ASSESSMENT_ID)"
echo "   ✅ Coluna 'Tipo de Assessment' na lista de grupos"
echo "   ✅ URLs atualizadas para /grupos/<nome>/<tipo_id>"
echo "   ✅ API endpoint com tipo_id obrigatório"
echo "   ✅ Filtros refinados para análises precisas"
echo ""
echo "💾 Backup salvo em: $BACKUP_DIR"
echo ""
echo "🧪 Como testar:"
echo "   1. Crie duas respostas públicas:"
echo "      - /public/3?group=teste"
echo "      - /public/7?group=teste"
echo "   2. Acesse /admin/grupos"
echo "   3. Você verá DOIS grupos separados:"
echo "      • 'teste' (Tipo: Nome do Assessment 3)"
echo "      • 'teste' (Tipo: Nome do Assessment 7)"
echo "   4. Clique em cada um para ver estatísticas independentes"
echo ""
echo "📊 Exemplo de uso:"
echo "   • Campanha 'linkedin' com Assessment de Cybersecurity (ID 3)"
echo "   • Campanha 'linkedin' com Assessment de LGPD (ID 7)"
echo "   → Análises separadas e precisas por tipo!"
echo ""
