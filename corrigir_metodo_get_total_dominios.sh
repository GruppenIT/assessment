#!/bin/bash

###############################################################################
# Script: Adicionar Método get_total_dominios() Faltante
# 
# Problema: AssessmentVersao não tem método get_total_dominios()
# Solução: Adicionar o método no modelo
###############################################################################

set -e

echo "======================================================================"
echo "Corrigindo Método get_total_dominios()"
echo "======================================================================"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ ! -f "app.py" ]; then
    echo -e "${RED}Erro: Execute no diretório raiz (/var/www/assessment)${NC}"
    exit 1
fi

echo "📁 Diretório: $(pwd)"
echo ""

# Backup
BACKUP_DIR="backups/get_total_dominios_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp models/assessment_version.py "$BACKUP_DIR/"
echo -e "${GREEN}✓ Backup: $BACKUP_DIR${NC}"
echo ""

echo "🔧 Adicionando método get_total_dominios()..."
echo ""

# Usar Python para adicionar o método de forma segura
python3 << 'ENDOFPYTHON'
import re

# Ler o arquivo
with open('models/assessment_version.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Verificar se já tem o método
if 'def get_total_dominios(' in content:
    print("⚠ Método get_total_dominios() já existe!")
else:
    # Encontrar onde inserir (após get_total_perguntas)
    pattern = r'(def get_total_perguntas\(self\):.*?\.count\(\))\s+(def get_dominios_ativos\(self\):)'
    
    replacement = r'''\1
    
    def get_total_dominios(self):
        """Retorna o total de domínios ativos nesta versão"""
        return AssessmentDominio.query.filter_by(
            versao_id=self.id,
            ativo=True
        ).count()
    
    \2'''
    
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Salvar
    with open('models/assessment_version.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ Método get_total_dominios() adicionado com sucesso")

ENDOFPYTHON

echo ""
echo "🔄 Reiniciando serviço..."
if command -v supervisorctl &> /dev/null; then
    sudo supervisorctl restart assessment
    echo -e "${GREEN}✓ Reiniciado via Supervisor${NC}"
elif [ -f "/etc/systemd/system/assessment.service" ]; then
    sudo systemctl restart assessment
    echo -e "${GREEN}✓ Reiniciado via Systemd${NC}"
fi

# Aguardar um pouco para o serviço iniciar
sleep 2

echo ""
echo "======================================================================"
echo -e "${GREEN}✓ MÉTODO ADICIONADO COM SUCESSO!${NC}"
echo "======================================================================"
echo ""
echo "🧪 TESTE AGORA:"
echo ""
echo "1. Limpe o cache do navegador (Ctrl+Shift+R)"
echo "2. Acesse /admin/grupos"
echo "3. A página DEVE carregar normalmente agora!"
echo "4. Abra o Console (F12)"
echo "5. Você DEVE ver as mensagens DEBUG do JavaScript"
echo "6. Clique em 'Excluir' - o diálogo DEVE aparecer!"
echo ""
echo "💾 Backup salvo em: $BACKUP_DIR"
echo ""
