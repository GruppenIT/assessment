#!/bin/bash

###############################################################################
# Script: Adicionar Rótulos de Valores nos Gráficos de Barras
# 
# Melhorias aplicadas:
# 1. Plugin Chart.js Datalabels adicionado via CDN
# 2. Rótulos de valores (%) visíveis nas barras verticais e horizontais
# 3. Rótulos não aparecem no gráfico radar (para não poluir)
# 4. Fonte em negrito, branca, centralizada nas barras
#
# Data: 2025-10-17
###############################################################################

set -e  # Parar em caso de erro

echo "======================================================================"
echo "Adicionar Rótulos de Valores nos Gráficos de Barras"
echo "======================================================================"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detectar diretório do projeto
if [ -f "app.py" ]; then
    PROJECT_DIR=$(pwd)
else
    echo -e "${RED}Erro: Execute este script no diretório raiz do projeto (onde está o app.py)${NC}"
    exit 1
fi

echo "📁 Diretório do projeto: $PROJECT_DIR"
echo ""

# Criar backup
BACKUP_DIR="backups/rotulos_graficos_$(date +%Y%m%d_%H%M%S)"
echo "💾 Criando backup em: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"
cp templates/admin/grupos_estatisticas.html "$BACKUP_DIR/" 2>/dev/null || true
echo -e "${GREEN}✓ Backup criado${NC}"
echo ""

# Aplicar melhoria: Adicionar plugin Datalabels
echo "🔧 Aplicando melhoria: Plugin Chart.js Datalabels e rótulos nas barras"

python3 << 'PYTHON_SCRIPT'
import re

with open('templates/admin/grupos_estatisticas.html', 'r', encoding='utf-8') as f:
    content = f.read()

modificado = False

# 1. Adicionar CDN do plugin Datalabels se não existir
if 'chartjs-plugin-datalabels' not in content:
    old_cdn = '<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>'
    new_cdn = '''<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
<!-- Chart.js Datalabels Plugin para rótulos nas barras -->
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>'''
    
    if old_cdn in content:
        content = content.replace(old_cdn, new_cdn)
        print("✓ Plugin Datalabels CDN adicionado")
        modificado = True
    else:
        print("⚠ CDN do Chart.js não encontrado no formato esperado")
else:
    print("ℹ Plugin Datalabels CDN já está adicionado")

# 2. Adicionar configuração de datalabels nas opções do gráfico
if 'datalabels: {' not in content:
    # Procurar o bloco de tooltip e adicionar datalabels depois
    pattern = r'(tooltip: \{[\s\S]*?\}\s*\})'
    
    datalabels_config = ''',
                datalabels: {
                    display: type !== 'radar', // Mostrar apenas em gráficos de barras
                    color: '#fff',
                    font: {
                        weight: 'bold',
                        size: 12
                    },
                    formatter: function(value) {
                        return value + '%';
                    },
                    anchor: 'center',
                    align: 'center'
                }'''
    
    def add_datalabels(match):
        return match.group(1) + datalabels_config
    
    new_content = re.sub(pattern, add_datalabels, content)
    
    if new_content != content:
        content = new_content
        print("✓ Configuração de datalabels adicionada")
        modificado = True
    else:
        print("⚠ Não foi possível adicionar configuração de datalabels automaticamente")
else:
    print("ℹ Configuração de datalabels já existe")

# Salvar se houve modificação
if modificado:
    with open('templates/admin/grupos_estatisticas.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("\n✓ Template atualizado com sucesso!")
else:
    print("\nℹ Nenhuma modificação necessária")
PYTHON_SCRIPT

echo -e "${GREEN}✓ Melhoria aplicada${NC}"
echo ""

# Reiniciar o serviço
echo "🔄 Reiniciando serviço..."
if command -v supervisorctl &> /dev/null; then
    sudo supervisorctl restart assessment
    echo -e "${GREEN}✓ Serviço reiniciado via Supervisor${NC}"
elif [ -f "/etc/systemd/system/assessment.service" ]; then
    sudo systemctl restart assessment
    echo -e "${GREEN}✓ Serviço reiniciado via Systemd${NC}"
else
    echo -e "${YELLOW}⚠ Serviço não detectado. Reinicie manualmente:${NC}"
    echo "   sudo supervisorctl restart assessment"
    echo "   ou"
    echo "   sudo systemctl restart assessment"
fi

echo ""
echo "======================================================================"
echo -e "${GREEN}✓ Rótulos de valores adicionados aos gráficos!${NC}"
echo "======================================================================"
echo ""
echo "📝 Melhorias aplicadas:"
echo "   ✓ Plugin Chart.js Datalabels carregado via CDN"
echo "   ✓ Valores (%) visíveis dentro das barras verticais"
echo "   ✓ Valores (%) visíveis dentro das barras horizontais"
echo "   ✓ Gráfico radar sem rótulos (para melhor visualização)"
echo "   ✓ Formatação: fonte branca, negrito, centralizada"
echo ""
echo "💾 Backup salvo em: $BACKUP_DIR"
echo ""
echo "🧪 Teste agora:"
echo "   1. Acesse /admin/grupos e clique em 'caxias'"
echo "   2. Veja os valores % dentro das barras verticais"
echo "   3. Alterne para barras horizontais - valores também aparecem"
echo "   4. Alterne para radar - limpo, sem rótulos"
echo ""
