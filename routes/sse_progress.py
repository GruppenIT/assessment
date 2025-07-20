"""
Sistema de Server-Sent Events para acompanhamento de progresso em tempo real
"""

import logging
import json
import threading
import time
from flask import Blueprint, Response, request
from flask_login import login_required
from utils.auth_utils import admin_required
from models.projeto import Projeto
from utils.ia_batch_processor import processar_dominio_individual
from utils.openai_utils import OpenAIAssistant
from app import db

sse_bp = Blueprint('sse', __name__)

# Armazenamento global de progresso por sessão
progress_storage = {}

@sse_bp.route('/progress/<session_id>')
@login_required
@admin_required
def progress_stream(session_id):
    """Stream de progresso em tempo real usando Server-Sent Events"""
    
    def generate():
        while True:
            if session_id in progress_storage:
                data = progress_storage[session_id]
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                
                # Se terminou, limpar o storage
                if data.get('status') in ['completed', 'error']:
                    time.sleep(1)
                    if session_id in progress_storage:
                        del progress_storage[session_id]
                    break
            else:
                yield f"data: {json.dumps({'status': 'waiting'}, ensure_ascii=False)}\n\n"
            
            time.sleep(0.5)  # Atualizar a cada 500ms
    
    return Response(
        generate(), 
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        }
    )

def processar_analise_em_background(projeto_id, session_id):
    """Processa análise de domínios em background com atualização de progresso"""
    try:
        logging.info(f"Iniciando processamento em background para projeto {projeto_id}")
        
        # Buscar projeto
        projeto = Projeto.query.get(projeto_id)
        if not projeto:
            progress_storage[session_id] = {
                'status': 'error',
                'message': 'Projeto não encontrado'
            }
            return
        
        # Verificar se projeto está finalizado
        if not projeto.is_totalmente_finalizado():
            progress_storage[session_id] = {
                'status': 'error',
                'message': 'Projeto deve estar totalmente finalizado'
            }
            return
        
        # Inicializar assistente
        assistant = OpenAIAssistant()
        if not assistant.is_configured():
            progress_storage[session_id] = {
                'status': 'error',
                'message': 'Integração com ChatGPT não configurada'
            }
            return
        
        # Coletar domínios para processar
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
        
        if not dominios_para_processar:
            progress_storage[session_id] = {
                'status': 'error',
                'message': 'Nenhum domínio encontrado para análise'
            }
            return
        
        total_dominios = len(dominios_para_processar)
        dominios_analises = {}
        dominios_processados = 0
        
        # Inicializar progresso
        progress_storage[session_id] = {
            'status': 'processing',
            'current_domain': 'Iniciando processamento...',
            'processed': 0,
            'total': total_dominios,
            'percentage': 0
        }
        
        # Processar domínios um por um
        for i, (dominio, tipo_nome) in enumerate(dominios_para_processar):
            # Atualizar progresso
            progress_storage[session_id] = {
                'status': 'processing',
                'current_domain': f'Processando: {dominio.nome}',
                'processed': i,
                'total': total_dominios,
                'percentage': int((i / total_dominios) * 100)
            }
            
            # Processar domínio individual
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
                
                # Salvamento incremental
                try:
                    projeto.analise_dominios_ia = json.dumps(dominios_analises, ensure_ascii=False)
                    db.session.commit()
                    logging.info(f"Progresso salvo: {dominios_processados} domínios")
                except Exception as e:
                    logging.error(f"Erro ao salvar progresso: {e}")
        
        # Finalizar processamento
        progress_storage[session_id] = {
            'status': 'completed',
            'current_domain': 'Processamento concluído!',
            'processed': dominios_processados,
            'total': total_dominios,
            'percentage': 100,
            'success_message': f'Análise de {dominios_processados} domínios gerada com sucesso!'
        }
        
        logging.info(f"Processamento concluído: {dominios_processados}/{total_dominios} domínios")
        
    except Exception as e:
        logging.error(f"Erro crítico no processamento em background: {e}")
        progress_storage[session_id] = {
            'status': 'error',
            'message': f'Erro durante processamento: {str(e)}'
        }

@sse_bp.route('/start_analysis/<int:projeto_id>')
@login_required
@admin_required
def start_analysis(projeto_id):
    """Inicia processamento de análise em background"""
    import uuid
    
    session_id = str(uuid.uuid4())
    
    # Iniciar thread de processamento
    thread = threading.Thread(
        target=processar_analise_em_background,
        args=(projeto_id, session_id)
    )
    thread.daemon = True
    thread.start()
    
    return json.dumps({
        'session_id': session_id,
        'status': 'started'
    })