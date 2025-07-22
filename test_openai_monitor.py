#!/usr/bin/env python3
"""
Script de teste para monitorar payloads OpenAI
"""

import json

# Teste direto sem imports Flask para evitar circular imports
class TestOpenAIPayloadMonitor:
    """Monitor para rastrear e analisar payloads enviados à OpenAI"""
    
    def calculate_payload_size(self, data):
        """Calcula o tamanho do payload em diferentes métricas"""
        json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        size_bytes = len(json_str.encode('utf-8'))
        size_chars = len(json_str)
        estimated_tokens = size_chars // 4
        
        return {
            'bytes': size_bytes,
            'characters': size_chars,
            'estimated_tokens': estimated_tokens
        }
    
    def analyze_project_payload(self, projeto_data):
        """Analisa especificamente payloads de projetos"""
        analysis = {
            'payload_size': self.calculate_payload_size(projeto_data),
            'warnings': [],
            'recommendations': []
        }
        
        total_tokens = analysis['payload_size']['estimated_tokens']
        
        if total_tokens > 100000:
            analysis['warnings'].append(f"CRÍTICO: Payload muito grande ({total_tokens:,} tokens estimados)")
        elif total_tokens > 50000:
            analysis['warnings'].append(f"ATENÇÃO: Payload grande ({total_tokens:,} tokens estimados)")
        elif total_tokens > 20000:
            analysis['warnings'].append(f"INFO: Payload moderado ({total_tokens:,} tokens estimados)")
        
        return analysis

test_monitor = TestOpenAIPayloadMonitor()

def test_monitor():
    monitor = TestOpenAIPayloadMonitor()
    """Testa o monitor de payload OpenAI"""
    print("🔧 TESTE DO MONITOR DE PAYLOAD OPENAI")
    print("="*50)
    
    # Simular dados de um projeto grande
    projeto_exemplo = {
        "projeto": {
            "nome": "Assessment Extenso - Cibersegurança",
            "data_criacao": "2025-07-22",
            "data_finalizacao": "2025-07-22"
        },
        "cliente": {
            "nome": "Empresa Teste Ltda",
            "razao_social": "Empresa Teste Limitada",
            "localidade": "São Paulo, SP",
            "segmento": "Tecnologia"
        },
        "respondentes": [
            {"nome": "João Silva", "email": "joao@empresa.com"},
            {"nome": "Maria Santos", "email": "maria@empresa.com"}
        ],
        "tipos_assessment": [
            {"nome": "Cibersegurança (NIST / ISO27001 / CIS)", "descricao": "Assessment completo de cibersegurança"}
        ],
        "dominios": []
    }
    
    # Simular múltiplos domínios com muitas perguntas
    for i in range(15):  # 15 domínios
        dominio = {
            "nome": f"Domínio {i+1} - Controles de Segurança",
            "descricao": f"Análise detalhada dos controles de segurança do domínio {i+1}",
            "perguntas": []
        }
        
        # Adicionar muitas perguntas por domínio
        for j in range(15):  # 15 perguntas por domínio = 225 perguntas total
            pergunta = {
                "id": f"{i}_{j}",
                "texto": f"Esta é uma pergunta muito detalhada sobre controles de segurança no domínio {i+1}, questão {j+1}. " * 5,  # Texto longo
                "referencia": "ISO 27001:2022 A.5.1.1, NIST CSF PR.AC-1, CIS Control 5",
                "recomendacao": "Implementar controles baseados em frameworks reconhecidos internacionalmente para garantir conformidade e eficácia.",
                "respostas": [
                    {
                        "respondente": "João Silva",
                        "nota": 3,
                        "comentario": "Atualmente temos alguns controles implementados, mas sabemos que precisa melhorar. Estamos planejando uma revisão completa para 2025 com investimento em novas ferramentas e treinamento da equipe. A política está sendo revista pelo comitê de governança."
                    },
                    {
                        "respondente": "Maria Santos", 
                        "nota": 2,
                        "comentario": "Concordo com o João. Nossos controles são básicos e precisam de upgrade urgente. Temos limitações de budget mas a diretoria aprovou investimentos para o próximo trimestre."
                    }
                ]
            }
            dominio["perguntas"].append(pergunta)
        
        projeto_exemplo["dominios"].append(dominio)
    
    # Analisar payload
    print("📊 Analisando payload do projeto...")
    analysis = monitor.analyze_project_payload(projeto_exemplo)
    
    print(f"\n📈 MÉTRICAS DO PAYLOAD:")
    print(f"   Bytes: {analysis['payload_size']['bytes']:,}")
    print(f"   Caracteres: {analysis['payload_size']['characters']:,}")
    print(f"   Tokens estimados: {analysis['payload_size']['estimated_tokens']:,}")
    
    print(f"\n⚠️  AVISOS ({len(analysis['warnings'])}):")
    for warning in analysis['warnings']:
        print(f"   • {warning}")
    
    print(f"\n💡 RECOMENDAÇÕES ({len(analysis['recommendations'])}):")
    for rec in analysis['recommendations']:
        print(f"   • {rec}")
    
    print(f"\n✅ Teste concluído!")
    
    # Verificar se payload é grande demais
    if analysis['payload_size']['estimated_tokens'] > 100000:
        print(f"\n🚨 ATENÇÃO: Payload muito grande!")
        print(f"   Tokens: {analysis['payload_size']['estimated_tokens']:,}")
        print(f"   Limite GPT-4o: ~128,000 tokens")
        print(f"   Recomendação: Processar em lotes ou otimizar dados")

if __name__ == "__main__":
    test_monitor()