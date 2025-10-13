from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.lead import Lead, LeadHistorico
from models.usuario import Usuario
from forms.lead_forms import LeadUpdateForm, LeadComentarioForm, LeadFiltroForm
from app import db
from utils.auth_utils import admin_required
from sqlalchemy import or_, desc
from datetime import datetime
import logging

leads_bp = Blueprint('leads', __name__, url_prefix='/admin/leads')

@leads_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Dashboard de leads com filtros e estatísticas"""
    form = LeadFiltroForm(request.args, meta={'csrf': False})
    
    # Query base
    query = Lead.query
    
    # Aplicar filtros
    if form.status.data:
        query = query.filter(Lead.status == form.status.data)
    
    if form.prioridade.data:
        query = query.filter(Lead.prioridade == form.prioridade.data)
    
    if form.busca.data:
        busca_term = f"%{form.busca.data}%"
        query = query.filter(
            or_(
                Lead.nome.ilike(busca_term),
                Lead.email.ilike(busca_term),
                Lead.empresa.ilike(busca_term)
            )
        )
    
    # Ordenar por data de criação (mais recentes primeiro)
    leads = query.order_by(desc(Lead.data_criacao)).all()
    
    # Calcular estatísticas
    total_leads = Lead.query.count()
    leads_novos = Lead.query.filter_by(status='novo').count()
    leads_qualificados = Lead.query.filter_by(status='qualificado').count()
    leads_ganhos = Lead.query.filter_by(status='ganho').count()
    
    # Estatísticas de pontuação
    leads_baixa = Lead.query.filter(Lead.pontuacao_geral < 40).count()
    leads_media = Lead.query.filter(Lead.pontuacao_geral >= 40, Lead.pontuacao_geral < 70).count()
    leads_alta = Lead.query.filter(Lead.pontuacao_geral >= 70).count()
    
    # Distribuição por status
    status_distribuicao = db.session.query(
        Lead.status, 
        db.func.count(Lead.id)
    ).group_by(Lead.status).all()
    
    status_dict = {status: count for status, count in status_distribuicao}
    
    return render_template('admin/leads/dashboard.html',
                         leads=leads,
                         form=form,
                         total_leads=total_leads,
                         leads_novos=leads_novos,
                         leads_qualificados=leads_qualificados,
                         leads_ganhos=leads_ganhos,
                         leads_baixa=leads_baixa,
                         leads_media=leads_media,
                         leads_alta=leads_alta,
                         status_dict=status_dict)


@leads_bp.route('/<int:lead_id>')
@login_required
@admin_required
def detalhes(lead_id):
    """Página de detalhes do lead com gestão de status e comentários"""
    lead = Lead.query.get_or_404(lead_id)
    
    # Formulários
    update_form = LeadUpdateForm(obj=lead)
    comentario_form = LeadComentarioForm()
    
    # Popular select de atribuição
    usuarios = Usuario.query.filter_by(tipo='admin').all()
    update_form.atribuido_a_id.choices = [(0, 'Não atribuído')] + [(u.id, u.nome) for u in usuarios]
    
    if lead.atribuido_a_id:
        update_form.atribuido_a_id.data = lead.atribuido_a_id
    else:
        update_form.atribuido_a_id.data = 0
    
    # Buscar histórico do lead
    historico = LeadHistorico.query.filter_by(lead_id=lead_id).order_by(desc(LeadHistorico.data_registro)).all()
    
    # Obter dados do assessment público
    assessment_publico = lead.assessment_publico
    
    return render_template('admin/leads/detalhes.html',
                         lead=lead,
                         update_form=update_form,
                         comentario_form=comentario_form,
                         historico=historico,
                         assessment_publico=assessment_publico)


@leads_bp.route('/<int:lead_id>/atualizar', methods=['POST'])
@login_required
@admin_required
def atualizar(lead_id):
    """Atualizar dados do lead (status, prioridade, atribuição, comentários)"""
    lead = Lead.query.get_or_404(lead_id)
    form = LeadUpdateForm()
    
    # Popular select de atribuição para validação
    usuarios = Usuario.query.filter_by(tipo='admin').all()
    form.atribuido_a_id.choices = [(0, 'Não atribuído')] + [(u.id, u.nome) for u in usuarios]
    
    if form.validate_on_submit():
        # Registrar mudanças no histórico
        mudancas = []
        
        # Status
        if lead.status != form.status.data:
            mudancas.append(f"Status alterado de '{lead.status}' para '{form.status.data}'")
            lead.status = form.status.data
        
        # Prioridade
        if lead.prioridade != form.prioridade.data:
            mudancas.append(f"Prioridade alterada de '{lead.prioridade}' para '{form.prioridade.data}'")
            lead.prioridade = form.prioridade.data
        
        # Atribuição
        nova_atribuicao_id = form.atribuido_a_id.data if form.atribuido_a_id.data != 0 else None
        if lead.atribuido_a_id != nova_atribuicao_id:
            if nova_atribuicao_id:
                usuario = Usuario.query.get(nova_atribuicao_id)
                mudancas.append(f"Lead atribuído a {usuario.nome}")
            else:
                mudancas.append("Lead desatribuído")
            lead.atribuido_a_id = nova_atribuicao_id
        
        # Comentários
        if form.comentarios.data and form.comentarios.data.strip() != lead.comentarios:
            lead.comentarios = form.comentarios.data
            mudancas.append("Comentários atualizados")
        
        # Atualizar timestamp
        lead.data_atualizacao = datetime.utcnow()
        
        # Registrar no histórico se houve mudanças
        if mudancas:
            for mudanca in mudancas:
                lead.adicionar_historico(
                    acao='atualizacao',
                    usuario_id=current_user.id,
                    detalhes=mudanca
                )
        
        db.session.commit()
        flash('Lead atualizado com sucesso!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Erro no campo {field}: {error}', 'danger')
    
    return redirect(url_for('leads.detalhes', lead_id=lead_id))


@leads_bp.route('/<int:lead_id>/comentario', methods=['POST'])
@login_required
@admin_required
def adicionar_comentario(lead_id):
    """Adicionar comentário ao histórico do lead"""
    lead = Lead.query.get_or_404(lead_id)
    form = LeadComentarioForm()
    
    if form.validate_on_submit():
        # Adicionar ao histórico
        lead.adicionar_historico(
            acao='comentario',
            usuario_id=current_user.id,
            detalhes=form.comentario.data
        )
        
        lead.data_atualizacao = datetime.utcnow()
        db.session.commit()
        
        flash('Comentário adicionado com sucesso!', 'success')
    else:
        flash('Erro ao adicionar comentário. Verifique os dados.', 'danger')
    
    return redirect(url_for('leads.detalhes', lead_id=lead_id))


@leads_bp.route('/<int:lead_id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir(lead_id):
    """Excluir lead e o assessment público associado (apenas admin)"""
    lead = Lead.query.get_or_404(lead_id)
    nome_lead = lead.nome
    
    try:
        # Buscar assessment público associado
        assessment_publico = lead.assessment_publico
        
        # Excluir assessment público primeiro (se existir)
        if assessment_publico:
            logging.info(f'Excluindo assessment público #{assessment_publico.id} associado ao lead #{lead_id}')
            db.session.delete(assessment_publico)
        
        # Excluir lead (o histórico será excluído automaticamente por cascade)
        db.session.delete(lead)
        db.session.commit()
        
        flash(f'Lead "{nome_lead}" e assessment público associado excluídos com sucesso!', 'success')
        logging.info(f'Lead #{lead_id} e assessment público excluídos por {current_user.nome}')
    except Exception as e:
        db.session.rollback()
        logging.error(f'Erro ao excluir lead {lead_id}: {e}')
        flash('Erro ao excluir lead. Tente novamente.', 'danger')
    
    return redirect(url_for('leads.dashboard'))


@leads_bp.route('/estatisticas')
@login_required
@admin_required
def estatisticas():
    """API endpoint para estatísticas de leads (para gráficos)"""
    
    # Distribuição por status
    status_data = db.session.query(
        Lead.status,
        db.func.count(Lead.id)
    ).group_by(Lead.status).all()
    
    # Distribuição por pontuação
    pontuacao_data = {
        'baixa': Lead.query.filter(Lead.pontuacao_geral < 40).count(),
        'media': Lead.query.filter(Lead.pontuacao_geral >= 40, Lead.pontuacao_geral < 70).count(),
        'alta': Lead.query.filter(Lead.pontuacao_geral >= 70).count()
    }
    
    # Leads por mês (últimos 6 meses)
    from datetime import datetime, timedelta
    seis_meses_atras = datetime.utcnow() - timedelta(days=180)
    
    leads_por_mes = db.session.query(
        db.func.date_trunc('month', Lead.data_criacao).label('mes'),
        db.func.count(Lead.id)
    ).filter(Lead.data_criacao >= seis_meses_atras).group_by('mes').all()
    
    return jsonify({
        'status': dict(status_data),
        'pontuacao': pontuacao_data,
        'por_mes': [{'mes': str(mes), 'count': count} for mes, count in leads_por_mes]
    })
