from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from app import db
from models.usuario import Usuario
from models.cliente import Cliente, ClienteAssessment
from models.respondente import Respondente
from models.tipo_assessment import TipoAssessment
from models.dominio import Dominio
from models.pergunta import Pergunta
from models.resposta import Resposta
from models.logo import Logo
from forms.admin_forms import DominioForm, PerguntaForm, LogoForm
from forms.cliente_forms import ClienteForm, ResponenteForm, TipoAssessmentForm, ImportacaoCSVForm
from utils.auth_utils import admin_required
from utils.upload_utils import allowed_file, save_uploaded_file
from utils.csv_utils import processar_csv_importacao, gerar_template_csv

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Dashboard administrativo"""
    # Estatísticas gerais
    total_clientes = Cliente.query.filter_by(ativo=True).count()
    total_respondentes = Respondente.query.filter_by(ativo=True).count()
    total_tipos_assessment = TipoAssessment.query.filter_by(ativo=True).count()
    total_dominios = Dominio.query.filter_by(ativo=True).count()
    total_perguntas = Pergunta.query.filter_by(ativo=True).count()
    total_respostas = Resposta.query.count()
    
    # Últimas atividades
    ultimas_respostas = Resposta.query.join(Respondente).order_by(
        Resposta.data_resposta.desc()
    ).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_clientes=total_clientes,
                         total_respondentes=total_respondentes,
                         total_tipos_assessment=total_tipos_assessment,
                         total_dominios=total_dominios,
                         total_perguntas=total_perguntas,
                         total_respostas=total_respostas,
                         ultimas_respostas=ultimas_respostas)

# Rotas para Tipos de Assessment
@admin_bp.route('/tipos_assessment')
@login_required
@admin_required
def tipos_assessment():
    """Gerenciamento de tipos de assessment"""
    tipos = TipoAssessment.query.order_by(TipoAssessment.ordem, TipoAssessment.nome).all()
    form = TipoAssessmentForm()
    return render_template('admin/tipos_assessment.html', tipos=tipos, form=form)

@admin_bp.route('/tipos_assessment/criar', methods=['POST'])
@login_required
@admin_required
def criar_tipo_assessment():
    """Cria um novo tipo de assessment"""
    form = TipoAssessmentForm()
    
    if form.validate_on_submit():
        tipo = TipoAssessment(
            nome=form.nome.data.strip(),
            descricao=form.descricao.data.strip() if form.descricao.data else None,
            ordem=int(form.ordem.data),
            ativo=True
        )
        
        try:
            db.session.add(tipo)
            db.session.commit()
            flash('Tipo de assessment criado com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Erro ao criar tipo de assessment.', 'danger')
    
    return redirect(url_for('admin.tipos_assessment'))

@admin_bp.route('/tipos_assessment/<int:tipo_id>/editar', methods=['POST'])
@login_required
@admin_required
def editar_tipo_assessment(tipo_id):
    """Edita um tipo de assessment existente"""
    tipo = TipoAssessment.query.get_or_404(tipo_id)
    
    nome = request.form.get('nome', '').strip()
    descricao = request.form.get('descricao', '').strip()
    ordem = request.form.get('ordem', type=int, default=1)
    
    if not nome:
        flash('Nome do tipo é obrigatório.', 'danger')
        return redirect(url_for('admin.tipos_assessment'))
    
    # Verificar se já existe outro tipo com este nome
    tipo_existente = TipoAssessment.query.filter(
        TipoAssessment.nome == nome,
        TipoAssessment.id != tipo_id
    ).first()
    
    if tipo_existente:
        flash('Já existe outro tipo com este nome.', 'danger')
        return redirect(url_for('admin.tipos_assessment'))
    
    try:
        tipo.nome = nome
        tipo.descricao = descricao if descricao else None
        tipo.ordem = ordem
        db.session.commit()
        flash('Tipo de assessment atualizado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao atualizar tipo de assessment.', 'danger')
    
    return redirect(url_for('admin.tipos_assessment'))

@admin_bp.route('/tipos_assessment/<int:tipo_id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_tipo_assessment(tipo_id):
    """Exclui um tipo de assessment"""
    tipo = TipoAssessment.query.get_or_404(tipo_id)
    
    # Verificar se há domínios associados
    dominios_count = Dominio.query.filter_by(tipo_assessment_id=tipo_id).count()
    if dominios_count > 0:
        flash(f'Não é possível excluir este tipo pois há {dominios_count} domínio(s) associado(s).', 'danger')
        return redirect(url_for('admin.tipos_assessment'))
    
    try:
        db.session.delete(tipo)
        db.session.commit()
        flash('Tipo de assessment excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao excluir tipo de assessment.', 'danger')
    
    return redirect(url_for('admin.tipos_assessment'))

# Rotas para Clientes
@admin_bp.route('/clientes')
@login_required
@admin_required
def clientes():
    """Gerenciamento de clientes"""
    clientes = Cliente.query.order_by(Cliente.nome).all()
    form = ClienteForm()
    return render_template('admin/clientes.html', clientes=clientes, form=form)

@admin_bp.route('/clientes/criar', methods=['POST'])
@login_required
@admin_required
def criar_cliente():
    """Cria um novo cliente"""
    form = ClienteForm()
    
    if form.validate_on_submit():
        # Processar upload do logo se fornecido
        logo_path = None
        if form.logo.data:
            logo_file = save_uploaded_file(form.logo.data, 'logos')
            if logo_file:
                logo_path = logo_file
        
        cliente = Cliente(
            nome=form.nome.data.strip(),
            razao_social=form.razao_social.data.strip(),
            cnpj=form.cnpj.data.strip() if form.cnpj.data else None,
            localidade=form.localidade.data.strip() if form.localidade.data else None,
            segmento=form.segmento.data.strip() if form.segmento.data else None,
            logo_path=logo_path,
            ativo=True
        )
        
        try:
            db.session.add(cliente)
            db.session.commit()
            flash('Cliente criado com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Erro ao criar cliente.', 'danger')
    
    return redirect(url_for('admin.clientes'))

@admin_bp.route('/clientes/<int:cliente_id>/respondentes')
@login_required
@admin_required
def respondentes_cliente(cliente_id):
    """Gerenciamento de respondentes de um cliente"""
    cliente = Cliente.query.get_or_404(cliente_id)
    respondentes = cliente.respondentes
    form = ResponenteForm()
    return render_template('admin/respondentes.html', cliente=cliente, respondentes=respondentes, form=form)

@admin_bp.route('/clientes/<int:cliente_id>/respondentes/criar', methods=['POST'])
@login_required
@admin_required
def criar_respondente(cliente_id):
    """Cria um novo respondente para um cliente"""
    cliente = Cliente.query.get_or_404(cliente_id)
    form = ResponenteForm()
    
    if form.validate_on_submit():
        from werkzeug.security import generate_password_hash
        
        # Verificar se email já existe
        email_existente = Respondente.query.filter_by(email=form.email.data.lower().strip()).first()
        if email_existente:
            flash('Este email já está sendo usado por outro respondente.', 'danger')
            return redirect(url_for('admin.respondentes_cliente', cliente_id=cliente_id))
        
        respondente = Respondente(
            cliente_id=cliente_id,
            nome=form.nome.data.strip(),
            email=form.email.data.lower().strip(),
            senha_hash=generate_password_hash(form.senha.data),
            cargo=form.cargo.data.strip() if form.cargo.data else None,
            setor=form.setor.data.strip() if form.setor.data else None,
            ativo=form.ativo.data
        )
        
        try:
            db.session.add(respondente)
            db.session.commit()
            flash('Respondente criado com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Erro ao criar respondente.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
    
    return redirect(url_for('admin.respondentes_cliente', cliente_id=cliente_id))

@admin_bp.route('/respondentes/<int:respondente_id>/editar', methods=['POST'])
@login_required
@admin_required
def editar_respondente(respondente_id):
    """Edita um respondente"""
    from flask_wtf.csrf import validate_csrf
    
    # Validar CSRF token se disponível
    try:
        validate_csrf(request.form.get('csrf_token'))
    except:
        pass  # Continuar sem CSRF por enquanto
    
    respondente = Respondente.query.get_or_404(respondente_id)
    cliente_id = respondente.cliente_id
    
    try:
        # Atualizar dados do respondente
        respondente.nome = request.form.get('nome')
        respondente.email = request.form.get('email')
        respondente.cargo = request.form.get('cargo') or None
        respondente.setor = request.form.get('setor') or None
        respondente.ativo = bool(request.form.get('ativo'))
        
        # Atualizar senha se fornecida
        nova_senha = request.form.get('senha')
        if nova_senha and nova_senha.strip():
            from werkzeug.security import generate_password_hash
            respondente.senha_hash = generate_password_hash(nova_senha)
        
        # Validar email único (exceto para o próprio respondente)
        email_existente = Respondente.query.filter(
            Respondente.email == respondente.email,
            Respondente.id != respondente_id
        ).first()
        
        if email_existente:
            flash('Este email já está sendo usado por outro respondente.', 'danger')
            return redirect(url_for('admin.respondentes_cliente', cliente_id=cliente_id))
        
        db.session.commit()
        flash('Respondente atualizado com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Erro ao atualizar respondente.', 'danger')
    
    return redirect(url_for('admin.respondentes_cliente', cliente_id=cliente_id))

@admin_bp.route('/respondentes/<int:respondente_id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_respondente(respondente_id):
    """Exclui um respondente"""
    respondente = Respondente.query.get_or_404(respondente_id)
    cliente_id = respondente.cliente_id
    
    try:
        db.session.delete(respondente)
        db.session.commit()
        flash('Respondente excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao excluir respondente.', 'danger')
    
    return redirect(url_for('admin.respondentes_cliente', cliente_id=cliente_id))

@admin_bp.route('/clientes/<int:cliente_id>/assessments')
@login_required
@admin_required
def assessments_cliente(cliente_id):
    """Retorna HTML para gerenciar assessments do cliente"""
    cliente = Cliente.query.get_or_404(cliente_id)
    tipos_assessment = TipoAssessment.query.filter_by(ativo=True).all()
    
    # Assessments já associados ao cliente
    assessments_associados = [ca.tipo_assessment_id for ca in cliente.cliente_assessments if ca.ativo]
    
    html = '<h6>Assessments Disponíveis</h6>'
    html += '<div class="list-group">'
    
    for tipo in tipos_assessment:
        if tipo.id in assessments_associados:
            html += f'''
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1">{tipo.nome}</h6>
                        <small class="text-muted">{tipo.descricao or ''}</small>
                    </div>
                    <div>
                        <span class="badge bg-success me-2">Associado</span>
                        <button class="btn btn-sm btn-outline-danger" onclick="desassociarAssessment({cliente_id}, {tipo.id})">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            '''
        else:
            html += f'''
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1">{tipo.nome}</h6>
                        <small class="text-muted">{tipo.descricao or ''}</small>
                    </div>
                    <div>
                        <button class="btn btn-sm btn-outline-success" onclick="associarAssessment({cliente_id}, {tipo.id})">
                            <i class="fas fa-plus"></i> Associar
                        </button>
                    </div>
                </div>
            '''
    
    html += '</div>'
    
    return html

@admin_bp.route('/clientes/<int:cliente_id>/assessments/associar', methods=['POST'])
@login_required
@admin_required
def associar_assessment_cliente(cliente_id):
    """Associa um assessment ao cliente"""
    cliente = Cliente.query.get_or_404(cliente_id)
    tipo_assessment_id = request.form.get('tipo_assessment_id')
    
    if not tipo_assessment_id:
        return jsonify({'success': False, 'message': 'Tipo de assessment não informado'})
    
    # Verificar se já existe associação
    associacao_existente = db.session.query(ClienteAssessment).filter_by(
        cliente_id=cliente_id,
        tipo_assessment_id=tipo_assessment_id
    ).first()
    
    if associacao_existente:
        if not associacao_existente.ativo:
            associacao_existente.ativo = True
            db.session.commit()
            return jsonify({'success': True, 'message': 'Assessment reativado'})
        else:
            return jsonify({'success': False, 'message': 'Assessment já associado'})
    
    # Criar nova associação
    nova_associacao = ClienteAssessment(
        cliente_id=cliente_id,
        tipo_assessment_id=tipo_assessment_id,
        ativo=True
    )
    
    try:
        db.session.add(nova_associacao)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Assessment associado com sucesso'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Erro ao associar assessment'})

@admin_bp.route('/clientes/<int:cliente_id>/assessments/desassociar', methods=['POST'])
@login_required
@admin_required
def desassociar_assessment_cliente(cliente_id):
    """Desassocia um assessment do cliente"""
    cliente = Cliente.query.get_or_404(cliente_id)
    tipo_assessment_id = request.form.get('tipo_assessment_id')
    
    if not tipo_assessment_id:
        return jsonify({'success': False, 'message': 'Tipo de assessment não informado'})
    
    # Encontrar associação
    associacao = db.session.query(ClienteAssessment).filter_by(
        cliente_id=cliente_id,
        tipo_assessment_id=tipo_assessment_id,
        ativo=True
    ).first()
    
    if not associacao:
        return jsonify({'success': False, 'message': 'Associação não encontrada'})
    
    try:
        associacao.ativo = False
        db.session.commit()
        return jsonify({'success': True, 'message': 'Assessment desassociado com sucesso'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Erro ao desassociar assessment'})

# Rota para Importação CSV
@admin_bp.route('/importar_csv', methods=['GET', 'POST'])
@login_required
@admin_required
def importar_csv():
    """Importação de dados via CSV"""
    form = ImportacaoCSVForm()
    
    if form.validate_on_submit():
        resultado = processar_csv_importacao(form.arquivo_csv.data, form.tipo_assessment_id.data)
        
        if resultado['sucesso']:
            flash(f'Importação concluída! {resultado["dominios_criados"]} domínios e {resultado["perguntas_criadas"]} perguntas criados.', 'success')
        else:
            flash(f'Erro na importação: {"; ".join(resultado["erros"])}', 'danger')
    
    return render_template('admin/importar_csv.html', form=form)

@admin_bp.route('/template_csv')
@login_required
@admin_required
def template_csv():
    """Download do template CSV"""
    from flask import Response
    
    template_content = gerar_template_csv()
    
    return Response(
        template_content,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=template_importacao.csv'}
    )

@admin_bp.route('/dominios')
@login_required
@admin_required
def dominios():
    """Gerenciamento de domínios"""
    dominios = Dominio.query.order_by(Dominio.ordem, Dominio.nome).all()
    tipos_assessment = TipoAssessment.query.filter_by(ativo=True).order_by(TipoAssessment.nome).all()
    tipos_assessment_json = [{'id': ta.id, 'nome': ta.nome} for ta in tipos_assessment]
    form = DominioForm()
    return render_template('admin/dominios.html', dominios=dominios, tipos_assessment=tipos_assessment, tipos_assessment_json=tipos_assessment_json, form=form)

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
        dominio.tipo_assessment_id = request.form.get('tipo_assessment_id', type=int)
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
