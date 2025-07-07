from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from app import db
from models.usuario import Usuario
from models.dominio import Dominio
from models.pergunta import Pergunta
from models.resposta import Resposta
from models.logo import Logo
from forms.admin_forms import DominioForm, PerguntaForm, LogoForm
from utils.auth_utils import admin_required
from utils.upload_utils import allowed_file, save_uploaded_file

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Dashboard administrativo"""
    # Estatísticas gerais
    total_clientes = Usuario.query.filter_by(tipo='cliente', ativo=True).count()
    total_dominios = Dominio.query.filter_by(ativo=True).count()
    total_perguntas = Pergunta.query.filter_by(ativo=True).count()
    total_respostas = Resposta.query.count()
    
    # Clientes com assessment completo
    clientes_completos = []
    clientes = Usuario.query.filter_by(tipo='cliente', ativo=True).all()
    for cliente in clientes:
        if cliente.assessment_concluido():
            clientes_completos.append(cliente)
    
    # Últimas atividades
    ultimas_respostas = Resposta.query.join(Usuario).order_by(
        Resposta.data_resposta.desc()
    ).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_clientes=total_clientes,
                         total_dominios=total_dominios,
                         total_perguntas=total_perguntas,
                         total_respostas=total_respostas,
                         clientes_completos=clientes_completos,
                         ultimas_respostas=ultimas_respostas)

@admin_bp.route('/dominios')
@login_required
@admin_required
def dominios():
    """Gerenciamento de domínios"""
    dominios = Dominio.query.order_by(Dominio.ordem, Dominio.nome).all()
    form = DominioForm()
    return render_template('admin/dominios.html', dominios=dominios, form=form)

@admin_bp.route('/dominios/criar', methods=['POST'])
@login_required
@admin_required
def criar_dominio():
    """Cria um novo domínio"""
    form = DominioForm()
    
    if form.validate_on_submit():
        # Verificar se já existe domínio com este nome
        dominio_existente = Dominio.query.filter_by(nome=form.nome.data.strip()).first()
        if dominio_existente:
            flash('Já existe um domínio com este nome.', 'danger')
            return redirect(url_for('admin.dominios'))
        
        dominio = Dominio(
            nome=form.nome.data.strip(),
            descricao=form.descricao.data.strip() if form.descricao.data else None,
            ordem=form.ordem.data
        )
        
        try:
            db.session.add(dominio)
            db.session.commit()
            flash('Domínio criado com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Erro ao criar domínio.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
    
    return redirect(url_for('admin.dominios'))

@admin_bp.route('/dominios/<int:dominio_id>/editar', methods=['POST'])
@login_required
@admin_required
def editar_dominio(dominio_id):
    """Edita um domínio existente"""
    dominio = Dominio.query.get_or_404(dominio_id)
    
    nome = request.form.get('nome', '').strip()
    descricao = request.form.get('descricao', '').strip()
    ordem = request.form.get('ordem', type=int, default=1)
    
    if not nome:
        flash('Nome do domínio é obrigatório.', 'danger')
        return redirect(url_for('admin.dominios'))
    
    # Verificar se já existe outro domínio com este nome
    dominio_existente = Dominio.query.filter(
        Dominio.nome == nome,
        Dominio.id != dominio_id
    ).first()
    
    if dominio_existente:
        flash('Já existe outro domínio com este nome.', 'danger')
        return redirect(url_for('admin.dominios'))
    
    try:
        dominio.nome = nome
        dominio.descricao = descricao if descricao else None
        dominio.ordem = ordem
        db.session.commit()
        flash('Domínio atualizado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao atualizar domínio.', 'danger')
    
    return redirect(url_for('admin.dominios'))

@admin_bp.route('/dominios/<int:dominio_id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_dominio(dominio_id):
    """Exclui um domínio"""
    dominio = Dominio.query.get_or_404(dominio_id)
    
    try:
        db.session.delete(dominio)
        db.session.commit()
        flash('Domínio excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao excluir domínio. Verifique se não há perguntas associadas.', 'danger')
    
    return redirect(url_for('admin.dominios'))

@admin_bp.route('/perguntas')
@login_required
@admin_required
def perguntas():
    """Gerenciamento de perguntas"""
    dominio_id = request.args.get('dominio_id', type=int)
    
    query = Pergunta.query.join(Dominio)
    if dominio_id:
        query = query.filter(Pergunta.dominio_id == dominio_id)
    
    perguntas = query.order_by(Dominio.ordem, Pergunta.ordem, Pergunta.id).all()
    dominios = Dominio.query.filter_by(ativo=True).order_by(Dominio.ordem, Dominio.nome).all()
    form = PerguntaForm()
    form.dominio_id.choices = [(d.id, d.nome) for d in dominios]
    
    return render_template('admin/perguntas.html',
                         perguntas=perguntas,
                         dominios=dominios,
                         form=form,
                         dominio_selecionado=dominio_id)

@admin_bp.route('/perguntas/criar', methods=['POST'])
@login_required
@admin_required
def criar_pergunta():
    """Cria uma nova pergunta"""
    form = PerguntaForm()
    dominios = Dominio.query.filter_by(ativo=True).order_by(Dominio.ordem, Dominio.nome).all()
    form.dominio_id.choices = [(d.id, d.nome) for d in dominios]
    
    if form.validate_on_submit():
        pergunta = Pergunta(
            dominio_id=form.dominio_id.data,
            texto=form.texto.data.strip(),
            descricao=form.descricao.data.strip() if form.descricao.data else None,
            ordem=form.ordem.data
        )
        
        try:
            db.session.add(pergunta)
            db.session.commit()
            flash('Pergunta criada com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Erro ao criar pergunta.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
    
    return redirect(url_for('admin.perguntas'))

@admin_bp.route('/perguntas/<int:pergunta_id>/editar', methods=['POST'])
@login_required
@admin_required
def editar_pergunta(pergunta_id):
    """Edita uma pergunta existente"""
    pergunta = Pergunta.query.get_or_404(pergunta_id)
    
    dominio_id = request.form.get('dominio_id', type=int)
    texto = request.form.get('texto', '').strip()
    descricao = request.form.get('descricao', '').strip()
    ordem = request.form.get('ordem', type=int, default=1)
    
    if not dominio_id or not texto:
        flash('Domínio e texto da pergunta são obrigatórios.', 'danger')
        return redirect(url_for('admin.perguntas'))
    
    try:
        pergunta.dominio_id = dominio_id
        pergunta.texto = texto
        pergunta.descricao = descricao if descricao else None
        pergunta.ordem = ordem
        db.session.commit()
        flash('Pergunta atualizada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao atualizar pergunta.', 'danger')
    
    return redirect(url_for('admin.perguntas'))

@admin_bp.route('/perguntas/<int:pergunta_id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_pergunta(pergunta_id):
    """Exclui uma pergunta"""
    pergunta = Pergunta.query.get_or_404(pergunta_id)
    
    try:
        db.session.delete(pergunta)
        db.session.commit()
        flash('Pergunta excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao excluir pergunta.', 'danger')
    
    return redirect(url_for('admin.perguntas'))

@admin_bp.route('/assessments')
@login_required
@admin_required
def assessments():
    """Visualização de assessments dos clientes"""
    clientes = Usuario.query.filter_by(tipo='cliente', ativo=True).order_by(Usuario.nome).all()
    
    assessments_data = []
    for cliente in clientes:
        total_perguntas = Pergunta.query.filter_by(ativo=True).count()
        respostas_dadas = len(cliente.respostas)
        progresso = cliente.get_progresso_assessment()
        concluido = cliente.assessment_concluido()
        
        # Calcular média geral
        if cliente.respostas:
            media_geral = sum(r.nota for r in cliente.respostas) / len(cliente.respostas)
        else:
            media_geral = 0
        
        assessments_data.append({
            'cliente': cliente,
            'total_perguntas': total_perguntas,
            'respostas_dadas': respostas_dadas,
            'progresso': progresso,
            'concluido': concluido,
            'media_geral': round(media_geral, 2)
        })
    
    return render_template('admin/assessments.html', assessments_data=assessments_data)

@admin_bp.route('/configuracoes')
@login_required
@admin_required
def configuracoes():
    """Configurações do sistema"""
    logo_atual = Logo.get_logo_ativo()
    form = LogoForm()
    return render_template('admin/configuracoes.html', logo_atual=logo_atual, form=form)

@admin_bp.route('/configuracoes/logo', methods=['POST'])
@login_required
@admin_required
def upload_logo():
    """Upload do logo da empresa"""
    form = LogoForm()
    
    if form.validate_on_submit():
        file = form.logo.data
        
        if file and allowed_file(file.filename):
            try:
                # Salvar o arquivo
                filename = save_uploaded_file(file, 'logos')
                caminho_arquivo = f'static/uploads/logos/{filename}'
                
                # Desativar logo anterior
                Logo.query.update({'ativo': False})
                
                # Criar novo registro de logo
                logo = Logo(
                    caminho_arquivo=caminho_arquivo,
                    nome_original=file.filename,
                    tamanho=len(file.read()),
                    tipo_mime=file.content_type,
                    ativo=True
                )
                
                # Resetar o ponteiro do arquivo
                file.seek(0)
                
                db.session.add(logo)
                db.session.commit()
                
                flash('Logo atualizado com sucesso!', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Erro ao fazer upload do logo.', 'danger')
        else:
            flash('Arquivo inválido. Use apenas imagens PNG, JPG ou GIF.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
    
    return redirect(url_for('admin.configuracoes'))
