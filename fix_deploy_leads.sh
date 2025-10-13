#!/bin/bash

# Script de correção rápida para deploy_onpremise_com_leads.sh
# Corrige qualquer typo "cho" → "echo" no script

echo "Corrigindo script de deployment..."

if [ -f "/tmp/deploy_onpremise_com_leads.sh" ]; then
    # Fazer backup do script problemático
    cp /tmp/deploy_onpremise_com_leads.sh /tmp/deploy_onpremise_com_leads.sh.bak
    
    # Corrigir typo
    sed -i 's/^cho /echo /g' /tmp/deploy_onpremise_com_leads.sh
    sed -i 's/ cho / echo /g' /tmp/deploy_onpremise_com_leads.sh
    
    echo "✓ Script corrigido!"
    echo ""
    echo "Execute novamente:"
    echo "  sudo /tmp/deploy_onpremise_com_leads.sh"
else
    echo "❌ Arquivo /tmp/deploy_onpremise_com_leads.sh não encontrado"
    echo ""
    echo "Faça upload novamente do script correto:"
    echo "  scp deploy_onpremise_com_leads.sh root@servidor:/tmp/"
fi
