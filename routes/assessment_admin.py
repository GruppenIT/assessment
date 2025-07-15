from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from models.assessment_version import AssessmentTipo, AssessmentVersao, AssessmentDominio
from models.pergunta import Pergunta
from models.usuario import Usuario
from utils.auth_utils import admin_required
from datetime import datetime

assessment_admin_bp = Blueprint('assessment_admin', __name__)

@assessment_admin_bp.route('/tipos-assessment')
@login_required
@admin_required
def listar_tipos():
    """Lista todos os tipos de assessment"""
    tipos = AssessmentTipo.query.filter_by(ativo=True).all()
    return render_template('admin/assessments/tipos.html', tipos=tipos)

@assessment_admin_bp.route('/tipos-assessment/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def novo_tipo():
    """Cria novo tipo de assessment"""
    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        
        if not nome:
            flash('Nome é obrigatório', 'error')
            return render_template('admin/assessments/tipo_form.html')
        
        # Criar tipo
        tipo = AssessmentTipo(
            nome=nome,
            descricao=descricao
        )
        db.session.add(tipo)
        db.session.flush()  # Para ter o ID
        
        # Criar primeira versão
        versao = AssessmentVersao(
            tipo_id=tipo.id,
            versao='1.0',
            status='draft',
            criado_por=current_user.id,
            notas_versao='Versão inicial'
        )
        db.session.add(versao)
        db.session.commit()
        
        flash(f'Tipo "{nome}" criado com sucesso!', 'success')
        return redirect(url_for('assessment_admin.editar_versao', versao_id=versao.id))
    
    return render_template('admin/assessments/tipo_form.html')

@assessment_admin_bp.route('/tipos-assessment/<int:tipo_id>')
@login_required
@admin_required
def ver_tipo(tipo_id):
    """Visualiza tipo de assessment e suas versões"""
    tipo = AssessmentTipo.query.get_or_404(tipo_id)
    versoes = tipo.get_versoes_ordenadas()
    return render_template('admin/assessments/tipo_detalhes.html', tipo=tipo, versoes=versoes)

@assessment_admin_bp.route('/tipos-assessment/versao/<int:versao_id>')
@login_required
@admin_required
def editar_versao(versao_id):
    """Edita uma versão de assessment"""
    versao = AssessmentVersao.query.get_or_404(versao_id)
    dominios = versao.get_dominios_ativos()
    return render_template('admin/assessments/versao_editor.html', versao=versao, dominios=dominios)

@assessment_admin_bp.route('/tipos-assessment/versao/<int:versao_id>/publicar', methods=['POST'])
@login_required
@admin_required
def publicar_versao(versao_id):
    """Publica uma versão de assessment"""
    versao = AssessmentVersao.query.get_or_404(versao_id)
    
    try:
        versao.publicar()
        flash(f'Versão {versao.versao} publicada com sucesso!', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    
    return redirect(url_for('assessment_admin.ver_tipo', tipo_id=versao.tipo_id))

@assessment_admin_bp.route('/assessments/versao/<int:versao_id>/nova-versao', methods=['POST'])
@login_required
@admin_required
def nova_versao(versao_id):
    """Cria nova versão baseada na atual"""
    versao_base = AssessmentVersao.query.get_or_404(versao_id)
    nova_versao_num = request.form.get('versao')
    notas = request.form.get('notas_versao', '')
    
    if not nova_versao_num:
        flash('Número da versão é obrigatório', 'error')
        return redirect(url_for('assessment_admin.ver_tipo', tipo_id=versao_base.tipo_id))
    
    # Verificar se versão já existe
    existe = AssessmentVersao.query.filter_by(
        tipo_id=versao_base.tipo_id,
        versao=nova_versao_num
    ).first()
    
    if existe:
        flash('Esta versão já existe', 'error')
        return redirect(url_for('assessment_admin.ver_tipo', tipo_id=versao_base.tipo_id))
    
    # Criar nova versão
    nova_versao = AssessmentVersao(
        tipo_id=versao_base.tipo_id,
        versao=nova_versao_num,
        status='draft',
        criado_por=current_user.id,
        notas_versao=notas
    )
    db.session.add(nova_versao)
    db.session.flush()
    
    # Copiar domínios e perguntas da versão base
    for dominio_base in versao_base.get_dominios_ativos():
        novo_dominio = AssessmentDominio(
            versao_id=nova_versao.id,
            nome=dominio_base.nome,
            descricao=dominio_base.descricao,
            ordem=dominio_base.ordem
        )
        db.session.add(novo_dominio)
        db.session.flush()
        
        # Copiar perguntas
        for pergunta_base in dominio_base.get_perguntas_ativas():
            nova_pergunta = Pergunta(
                dominio_versao_id=novo_dominio.id,
                texto=pergunta_base.texto,
                descricao=pergunta_base.descricao,
                ordem=pergunta_base.ordem
            )
            db.session.add(nova_pergunta)
    
    db.session.commit()
    flash(f'Nova versão {nova_versao_num} criada com sucesso!', 'success')
    return redirect(url_for('assessment_admin.editar_versao', versao_id=nova_versao.id))

@assessment_admin_bp.route('/assessments/dominio/<int:versao_id>/novo', methods=['POST'])
@login_required
@admin_required
def novo_dominio(versao_id):
    """Adiciona novo domínio à versão"""
    versao = AssessmentVersao.query.get_or_404(versao_id)
    
    if versao.status != 'draft':
        flash('Apenas versões em draft podem ser editadas', 'error')
        return redirect(url_for('assessment_admin.editar_versao', versao_id=versao_id))
    
    nome = request.form.get('nome')
    descricao = request.form.get('descricao', '')
    
    if not nome:
        flash('Nome do domínio é obrigatório', 'error')
        return redirect(url_for('assessment_admin.editar_versao', versao_id=versao_id))
    
    # Calcular próxima ordem
    ultima_ordem = db.session.query(db.func.max(AssessmentDominio.ordem)).filter_by(
        versao_id=versao_id
    ).scalar() or 0
    
    dominio = AssessmentDominio(
        versao_id=versao_id,
        nome=nome,
        descricao=descricao,
        ordem=ultima_ordem + 1
    )
    db.session.add(dominio)
    db.session.commit()
    
    flash(f'Domínio "{nome}" adicionado com sucesso!', 'success')
    return redirect(url_for('assessment_admin.editar_versao', versao_id=versao_id))

@assessment_admin_bp.route('/assessments/pergunta/<int:dominio_id>/nova', methods=['POST'])
@login_required
@admin_required
def nova_pergunta(dominio_id):
    """Adiciona nova pergunta ao domínio"""
    dominio = AssessmentDominio.query.get_or_404(dominio_id)
    
    if dominio.versao.status != 'draft':
        flash('Apenas versões em draft podem ser editadas', 'error')
        return redirect(url_for('assessment_admin.editar_versao', versao_id=dominio.versao_id))
    
    texto = request.form.get('texto')
    descricao = request.form.get('descricao', '')
    
    if not texto:
        flash('Texto da pergunta é obrigatório', 'error')
        return redirect(url_for('assessment_admin.editar_versao', versao_id=dominio.versao_id))
    
    # Calcular próxima ordem
    ultima_ordem = db.session.query(db.func.max(Pergunta.ordem)).filter_by(
        dominio_versao_id=dominio_id
    ).scalar() or 0
    
    pergunta = Pergunta(
        dominio_versao_id=dominio_id,
        texto=texto,
        descricao=descricao,
        ordem=ultima_ordem + 1
    )
    db.session.add(pergunta)
    db.session.commit()
    
    flash('Pergunta adicionada com sucesso!', 'success')
    return redirect(url_for('assessment_admin.editar_versao', versao_id=dominio.versao_id))

@assessment_admin_bp.route('/tipos-assessment/importar-csv')
@login_required
@admin_required
def importar_csv():
    """Página de importação CSV para assessments versionados"""
    tipos = AssessmentTipo.query.filter_by(ativo=True).all()
    return render_template('admin/assessments/importar_csv.html', tipos=tipos)

@assessment_admin_bp.route('/tipos-assessment/importar-csv', methods=['POST'])
@login_required
@admin_required
def processar_importacao_csv():
    """Processa importação CSV criando nova versão draft"""
    from werkzeug.utils import secure_filename
    import csv
    import io
    import os
    from decimal import Decimal
    
    tipo_id = request.form.get('tipo_assessment_id')
    nova_versao_num = request.form.get('nova_versao')
    arquivo = request.files.get('arquivo_csv')
    
    if not tipo_id or not nova_versao_num or not arquivo:
        flash('Todos os campos são obrigatórios', 'error')
        return redirect(url_for('assessment_admin.importar_csv'))
    
    tipo = AssessmentTipo.query.get_or_404(tipo_id)
    
    # Verificar se versão já existe
    versao_existe = AssessmentVersao.query.filter_by(
        tipo_id=tipo_id,
        versao=nova_versao_num
    ).first()
    
    if versao_existe:
        flash('Esta versão já existe para este tipo', 'error')
        return redirect(url_for('assessment_admin.importar_csv'))
    
    try:
        # Ler arquivo CSV
        stream = io.StringIO(arquivo.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.reader(stream)
        
        # Criar nova versão
        nova_versao = AssessmentVersao(
            tipo_id=tipo_id,
            versao=nova_versao_num,
            status='draft',
            criado_por=current_user.id,
            notas_versao=f'Versão importada via CSV em {datetime.now().strftime("%d/%m/%Y")}'
        )
        db.session.add(nova_versao)
        db.session.flush()
        
        dominios_criados = {}
        perguntas_criadas = 0
        
        # Processar cada linha do CSV
        next(csv_input)  # Pular cabeçalho
        for row in csv_input:
            if len(row) < 3:
                continue
                
            dominio_nome = row[0].strip()
            pergunta_texto = row[1].strip()
            pergunta_descricao = row[2].strip() if len(row) > 2 else ''
            
            if not dominio_nome or not pergunta_texto:
                continue
            
            # Criar domínio se não existir
            if dominio_nome not in dominios_criados:
                dominio = AssessmentDominio(
                    versao_id=nova_versao.id,
                    nome=dominio_nome,
                    ordem=len(dominios_criados) + 1
                )
                db.session.add(dominio)
                db.session.flush()
                dominios_criados[dominio_nome] = dominio
            
            # Criar pergunta
            dominio = dominios_criados[dominio_nome]
            ultima_ordem = db.session.query(db.func.max(Pergunta.ordem)).filter_by(
                dominio_versao_id=dominio.id
            ).scalar() or 0
            
            pergunta = Pergunta(
                dominio_versao_id=dominio.id,
                texto=pergunta_texto,
                descricao=pergunta_descricao,
                ordem=ultima_ordem + 1
            )
            db.session.add(pergunta)
            perguntas_criadas += 1
        
        db.session.commit()
        
        flash(f'Importação concluída! Criados {len(dominios_criados)} domínios e {perguntas_criadas} perguntas na versão {nova_versao_num}', 'success')
        return redirect(url_for('assessment_admin.editar_versao', versao_id=nova_versao.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro na importação: {str(e)}', 'error')
        return redirect(url_for('assessment_admin.importar_csv'))