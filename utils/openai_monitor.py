"""
Monitor para payloads OpenAI e métricas de performance
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional

class OpenAIPayloadMonitor:
    """Monitor para rastrear e analisar payloads enviados à OpenAI"""
    
    def __init__(self):
        self.metrics = {
            'total_requests': 0,
            'total_tokens_input': 0,
            'total_tokens_output': 0,
            'avg_response_time': 0,
            'large_payload_warnings': 0,
            'request_history': []
        }
    
    def calculate_payload_size(self, data: Any) -> Dict[str, int]:
        """Calcula o tamanho do payload em diferentes métricas"""
        
        # Converter para JSON string para medições precisas
        json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        
        # Calcular tamanhos
        size_bytes = len(json_str.encode('utf-8'))
        size_chars = len(json_str)
        
        # Estimativa aproximada de tokens (1 token ≈ 4 caracteres para texto em português)
        estimated_tokens = size_chars // 4
        
        return {
            'bytes': size_bytes,
            'characters': size_chars,
            'estimated_tokens': estimated_tokens,
            'json_string': json_str[:500] + '...' if len(json_str) > 500 else json_str  # Amostra para debug
        }
    
    def analyze_project_payload(self, projeto_data: Dict) -> Dict[str, Any]:
        """Analisa especificamente payloads de projetos"""
        
        analysis = {
            'payload_size': self.calculate_payload_size(projeto_data),
            'content_breakdown': {},
            'warnings': [],
            'recommendations': []
        }
        
        # Analisar estrutura do payload
        if isinstance(projeto_data, dict):
            for key, value in projeto_data.items():
                if isinstance(value, (list, dict)):
                    analysis['content_breakdown'][key] = {
                        'type': type(value).__name__,
                        'size': self.calculate_payload_size(value),
                        'item_count': len(value) if isinstance(value, (list, dict)) else None
                    }
        
        # Detectar payloads grandes
        total_tokens = analysis['payload_size']['estimated_tokens']
        
        if total_tokens > 100000:  # ~100k tokens (limite GPT-4o é 128k)
            analysis['warnings'].append(f"CRÍTICO: Payload muito grande ({total_tokens:,} tokens estimados). Próximo do limite da OpenAI.")
            analysis['recommendations'].append("Considere dividir o processamento em lotes menores")
        elif total_tokens > 50000:  # ~50k tokens
            analysis['warnings'].append(f"ATENÇÃO: Payload grande ({total_tokens:,} tokens estimados). Pode causar lentidão.")
            analysis['recommendations'].append("Monitor o tempo de resposta. Considere otimização se necessário.")
        elif total_tokens > 20000:  # ~20k tokens
            analysis['warnings'].append(f"INFO: Payload moderado ({total_tokens:,} tokens estimados). Dentro dos limites normais.")
        
        # Verificar se há muitas perguntas/respostas
        if 'dominios' in projeto_data:
            total_perguntas = 0
            for dominio in projeto_data.get('dominios', []):
                total_perguntas += len(dominio.get('perguntas', []))
            
            if total_perguntas > 150:
                analysis['warnings'].append(f"Assessment com {total_perguntas} perguntas pode gerar payload extenso")
                analysis['recommendations'].append("Para assessments com +200 perguntas, considere processamento por domínios")
        
        return analysis
    
    def log_request(self, operation: str, payload_analysis: Dict, response_time: float, 
                   success: bool, error: Optional[str] = None):
        """Registra métricas de uma requisição"""
        
        request_log = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'payload_tokens': payload_analysis['payload_size']['estimated_tokens'],
            'payload_bytes': payload_analysis['payload_size']['bytes'],
            'response_time_seconds': response_time,
            'success': success,
            'error': error,
            'warnings': payload_analysis.get('warnings', [])
        }
        
        # Atualizar métricas globais
        self.metrics['total_requests'] += 1
        self.metrics['total_tokens_input'] += payload_analysis['payload_size']['estimated_tokens']
        
        # Calcular média de tempo de resposta
        if self.metrics['avg_response_time'] == 0:
            self.metrics['avg_response_time'] = response_time
        else:
            self.metrics['avg_response_time'] = (
                (self.metrics['avg_response_time'] * (self.metrics['total_requests'] - 1) + response_time) 
                / self.metrics['total_requests']
            )
        
        # Contar warnings de payload grande
        if any('CRÍTICO' in w or 'ATENÇÃO' in w for w in payload_analysis.get('warnings', [])):
            self.metrics['large_payload_warnings'] += 1
        
        # Manter histórico dos últimos 10 requests
        self.metrics['request_history'].append(request_log)
        if len(self.metrics['request_history']) > 10:
            self.metrics['request_history'].pop(0)
        
        # Log detalhado
        level = logging.WARNING if not success or payload_analysis.get('warnings') else logging.INFO
        logging.log(level, 
                   f"OpenAI {operation}: "
                   f"{payload_analysis['payload_size']['estimated_tokens']:,} tokens, "
                   f"{response_time:.2f}s, "
                   f"Success: {success}"
                   f"{f', Error: {error}' if error else ''}")
        
        # Log warnings separadamente
        for warning in payload_analysis.get('warnings', []):
            if 'CRÍTICO' in warning:
                logging.error(f"OpenAI Payload: {warning}")
            elif 'ATENÇÃO' in warning:
                logging.warning(f"OpenAI Payload: {warning}")
            else:
                logging.info(f"OpenAI Payload: {warning}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Retorna resumo das métricas coletadas"""
        return {
            'total_requests': self.metrics['total_requests'],
            'total_tokens_input': self.metrics['total_tokens_input'],
            'avg_response_time': round(self.metrics['avg_response_time'], 2),
            'large_payload_warnings': self.metrics['large_payload_warnings'],
            'recent_requests': self.metrics['request_history'][-5:],  # Últimos 5
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> list:
        """Gera recomendações baseadas nas métricas"""
        recommendations = []
        
        if self.metrics['large_payload_warnings'] > 2:
            recommendations.append("Considere implementar processamento em lotes para payloads grandes")
        
        if self.metrics['avg_response_time'] > 30:
            recommendations.append("Tempo de resposta médio alto. Verifique conexão ou reduza tamanho dos payloads")
        
        if self.metrics['total_tokens_input'] > 500000:
            recommendations.append("Alto uso de tokens. Monitor os custos da API OpenAI")
        
        return recommendations

# Instância global do monitor
payload_monitor = OpenAIPayloadMonitor()

def monitor_openai_request(operation: str):
    """Decorator para monitorar requisições OpenAI"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Tentar extrair dados do payload do primeiro argumento
            payload_data = args[1] if len(args) > 1 else kwargs.get('dados', {})
            
            # Analisar payload
            analysis = payload_monitor.analyze_project_payload(payload_data)
            
            # Log pré-processamento para payloads críticos
            for warning in analysis.get('warnings', []):
                if 'CRÍTICO' in warning:
                    logging.error(f"ANTES DO PROCESSAMENTO: {warning}")
            
            try:
                # Executar função original
                result = func(*args, **kwargs)
                
                # Calcular tempo de resposta
                response_time = time.time() - start_time
                
                # Registrar sucesso
                payload_monitor.log_request(
                    operation=operation,
                    payload_analysis=analysis,
                    response_time=response_time,
                    success=True
                )
                
                return result
                
            except Exception as e:
                # Calcular tempo até erro
                response_time = time.time() - start_time
                
                # Registrar erro
                payload_monitor.log_request(
                    operation=operation,
                    payload_analysis=analysis,
                    response_time=response_time,
                    success=False,
                    error=str(e)
                )
                
                # Re-raise o erro
                raise e
        
        return wrapper
    return decorator