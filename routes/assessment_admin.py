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
        
        # Registrar criação na auditoria
        from models.auditoria import registrar_criacao
        registrar_criacao(
            entidade='assessment_tipo',
            entidade_id=tipo.id,
            entidade_nome=nome,
            detalhes={'versao_inicial': versao.versao}
        )
        
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
        
        # Registrar publicação na auditoria
        from models.auditoria import Auditoria
        Auditoria.registrar(
            acao='publish',
            entidade='assessment_versao',
            entidade_id=versao.id,
            entidade_nome=f'{versao.tipo.nome} v{versao.versao}',
            descricao=f'Publicou versão {versao.versao} do assessment "{versao.tipo.nome}"',
            detalhes={
                'tipo_id': versao.tipo_id,
                'versao': versao.versao,
                'total_dominios': versao.get_total_dominios(),
                'total_perguntas': versao.get_total_perguntas()
            }
        )
        
        flash(f'Versão {versao.versao} publicada com sucesso!', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    
    return redirect(url_for('assessment_admin.ver_tipo', tipo_id=versao.tipo_id))

@assessment_admin_bp.route('/tipos-assessment/versao/<int:versao_id>/nova-versao', methods=['POST'])
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
    
    # Nova versão é criada vazia (sem domínios e perguntas)
    # O usuário pode adicionar conteúdo manualmente ou via CSV
    
    db.session.commit()
    flash(f'Nova versão {nova_versao_num} criada com sucesso!', 'success')
    return redirect(url_for('assessment_admin.editar_versao', versao_id=nova_versao.id))

@assessment_admin_bp.route('/tipos-assessment/dominio/<int:versao_id>/novo', methods=['POST'])
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

@assessment_admin_bp.route('/tipos-assessment/pergunta/<int:dominio_id>/nova', methods=['POST'])
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
    referencia = request.form.get('referencia', '')
    recomendacao = request.form.get('recomendacao', '')
    light = request.form.get('light') == '1'
    
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
        descricao=descricao if descricao else None,
        referencia=referencia if referencia else None,
        recomendacao=recomendacao if recomendacao else None,
        light=light,
        ordem=ultima_ordem + 1
    )
    db.session.add(pergunta)
    db.session.commit()
    
    flash('Pergunta adicionada com sucesso!', 'success')
    return redirect(url_for('assessment_admin.editar_versao', versao_id=dominio.versao_id))

@assessment_admin_bp.route('/tipos-assessment/pergunta/<int:pergunta_id>/editar', methods=['POST'])
@login_required
@admin_required
def editar_pergunta(pergunta_id):
    """Edita uma pergunta existente"""
    pergunta = Pergunta.query.get_or_404(pergunta_id)
    dominio = pergunta.dominio_versao
    
    if dominio.versao.status != 'draft':
        flash('Apenas versões em draft podem ser editadas', 'error')
        return redirect(url_for('assessment_admin.editar_versao', versao_id=dominio.versao_id))
    
    texto = request.form.get('texto')
    descricao = request.form.get('descricao', '')
    referencia = request.form.get('referencia', '')
    recomendacao = request.form.get('recomendacao', '')
    light = request.form.get('light') == '1'
    ordem = request.form.get('ordem')
    
    if not texto:
        flash('Texto da pergunta é obrigatório', 'error')
        return redirect(url_for('assessment_admin.editar_versao', versao_id=dominio.versao_id))
    
    try:
        ordem_int = int(ordem) if ordem else pergunta.ordem
    except ValueError:
        ordem_int = pergunta.ordem
    
    # Atualizar pergunta
    pergunta.texto = texto
    pergunta.descricao = descricao if descricao else None
    pergunta.referencia = referencia if referencia else None
    pergunta.recomendacao = recomendacao if recomendacao else None
    pergunta.light = light
    pergunta.ordem = ordem_int
    
    db.session.commit()
    
    flash('Pergunta atualizada com sucesso!', 'success')
    return redirect(url_for('assessment_admin.editar_versao', versao_id=dominio.versao_id))

@assessment_admin_bp.route('/tipos-assessment/reordenar-perguntas', methods=['POST'])
@login_required
@admin_required
def reordenar_perguntas():
    """Reordena perguntas via drag and drop"""
    try:
        data = request.get_json()
        dominio_id = data.get('dominio_id')
        ordens = data.get('ordens', [])
        
        dominio = AssessmentDominio.query.get_or_404(dominio_id)
        
        # Verificar se versão está em draft
        if dominio.versao.status != 'draft':
            return {'success': False, 'message': 'Apenas versões em draft podem ser editadas'}
        
        # Atualizar ordem das perguntas
        for item in ordens:
            pergunta_id = item['id']
            nova_ordem = item['ordem']
            
            pergunta = Pergunta.query.filter_by(
                id=pergunta_id,
                dominio_versao_id=dominio_id
            ).first()
            
            if pergunta:
                pergunta.ordem = nova_ordem
        
        db.session.commit()
        
        return {'success': True, 'message': 'Ordem atualizada com sucesso'}
        
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Erro ao atualizar ordem: {str(e)}'}

@assessment_admin_bp.route('/tipos-assessment/<int:tipo_id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_tipo_assessment(tipo_id):
    """Edita nome e descrição de um tipo de assessment"""
    tipo = AssessmentTipo.query.get_or_404(tipo_id)
    
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        descricao = request.form.get('descricao', '').strip()
        
        if not nome:
            flash('Nome é obrigatório', 'error')
            return redirect(url_for('assessment_admin.editar_tipo_assessment', tipo_id=tipo_id))
        
        # Verificar se nome já existe (exceto o próprio tipo)
        nome_existente = AssessmentTipo.query.filter(
            AssessmentTipo.nome == nome,
            AssessmentTipo.id != tipo_id
        ).first()
        
        if nome_existente:
            flash('Já existe um tipo de assessment com este nome', 'error')
            return redirect(url_for('assessment_admin.editar_tipo_assessment', tipo_id=tipo_id))
        
        # Atualizar tipo
        tipo.nome = nome
        tipo.descricao = descricao if descricao else None
        
        db.session.commit()
        
        flash('Tipo de assessment atualizado com sucesso!', 'success')
        return redirect(url_for('assessment_admin.listar_tipos'))
    
    return render_template('admin/assessments/editar_tipo.html', tipo=tipo)

@assessment_admin_bp.route('/tipos-assessment/importar-csv')
@login_required
@admin_required
def importar_csv():
    """Página de importação CSV para assessments versionados"""
    tipos = AssessmentTipo.query.filter_by(ativo=True).all()
    return render_template('admin/assessments/importar_csv.html', tipos=tipos)

@assessment_admin_bp.route('/tipos-assessment/<int:tipo_id>/desativar', methods=['POST'])
@login_required
@admin_required
def desativar_tipo(tipo_id):
    """Desativa um tipo de assessment"""
    tipo = AssessmentTipo.query.get_or_404(tipo_id)
    
    # Verificar se há projetos usando este tipo
    from models.projeto import ProjetoAssessment
    projetos_ativo = ProjetoAssessment.query.filter_by(tipo_assessment_id=tipo_id).count()
    
    if projetos_ativo > 0:
        flash(f'Não é possível desativar o tipo "{tipo.nome}" pois há {projetos_ativo} projeto(s) ativo(s) usando-o.', 'error')
        return redirect(url_for('assessment_admin.ver_tipo', tipo_id=tipo_id))
    
    tipo.ativo = False
    db.session.commit()
    
    flash(f'Tipo "{tipo.nome}" desativado com sucesso!', 'success')
    return redirect(url_for('assessment_admin.listar_tipos'))

@assessment_admin_bp.route('/tipos-assessment/<int:tipo_id>/clonar', methods=['POST'])
@login_required
@admin_required
def clonar_tipo(tipo_id):
    """Clona um tipo de assessment criando um novo independente"""
    tipo_original = AssessmentTipo.query.get_or_404(tipo_id)
    novo_nome = request.form.get('nome')
    nova_descricao = request.form.get('descricao', '')
    
    if not novo_nome:
        flash('Nome é obrigatório para clonagem', 'error')
        return redirect(url_for('assessment_admin.ver_tipo', tipo_id=tipo_id))
    
    # Verificar se nome já existe
    existe = AssessmentTipo.query.filter_by(nome=novo_nome).first()
    if existe:
        flash('Já existe um tipo com este nome', 'error')
        return redirect(url_for('assessment_admin.ver_tipo', tipo_id=tipo_id))
    
    # Criar novo tipo
    novo_tipo = AssessmentTipo(
        nome=novo_nome,
        descricao=nova_descricao
    )
    db.session.add(novo_tipo)
    db.session.flush()
    
    # Pegar versão ativa do tipo original
    versao_original = tipo_original.get_versao_ativa()
    if not versao_original:
        flash('Tipo original não tem versão ativa para clonar', 'error')
        return redirect(url_for('assessment_admin.ver_tipo', tipo_id=tipo_id))
    
    # Criar versão 1.0 para o novo tipo
    nova_versao = AssessmentVersao(
        tipo_id=novo_tipo.id,
        versao='1.0',
        status='draft',
        criado_por=current_user.id,
        notas_versao=f'Clonado de {tipo_original.nome} v{versao_original.versao}'
    )
    db.session.add(nova_versao)
    db.session.flush()
    
    # Copiar domínios e perguntas
    for dominio_original in versao_original.get_dominios_ativos():
        novo_dominio = AssessmentDominio(
            versao_id=nova_versao.id,
            nome=dominio_original.nome,
            descricao=dominio_original.descricao,
            ordem=dominio_original.ordem
        )
        db.session.add(novo_dominio)
        db.session.flush()
        
        # Copiar perguntas
        for pergunta_original in dominio_original.get_perguntas_ativas():
            nova_pergunta = Pergunta(
                dominio_versao_id=novo_dominio.id,
                texto=pergunta_original.texto,
                descricao=pergunta_original.descricao,
                referencia=pergunta_original.referencia,
                recomendacao=pergunta_original.recomendacao,
                light=pergunta_original.light,
                ordem=pergunta_original.ordem
            )
            db.session.add(nova_pergunta)
    
    db.session.commit()
    flash(f'Tipo "{novo_nome}" clonado com sucesso!', 'success')
    return redirect(url_for('assessment_admin.editar_versao', versao_id=nova_versao.id))

@assessment_admin_bp.route('/tipos-assessment/versao/<int:versao_id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_versao(versao_id):
    """Exclui uma versão que ainda não foi publicada"""
    versao = AssessmentVersao.query.get_or_404(versao_id)
    
    # Verificar se a versão pode ser excluída
    if versao.status != 'draft':
        flash('Apenas versões em draft podem ser excluídas', 'error')
        return redirect(url_for('assessment_admin.ver_tipo', tipo_id=versao.tipo_id))
    
    # Verificar se há projetos usando esta versão
    from models.projeto import ProjetoAssessment
    projetos_usando = ProjetoAssessment.query.filter_by(versao_assessment_id=versao_id).count()
    
    if projetos_usando > 0:
        flash(f'Não é possível excluir esta versão pois há {projetos_usando} projeto(s) usando-a.', 'error')
        return redirect(url_for('assessment_admin.ver_tipo', tipo_id=versao.tipo_id))
    
    tipo_id = versao.tipo_id
    tipo_nome = versao.tipo.nome
    versao_num = versao.versao
    
    # Excluir perguntas primeiro (devido às foreign keys)
    for dominio in versao.get_dominios_ativos():
        Pergunta.query.filter_by(dominio_versao_id=dominio.id).delete()
    
    # Excluir domínios
    AssessmentDominio.query.filter_by(versao_id=versao_id).delete()
    
    # Excluir a versão
    db.session.delete(versao)
    db.session.commit()
    
    flash(f'Versão {versao_num} do tipo "{tipo_nome}" excluída com sucesso!', 'success')
    return redirect(url_for('assessment_admin.ver_tipo', tipo_id=tipo_id))

@assessment_admin_bp.route('/tipos-assessment/versao/<int:versao_id>/importar-csv', methods=['POST'])
@login_required
@admin_required
def importar_csv_versao(versao_id):
    """Importa CSV para uma versão específica"""
    versao = AssessmentVersao.query.get_or_404(versao_id)
    
    # Verificar se a versão pode receber importação
    if versao.status != 'draft':
        flash('Apenas versões em draft podem receber importação CSV', 'error')
        return redirect(url_for('assessment_admin.editar_versao', versao_id=versao_id))
    
    # Verificar se a versão está vazia
    if versao.get_total_perguntas() > 0:
        flash('A versão deve estar vazia para receber importação CSV', 'error')
        return redirect(url_for('assessment_admin.editar_versao', versao_id=versao_id))
    
    arquivo = request.files.get('arquivo_csv')
    if not arquivo or arquivo.filename == '':
        flash('Nenhum arquivo selecionado', 'error')
        return redirect(url_for('assessment_admin.editar_versao', versao_id=versao_id))
    
    if not arquivo.filename.lower().endswith('.csv'):
        flash('Arquivo deve ser um CSV', 'error')
        return redirect(url_for('assessment_admin.editar_versao', versao_id=versao_id))
    
    try:
        # Processar CSV
        import csv
        import io
        
        # Ler arquivo CSV com separador ponto e vírgula
        stream = io.StringIO(arquivo.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.DictReader(stream, delimiter=';')
        
        dominios_criados = {}
        perguntas_criadas = 0
        
        for row in csv_input:
            dominio_nome = row.get('Dominio', '').strip()
            dominio_descricao = row.get('DescriçãoDominio', '').strip()
            dominio_ordem = row.get('OrdemDominio', '').strip()
            pergunta_texto = row.get('Pergunta', '').strip()
            pergunta_descricao = row.get('DescriçãoPergunta', '').strip()
            pergunta_referencia = row.get('Referência', '').strip()
            pergunta_recomendacao = row.get('Recomendação', '').strip()
            pergunta_light = row.get('Light', '').strip().lower() in ['1', 'sim', 'true', 's']
            pergunta_ordem = row.get('OrdemPergunta', '').strip()
            
            if not dominio_nome or not pergunta_texto:
                continue
                
            # Criar ou encontrar domínio
            if dominio_nome not in dominios_criados:
                try:
                    ordem_dom = int(dominio_ordem) if dominio_ordem else len(dominios_criados) + 1
                except ValueError:
                    ordem_dom = len(dominios_criados) + 1
                    
                dominio = AssessmentDominio(
                    versao_id=versao_id,
                    nome=dominio_nome,
                    descricao=dominio_descricao,
                    ordem=ordem_dom
                )
                db.session.add(dominio)
                db.session.flush()
                dominios_criados[dominio_nome] = dominio
            else:
                dominio = dominios_criados[dominio_nome]
            
            # Criar pergunta
            try:
                ordem_perg = int(pergunta_ordem) if pergunta_ordem else len(dominio.get_perguntas_ativas()) + 1
            except ValueError:
                ordem_perg = len(dominio.get_perguntas_ativas()) + 1
                
            pergunta = Pergunta(
                dominio_versao_id=dominio.id,
                texto=pergunta_texto,
                descricao=pergunta_descricao,
                referencia=pergunta_referencia if pergunta_referencia else None,
                recomendacao=pergunta_recomendacao if pergunta_recomendacao else None,
                light=pergunta_light,
                ordem=ordem_perg
            )
            db.session.add(pergunta)
            perguntas_criadas += 1
        
        db.session.commit()
        
        # Registrar importação CSV na auditoria
        from models.auditoria import Auditoria
        Auditoria.registrar(
            acao='import_csv',
            entidade='assessment_versao',
            entidade_id=versao_id,
            entidade_nome=f'{versao.tipo.nome} v{versao.versao}',
            descricao=f'Importou CSV para "{versao.tipo.nome}" v{versao.versao}',
            detalhes={
                'dominios_criados': len(dominios_criados),
                'perguntas_criadas': perguntas_criadas,
                'arquivo_nome': arquivo.filename
            }
        )
        
        flash(f'Importação concluída! {len(dominios_criados)} domínios e {perguntas_criadas} perguntas criadas.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao processar CSV: {str(e)}', 'error')
    
    return redirect(url_for('assessment_admin.editar_versao', versao_id=versao_id))

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
        # Ler arquivo CSV com separador ponto e vírgula
        stream = io.StringIO(arquivo.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.DictReader(stream, delimiter=';')
        
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
        for row in csv_input:
            dominio_nome = row.get('Dominio', '').strip()
            dominio_descricao = row.get('DescriçãoDominio', '').strip()
            dominio_ordem = row.get('OrdemDominio', '').strip()
            pergunta_texto = row.get('Pergunta', '').strip()
            pergunta_descricao = row.get('DescriçãoPergunta', '').strip()
            pergunta_referencia = row.get('Referência', '').strip()
            pergunta_recomendacao = row.get('Recomendação', '').strip()
            pergunta_light = row.get('Light', '').strip().lower() in ['1', 'sim', 'true', 's']
            pergunta_ordem = row.get('OrdemPergunta', '').strip()
            
            if not dominio_nome or not pergunta_texto:
                continue
            
            # Criar domínio se não existir
            if dominio_nome not in dominios_criados:
                try:
                    ordem_dom = int(dominio_ordem) if dominio_ordem else len(dominios_criados) + 1
                except ValueError:
                    ordem_dom = len(dominios_criados) + 1
                    
                dominio = AssessmentDominio(
                    versao_id=nova_versao.id,
                    nome=dominio_nome,
                    descricao=dominio_descricao,
                    ordem=ordem_dom
                )
                db.session.add(dominio)
                db.session.flush()
                dominios_criados[dominio_nome] = dominio
            
            # Criar pergunta
            dominio = dominios_criados[dominio_nome]
            try:
                ordem_perg = int(pergunta_ordem) if pergunta_ordem else 1
            except ValueError:
                ordem_perg = 1
            
            pergunta = Pergunta(
                dominio_versao_id=dominio.id,
                texto=pergunta_texto,
                descricao=pergunta_descricao,
                referencia=pergunta_referencia if pergunta_referencia else None,
                recomendacao=pergunta_recomendacao if pergunta_recomendacao else None,
                light=pergunta_light,
                ordem=ordem_perg
            )
            db.session.add(pergunta)
            perguntas_criadas += 1
        
        db.session.commit()
        
        # Registrar criação de nova versão e importação CSV na auditoria
        from models.auditoria import Auditoria
        Auditoria.registrar(
            acao='create',
            entidade='assessment_versao',
            entidade_id=nova_versao.id,
            entidade_nome=f'{tipo.nome} v{nova_versao_num}',
            descricao=f'Criou nova versão {nova_versao_num} para "{tipo.nome}" via importação CSV',
            detalhes={
                'tipo_id': tipo.id,
                'versao': nova_versao_num,
                'dominios_criados': len(dominios_criados),
                'perguntas_criadas': perguntas_criadas,
                'arquivo_nome': arquivo.filename
            }
        )
        
        flash(f'Importação concluída! Criados {len(dominios_criados)} domínios e {perguntas_criadas} perguntas na versão {nova_versao_num}', 'success')
        return redirect(url_for('assessment_admin.editar_versao', versao_id=nova_versao.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro na importação: {str(e)}', 'error')
        return redirect(url_for('assessment_admin.importar_csv'))