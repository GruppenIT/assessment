#!/bin/bash
#
# Script de Diagnóstico e Reinício da Aplicação
# Identifica como a aplicação está rodando e reinicia corretamente
#

echo "=========================================="
echo "Diagnóstico da Aplicação Assessment"
echo "=========================================="
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}1. Procurando processos Python/Gunicorn...${NC}"
ps aux | grep -E "python|gunicorn|flask" | grep -v grep
echo ""

echo -e "${YELLOW}2. Verificando portas em uso (5000-5010)...${NC}"
netstat -tuln | grep -E "500[0-9]|5010" || ss -tuln | grep -E "500[0-9]|5010"
echo ""

echo -e "${YELLOW}3. Verificando Supervisor...${NC}"
if command -v supervisorctl &> /dev/null; then
    echo "Supervisor instalado. Status:"
    sudo supervisorctl status 2>/dev/null || echo "Nenhum processo no Supervisor"
else
    echo "Supervisor não instalado"
fi
echo ""

echo -e "${YELLOW}4. Verificando Systemd...${NC}"
if command -v systemctl &> /dev/null; then
    echo "Systemd instalado. Procurando serviços..."
    systemctl list-units --type=service | grep -i assessment || echo "Nenhum serviço 'assessment' encontrado"
    systemctl list-units --type=service | grep -i flask || echo "Nenhum serviço 'flask' encontrado"
    systemctl list-units --type=service | grep -i gunicorn || echo "Nenhum serviço 'gunicorn' encontrado"
else
    echo "Systemd não disponível"
fi
echo ""

echo -e "${YELLOW}5. Procurando scripts de inicialização...${NC}"
ls -la /etc/init.d/ 2>/dev/null | grep -E "assessment|flask|gunicorn" || echo "Nenhum script init.d encontrado"
echo ""

echo -e "${YELLOW}6. Verificando crontab...${NC}"
crontab -l 2>/dev/null | grep -E "assessment|flask|gunicorn" || echo "Nenhuma entrada no crontab"
sudo crontab -l 2>/dev/null | grep -E "assessment|flask|gunicorn" || echo "Nenhuma entrada no crontab root"
echo ""

echo "=========================================="
echo -e "${GREEN}Diagnóstico Concluído${NC}"
echo "=========================================="
echo ""

# Tentar encontrar o PID do processo principal
PID=$(ps aux | grep -E "gunicorn.*main:app|python.*main.py|flask run" | grep -v grep | awk '{print $2}' | head -1)

if [ -n "$PID" ]; then
    echo -e "${GREEN}✓ Aplicação encontrada rodando (PID: $PID)${NC}"
    echo ""
    echo "Para reiniciar a aplicação, execute:"
    echo -e "${YELLOW}  sudo kill -HUP $PID${NC}  (reload graceful)"
    echo "ou"
    echo -e "${YELLOW}  sudo kill $PID && [comando_de_inicio]${NC}  (reinício completo)"
    echo ""
    
    # Perguntar se quer reiniciar
    read -p "Deseja reiniciar a aplicação agora? (s/N): " resposta
    if [[ "$resposta" =~ ^[Ss]$ ]]; then
        echo "Reiniciando aplicação..."
        sudo kill -HUP $PID
        sleep 2
        if ps -p $PID > /dev/null; then
            echo -e "${GREEN}✓ Aplicação reiniciada com sucesso${NC}"
        else
            echo -e "${RED}✗ Processo encerrado. Você precisa iniciá-lo manualmente.${NC}"
        fi
    fi
else
    echo -e "${RED}✗ Aplicação NÃO está rodando${NC}"
    echo ""
    echo "Para iniciar a aplicação, você pode usar:"
    echo -e "${YELLOW}  cd /var/www/assessment${NC}"
    echo -e "${YELLOW}  gunicorn --bind 0.0.0.0:5000 --daemon main:app${NC}"
    echo ""
fi
