"""
Processador em lote para análises IA
Permite processamento incremental com salvamento de progresso
"""

import json
import logging
from datetime import datetime
# from utils.openai_utils import OpenAIAssistant, coletar_dados_dominio_para_ia  # Temporariamente desabilitado
from app import db

def processar_dominio_individual(projeto, dominio, assistant, tipo_nome):
    """Processa um domínio individual e retorna resultado"""
    try:
        logging.info(f"Processando domínio: {dominio.nome}")
        
        # Coletar dados do domínio
        dados_dominio = coletar_dados_dominio_para_ia(projeto, dominio)
        if not dados_dominio:
            logging.warning(f"Não foi possível coletar dados para domínio: {dominio.nome}")
            return None
        
        # Gerar análise
        analise = assistant.gerar_analise_dominio(dados_dominio)
        if not analise:
            logging.warning(f"Análise vazia para domínio: {dominio.nome}")
            return None
        
        return {
            'dominio_nome': dominio.nome,
            'tipo_nome': tipo_nome,
            'analise': analise,
            'estatisticas': dados_dominio['estatisticas'],
            'gerado_em': datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Erro ao processar domínio {dominio.nome}: {e}")
        return None

def gerar_analise_incremental(projeto):
    """Gera análise incremental dos domínios"""
    try:
        logging.info(f"Iniciando análise incremental para projeto {projeto.id}")
        
        # Verificar se projeto está finalizado
        if not projeto.is_totalmente_finalizado():
            return {
                'erro': 'O projeto deve estar totalmente finalizado para gerar a análise dos domínios.'
            }
        
        # Função temporariamente desabilitada
        return {
            'erro': 'Função de análise incremental temporariamente desabilitada durante refatoração.'
        }
        
        # Estrutura para armazenar resultados
        dominios_analises = {}
        total_dominios = 0
        dominios_processados = 0
        
        # Coletar lista de domínios
        dominios_para_processar = []
        
        for projeto_assessment in projeto.assessments:
            if not projeto_assessment.finalizado:
                continue
                
            # Identificar domínios do assessment
            dominios_query = None
            if projeto_assessment.versao_assessment_id:
                # Sistema novo
                from models.assessment_version import AssessmentDominio
                dominios_query = AssessmentDominio.query.filter_by(
                    versao_id=projeto_assessment.versao_assessment.id,
                    ativo=True
                ).order_by(AssessmentDominio.ordem)
            elif projeto_assessment.tipo_assessment_id:
                # Sistema antigo
                from models.dominio import Dominio
                dominios_query = Dominio.query.filter_by(
                    tipo_assessment_id=projeto_assessment.tipo_assessment_id,
                    ativo=True
                ).order_by(Dominio.ordem)
            
            if not dominios_query:
                continue
                
            tipo_nome = (projeto_assessment.versao_assessment.tipo.nome 
                        if projeto_assessment.versao_assessment_id 
                        else projeto_assessment.tipo_assessment.nome)
            
            # Adicionar domínios à lista
            for dominio in dominios_query:
                dominios_para_processar.append((dominio, tipo_nome))
                total_dominios += 1
        
        if not dominios_para_processar:
            return {'erro': 'Nenhum domínio encontrado para análise.'}
        
        logging.info(f"Encontrados {total_dominios} domínios para processar")
        
        # Processar domínios um por um
        for dominio, tipo_nome in dominios_para_processar:
            resultado_dominio = processar_dominio_individual(projeto, dominio, assistant, tipo_nome)
            
            if resultado_dominio:
                # Organizar por tipo
                if tipo_nome not in dominios_analises:
                    dominios_analises[tipo_nome] = {}
                
                dominios_analises[tipo_nome][resultado_dominio['dominio_nome']] = {
                    'analise': resultado_dominio['analise'],
                    'estatisticas': resultado_dominio['estatisticas'],
                    'gerado_em': resultado_dominio['gerado_em']
                }
                
                dominios_processados += 1
                logging.info(f"Progresso: {dominios_processados}/{total_dominios}")
                
                # Salvamento incremental a cada domínio processado
                try:
                    projeto.analise_dominios_ia = json.dumps(dominios_analises, ensure_ascii=False)
                    db.session.commit()
                    logging.info(f"Progresso salvo: {dominios_processados} domínios")
                except Exception as e:
                    logging.error(f"Erro ao salvar progresso: {e}")
        
        return {
            'analises': dominios_analises,
            'assistant_name': assistant.assistant_name,
            'total_dominios': total_dominios,
            'dominios_processados': dominios_processados,
            'gerado_em': datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Erro crítico na análise incremental: {e}")
        return {
            'erro': f'Erro durante processamento: {str(e)}'
        }