#!/bin/bash

echo "======================================================================"
echo "IMPLEMENTAÇÃO: QR CODE NAS ESTATÍSTICAS DE GRUPOS"
echo "======================================================================"
echo ""
echo "O QUE FOI IMPLEMENTADO:"
echo "  ✓ QR Code exibido ao lado das estatísticas (Total, Pontuação, etc.)"
echo "  ✓ Aparece apenas para grupos específicos (NÃO para grupo GERAL)"
echo "  ✓ URL gerada automaticamente: /public/{tipo_id}?group={nome_grupo}"
echo "  ✓ Layout responsivo: 4 cards de estatísticas + 1 card com QR Code"
echo "  ✓ URL exibida abaixo do QR Code para referência"
echo ""
echo "======================================================================"
echo "APLICANDO NO SERVIDOR..."
echo "======================================================================"
echo ""

# Ir para diretório do projeto
cd /var/www/assessment || {
    echo "❌ ERRO: Diretório /var/www/assessment não encontrado"
    exit 1
}

# Fazer backup do estado atual
echo "1. Criando backup..."
git diff > /tmp/backup_antes_qrcode_$(date +%Y%m%d_%H%M%S).patch
echo "   ✓ Backup salvo em /tmp/"
echo ""

# Fazer git pull
echo "2. Atualizando código do repositório..."
git pull origin main || {
    echo "❌ ERRO: Falha ao fazer git pull"
    echo "   Execute: cd /var/www/assessment && git status"
    exit 1
}
echo "   ✓ Código atualizado"
echo ""

# Reiniciar serviço
echo "3. Reiniciando serviço assessment..."
if command -v supervisorctl &> /dev/null; then
    sudo supervisorctl restart assessment
    echo "   ✓ Serviço reiniciado via Supervisor"
elif systemctl is-active --quiet assessment; then
    sudo systemctl restart assessment
    echo "   ✓ Serviço reiniciado via Systemd"
else
    echo "   ⚠ Não foi possível detectar o gerenciador de serviços"
    echo "   Execute manualmente: sudo supervisorctl restart assessment"
fi
echo ""

# Aguardar inicialização
echo "4. Aguardando inicialização (5 segundos)..."
sleep 5
echo "   ✓ Pronto para testar"
echo ""

echo "======================================================================"
echo "✅ IMPLANTAÇÃO CONCLUÍDA!"
echo "======================================================================"
echo ""
echo "COMO TESTAR:"
echo ""
echo "1. Acesse qualquer grupo ESPECÍFICO (não GERAL):"
echo "   Exemplo: /admin/grupos/TreinamentoDia02/7"
echo ""
echo "2. Verifique que aparecem 5 cards na linha de estatísticas:"
echo "   [Total] [Pontuação] [Primeira] [Última] [QR Code]"
echo ""
echo "3. O QR Code deve apontar para:"
echo "   https://assessments.zerobox.com.br/public/7?group=TreinamentoDia02"
echo ""
echo "4. No grupo GERAL (/admin/grupos/geral/7):"
echo "   Aparecem apenas 4 cards (SEM QR Code) ✓"
echo ""
echo "5. Teste escaneando o QR Code com seu celular"
echo "   Deve abrir a página pública do assessment com a tag correta"
echo ""
echo "======================================================================"
echo "EXEMPLO DE USO:"
echo "======================================================================"
echo ""
echo "📱 CENÁRIO: Apresentação com projetor"
echo ""
echo "1. Abra /admin/grupos/SeuGrupo/7 e projete na tela"
echo "2. Participantes escaneiam o QR Code com celular"
echo "3. Respondem o assessment enquanto você vê estatísticas em tempo real"
echo "4. Auto-refresh atualiza dados automaticamente (configurável: 5s, 10s, etc.)"
echo ""
echo "======================================================================"
