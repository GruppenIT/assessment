from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.assessment_version import AssessmentTipo
from models.dominio import Dominio
from models.pergunta import Pergunta
from models.assessment_publico import AssessmentPublico, RespostaPublica
from forms.publico_forms import RespostaPublicaForm, DadosRespondentePubForm
from app import db
from datetime import datetime
import logging

publico_bp = Blueprint('publico', __name__, url_prefix='/public')

@publico_bp.route('/<int:assessment_id>')
def iniciar_assessment(assessment_id):
    """Página inicial do assessment público"""
    tipo_assessment = AssessmentTipo.query.get_or_404(assessment_id)
    
    # Verificar se o assessment tem URL pública habilitada
    if not tipo_assessment.url_publica:
        flash('Este assessment não está disponível publicamente.', 'warning')
        return redirect(url_for('auth.login'))
    
    # Obter versão publicada do assessment
    versao_publicada = tipo_assessment.get_versao_ativa()
    
    if not versao_publicada:
        flash('Este assessment não possui versão publicada.', 'warning')
        return redirect(url_for('auth.login'))
    
    # Obter domínios ativos da versão publicada
    from models.assessment_version import AssessmentDominio
    dominios = AssessmentDominio.query.filter_by(
        versao_id=versao_publicada.id,
        ativo=True
    ).order_by(AssessmentDominio.ordem).all()
    
    # Filtrar apenas domínios que têm perguntas light
    dominios_com_light = []
    for dominio in dominios:
        perguntas_light = [p for p in dominio.perguntas if p.ativo and p.light]
        if perguntas_light:
            dominios_com_light.append(dominio)
    
    if not dominios_com_light:
        flash('Este assessment não possui perguntas disponíveis.', 'warning')
        return redirect(url_for('auth.login'))
    
    # Criar sessão para o assessment público
    session_key = f'assessment_publico_{assessment_id}'
    
    # Inicializar ou obter dados da sessão
    if session_key not in session:
        # Criar novo assessment público no banco
        assessment_publico = AssessmentPublico(
            tipo_assessment_id=assessment_id,
            token=AssessmentPublico.gerar_token(),
            ip_address=request.remote_addr
        )
        db.session.add(assessment_publico)
        db.session.commit()
        
        session[session_key] = {
            'assessment_publico_id': assessment_publico.id,
            'dominio_atual': 0,
            'dominios_ids': [d.id for d in dominios_com_light]
        }
    
    # Redirecionar para o primeiro domínio
    return redirect(url_for('publico.responder_dominio', 
                          assessment_id=assessment_id, 
                          dominio_index=0))

@publico_bp.route('/<int:assessment_id>/dominio/<int:dominio_index>', methods=['GET', 'POST'])
def responder_dominio(assessment_id, dominio_index):
    """Responder perguntas de um domínio específico"""
    tipo_assessment = AssessmentTipo.query.get_or_404(assessment_id)
    
    if not tipo_assessment.url_publica:
        flash('Este assessment não está disponível publicamente.', 'warning')
        return redirect(url_for('auth.login'))
    
    session_key = f'assessment_publico_{assessment_id}'
    
    if session_key not in session:
        return redirect(url_for('publico.iniciar_assessment', assessment_id=assessment_id))
    
    session_data = session[session_key]
    dominios_ids = session_data['dominios_ids']
    
    # Verificar se o índice é válido
    if dominio_index >= len(dominios_ids):
        # Se todas as perguntas foram respondidas, ir para dados do respondente
        return redirect(url_for('publico.dados_respondente', assessment_id=assessment_id))
    
    dominio_id = dominios_ids[dominio_index]
    from models.assessment_version import AssessmentDominio
    dominio = AssessmentDominio.query.get_or_404(dominio_id)
    
    # Obter perguntas light do domínio (usando dominio_versao_id)
    perguntas = Pergunta.query.filter_by(
        dominio_versao_id=dominio_id,
        ativo=True,
        light=True
    ).order_by(Pergunta.ordem).all()
    
    if not perguntas:
        # Se não há perguntas, pular para o próximo domínio
        return redirect(url_for('publico.responder_dominio', 
                              assessment_id=assessment_id, 
                              dominio_index=dominio_index + 1))
    
    form = RespostaPublicaForm()
    
    if form.validate_on_submit():
        # Salvar respostas
        assessment_publico_id = session_data['assessment_publico_id']
        
        for pergunta in perguntas:
            campo_nome = f'pergunta_{pergunta.id}'
            valor = request.form.get(campo_nome)
            
            if valor:
                # Converter resposta: Não=0, Parcial=3, Sim=5
                valor_int = int(valor)
                
                # Verificar se já existe resposta
                resposta_existente = RespostaPublica.query.filter_by(
                    assessment_publico_id=assessment_publico_id,
                    pergunta_id=pergunta.id
                ).first()
                
                if resposta_existente:
                    resposta_existente.valor = valor_int
                    resposta_existente.data_resposta = datetime.utcnow()
                else:
                    resposta = RespostaPublica(
                        assessment_publico_id=assessment_publico_id,
                        pergunta_id=pergunta.id,
                        valor=valor_int
                    )
                    db.session.add(resposta)
        
        db.session.commit()
        
        # Atualizar índice do domínio atual na sessão
        session[session_key]['dominio_atual'] = dominio_index + 1
        session.modified = True
        
        # Ir para o próximo domínio
        return redirect(url_for('publico.responder_dominio', 
                              assessment_id=assessment_id, 
                              dominio_index=dominio_index + 1))
    
    # Obter respostas existentes se houver
    assessment_publico_id = session_data['assessment_publico_id']
    respostas_existentes = {}
    
    for pergunta in perguntas:
        resposta = RespostaPublica.query.filter_by(
            assessment_publico_id=assessment_publico_id,
            pergunta_id=pergunta.id
        ).first()
        if resposta:
            respostas_existentes[pergunta.id] = resposta.valor
    
    # Calcular progresso
    total_dominios = len(dominios_ids)
    dominios_respondidos = dominio_index
    progresso_percentual = round((dominios_respondidos / total_dominios) * 100) if total_dominios > 0 else 0
    
    return render_template('publico/responder_dominio.html',
                         tipo_assessment=tipo_assessment,
                         dominio=dominio,
                         perguntas=perguntas,
                         form=form,
                         respostas_existentes=respostas_existentes,
                         dominio_index=dominio_index,
                         total_dominios=total_dominios,
                         progresso_percentual=progresso_percentual)

@publico_bp.route('/<int:assessment_id>/dados', methods=['GET', 'POST'])
def dados_respondente(assessment_id):
    """Capturar dados do respondente ao final do assessment"""
    tipo_assessment = AssessmentTipo.query.get_or_404(assessment_id)
    
    if not tipo_assessment.url_publica:
        flash('Este assessment não está disponível publicamente.', 'warning')
        return redirect(url_for('auth.login'))
    
    session_key = f'assessment_publico_{assessment_id}'
    
    if session_key not in session:
        return redirect(url_for('publico.iniciar_assessment', assessment_id=assessment_id))
    
    session_data = session[session_key]
    assessment_publico_id = session_data['assessment_publico_id']
    
    assessment_publico = AssessmentPublico.query.get_or_404(assessment_publico_id)
    
    form = DadosRespondentePubForm()
    
    if form.validate_on_submit():
        # Salvar dados do respondente
        assessment_publico.nome_respondente = form.nome_completo.data
        assessment_publico.email_respondente = form.email.data
        assessment_publico.telefone_respondente = form.telefone.data
        assessment_publico.cargo_respondente = form.cargo.data
        assessment_publico.empresa_respondente = form.empresa.data
        assessment_publico.data_conclusao = datetime.utcnow()
        
        db.session.commit()
        
        # Criar lead automaticamente a partir do assessment público
        from models.lead import Lead
        
        # Verificar se já existe lead para este assessment
        lead_existente = Lead.query.filter_by(assessment_publico_id=assessment_publico.id).first()
        
        if not lead_existente:
            try:
                lead = Lead.criar_de_assessment_publico(assessment_publico)
                db.session.add(lead)
                db.session.flush()  # Garante que o lead tenha um ID antes de adicionar histórico
                
                # Adicionar entrada no histórico
                lead.adicionar_historico(
                    acao='criado',
                    detalhes=f'Lead criado automaticamente a partir do assessment público #{assessment_publico.id}'
                )
                
                db.session.commit()
                logging.info(f"Lead criado automaticamente para assessment público {assessment_publico.id}")
            except Exception as e:
                logging.error(f"Erro ao criar lead automático: {e}")
                # Não falhar o processo se houver erro na criação do lead
                db.session.rollback()
        
        # Redirecionar para resultado
        return redirect(url_for('publico.resultado', 
                              assessment_id=assessment_id,
                              token=assessment_publico.token))
    
    return render_template('publico/dados_respondente.html',
                         tipo_assessment=tipo_assessment,
                         form=form)

@publico_bp.route('/<int:assessment_id>/resultado/<token>')
def resultado(assessment_id, token):
    """Exibir resultado do assessment com recomendações IA"""
    tipo_assessment = AssessmentTipo.query.get_or_404(assessment_id)
    
    assessment_publico = AssessmentPublico.query.filter_by(
        tipo_assessment_id=assessment_id,
        token=token
    ).first_or_404()
    
    # Calcular pontuação geral
    pontuacao_geral = assessment_publico.calcular_pontuacao_geral()
    
    # Obter domínios respondidos com pontuações
    dominios_dados = []
    for dominio in assessment_publico.get_dominios_respondidos():
        pontuacao_dominio = assessment_publico.calcular_pontuacao_dominio(dominio.id)
        
        dominios_dados.append({
            'dominio': dominio,
            'pontuacao': pontuacao_dominio,
            'recomendacao': None  # Será preenchido pela IA
        })
    
    # Gerar recomendações com OpenAI
    from utils.publico_utils import gerar_recomendacoes_ia
    
    try:
        logging.info(f"Gerando recomendações IA para assessment público {assessment_publico.id}")
        recomendacoes = gerar_recomendacoes_ia(assessment_publico, dominios_dados)
        
        # Atualizar recomendações nos dados dos domínios
        for i, dominio_data in enumerate(dominios_dados):
            if i < len(recomendacoes):
                dominio_data['recomendacao'] = recomendacoes[i]
                logging.info(f"Recomendação atribuída ao domínio {dominio_data['dominio'].nome}")
    except Exception as e:
        logging.error(f"Erro ao gerar recomendações IA: {e}", exc_info=True)
        # Se falhar, adicionar recomendações padrão
        for dominio_data in dominios_dados:
            pontuacao = dominio_data['pontuacao']
            dominio_nome = dominio_data['dominio'].nome
            dominio_data['recomendacao'] = (
                f"Com base na pontuação de {pontuacao:.0f}%, recomenda-se revisar e fortalecer "
                f"as práticas relacionadas a {dominio_nome}, priorizando a implementação "
                f"de processos formais e a melhoria contínua dos controles existentes."
            )
    
    # Limpar sessão
    session_key = f'assessment_publico_{assessment_id}'
    session.pop(session_key, None)
    
    return render_template('publico/resultado.html',
                         tipo_assessment=tipo_assessment,
                         assessment_publico=assessment_publico,
                         pontuacao_geral=pontuacao_geral,
                         dominios_dados=dominios_dados)
