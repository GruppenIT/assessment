#!/usr/bin/env python3
"""
Debug script para testar processamento de quebras de linha
"""

def test_linebreak_processing():
    """Testa como quebras de linha são processadas"""
    
    # Texto com quebras de linha simples e duplas
    texto_original = """Este é o primeiro parágrafo.

Este é o segundo parágrafo.
E esta é uma segunda linha do parágrafo.

Terceiro parágrafo aqui."""
    
    print("🔧 TESTE DE PROCESSAMENTO DE QUEBRAS DE LINHA")
    print("="*60)
    
    print("📝 TEXTO ORIGINAL:")
    print(repr(texto_original))
    print("\nVisualizando:")
    print(texto_original)
    
    # Simular processamento atual (problema)
    print("\n🚨 PROCESSAMENTO ATUAL (PROBLEMÁTICO):")
    import re
    texto_limpo = re.sub(r'<[^>]+>', '', texto_original)
    paragrafos = texto_limpo.split('\n\n')
    
    print(f"Dividido em {len(paragrafos)} parágrafos:")
    for i, paragrafo in enumerate(paragrafos, 1):
        if paragrafo.strip():
            paragrafo_processado = paragrafo.strip()  # Remove quebras simples
            print(f"  Parágrafo {i}: {repr(paragrafo_processado)}")
    
    # Novo processamento (solução)
    print("\n✅ NOVO PROCESSAMENTO (CORRIGIDO):")
    paragrafos_novos = texto_limpo.split('\n\n')
    
    print(f"Dividido em {len(paragrafos_novos)} parágrafos:")
    for i, paragrafo in enumerate(paragrafos_novos, 1):
        if paragrafo.strip():
            # Preservar quebras simples convertendo para <br/>
            paragrafo_formatado = paragrafo.strip().replace('\n', '<br/>')
            print(f"  Parágrafo {i}: {repr(paragrafo_formatado)}")
    
    print("\n📊 RESULTADO:")
    print("- Problema: quebras de linha simples (\\n) eram removidas com .strip()")
    print("- Solução: preservar quebras simples convertendo para <br/> no ReportLab")
    print("- Quebras duplas (\\n\\n) continuam separando parágrafos")

if __name__ == "__main__":
    test_linebreak_processing()