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
from models.configuracao import Configuracao
from forms.admin_forms import DominioForm, PerguntaForm, LogoForm
from forms.cliente_forms import ClienteForm, ResponenteForm, TipoAssessmentForm, ImportacaoCSVForm
from forms.configuracao_forms import ConfiguracaoForm
from utils.auth_utils import admin_required
from utils.upload_utils import allowed_file, save_uploaded_file
from utils.csv_utils import processar_csv_importacao, gerar_template_csv

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Dashboard principal do administrador com informações completas"""
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    # Determinar momento do dia
    hora = datetime.now().hour
    if hora < 12:
        momento_do_dia = "Bom dia"
    elif hora < 18:
        momento_do_dia = "Boa tarde"
    else:
        momento_do_dia = "Boa noite"
    
    # Estatísticas principais
    total_clientes = Cliente.query.filter_by(ativo=True).count()
    total_respondentes = Respondente.query.count()
    respondentes_ativos = Respondente.query.filter_by(ativo=True).count()
    total_respostas = Resposta.query.count()
    total_assessments = ClienteAssessment.query.filter_by(ativo=True).count()
    
    # Clientes criados este mês
    inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    clientes_mes = Cliente.query.filter(
        Cliente.data_criacao >= inicio_mes,
        Cliente.ativo == True
    ).count()
    
    # Calcular progresso médio e assessments pendentes
    progresso_medio = 0
    assessments_pendentes = 0
    
    if total_assessments > 0:
        progressos = []
        for ca in ClienteAssessment.query.filter_by(ativo=True).all():
            total_perguntas = Pergunta.query.join(Dominio).filter(
                Dominio.tipo_assessment_id == ca.tipo_assessment_id,
                Dominio.ativo == True,
                Pergunta.ativo == True
            ).count()
            
            respostas_cliente = 0
            for respondente in ca.cliente.respondentes:
                respostas_cliente += Resposta.query.join(Pergunta).join(Dominio).filter(
                    Resposta.respondente_id == respondente.id,
                    Dominio.tipo_assessment_id == ca.tipo_assessment_id
                ).count()
            
            if total_perguntas > 0 and ca.cliente.respondentes:
                progresso = (respostas_cliente / (total_perguntas * len(ca.cliente.respondentes)) * 100)
                progressos.append(progresso)
                if progresso < 100:
                    assessments_pendentes += 1
        
        progresso_medio = sum(progressos) / len(progressos) if progressos else 0
    
    # Estatísticas organizadas
    estatisticas = {
        'total_clientes': total_clientes,
        'clientes_mes': clientes_mes,
        'total_respondentes': total_respondentes,
        'respondentes_ativos': respondentes_ativos,
        'total_assessments': total_assessments,
        'assessments_pendentes': assessments_pendentes,
        'progresso_medio': progresso_medio,
        'total_respostas': total_respostas
    }
    
    # Distribuição por tipo de assessment
    tipos_assessment = []
    for tipo in TipoAssessment.query.filter_by(ativo=True).all():
        total_clientes_tipo = ClienteAssessment.query.filter_by(
            tipo_assessment_id=tipo.id,
            ativo=True
        ).count()
        
        tipos_assessment.append({
            'nome': tipo.nome,
            'total_clientes': total_clientes_tipo
        })
    
    # Atividade recente
    atividade_recente = []
    
    # Últimos clientes criados
    ultimos_clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.data_criacao.desc()).limit(3).all()
    for cliente in ultimos_clientes:
        tempo_delta = datetime.now() - cliente.data_criacao
        if tempo_delta.days == 0:
            tempo_formatado = f"Hoje às {cliente.data_criacao.strftime('%H:%M')}"
        elif tempo_delta.days == 1:
            tempo_formatado = "Ontem"
        else:
            tempo_formatado = f"{tempo_delta.days} dias atrás"
        
        atividade_recente.append({
            'titulo': 'Novo Cliente Cadastrado',
            'descricao': f'{cliente.nome} foi adicionado ao sistema',
            'tempo_formatado': tempo_formatado,
            'icone': 'fa-building',
            'cor': 'primary'
        })
    
    # Últimas respostas de assessments
    ultimas_respostas = Resposta.query.order_by(Resposta.data_resposta.desc()).limit(2).all()
    for resposta in ultimas_respostas:
        tempo_delta = datetime.now() - resposta.data_resposta
        if tempo_delta.days == 0:
            tempo_formatado = f"Hoje às {resposta.data_resposta.strftime('%H:%M')}"
        elif tempo_delta.days == 1:
            tempo_formatado = "Ontem"
        else:
            tempo_formatado = f"{tempo_delta.days} dias atrás"
        
        atividade_recente.append({
            'titulo': 'Resposta de Assessment',
            'descricao': f'{resposta.respondente.nome} respondeu uma pergunta',
            'tempo_formatado': tempo_formatado,
            'icone': 'fa-clipboard-check',
            'cor': 'success'
        })
    
    # Manter apenas as 5 mais recentes
    atividade_recente = atividade_recente[:5]
    
    # Alertas importantes
    alertas_importantes = []
    
    # Verificar clientes sem respondentes
    clientes_sem_respondentes = Cliente.query.filter_by(ativo=True).filter(~Cliente.respondentes.any()).count()
    if clientes_sem_respondentes > 0:
        alertas_importantes.append({
            'tipo': 'warning',
            'icone': 'fa-users',
            'titulo': 'Clientes sem Respondentes',
            'mensagem': f'{clientes_sem_respondentes} cliente(s) não possui(em) respondentes cadastrados',
            'acao_url': url_for('admin.clientes'),
            'acao_texto': 'Gerenciar'
        })
    
    return render_template('admin/dashboard.html',
                         momento_do_dia=momento_do_dia,
                         estatisticas=estatisticas,
                         tipos_assessment=tipos_assessment,
                         atividade_recente=atividade_recente,
                         alertas_importantes=alertas_importantes)

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
    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
    form = ClienteForm()
    return render_template('admin/clientes.html', clientes=clientes, form=form)

@admin_bp.route('/cliente/<int:cliente_id>/respostas/<int:tipo_assessment_id>')
@login_required
@admin_required
def respostas_por_respondente(cliente_id, tipo_assessment_id):
    """Visualizar respostas por respondente"""
    cliente = Cliente.query.get_or_404(cliente_id)
    tipo_assessment = TipoAssessment.query.get_or_404(tipo_assessment_id)
    
    # Buscar respondentes do cliente
    respondentes = Respondente.query.filter_by(cliente_id=cliente_id, ativo=True).all()
    
    # Para cada respondente, calcular estatísticas
    for respondente in respondentes:
        # Contar respostas
        respostas = Resposta.query.filter_by(respondente_id=respondente.id).join(Pergunta).join(Dominio).filter(
            Dominio.tipo_assessment_id == tipo_assessment_id
        ).all()
        respondente.respostas = respostas
        respondente.respostas_count = len(respostas)
        
        # Calcular progresso
        total_perguntas = Pergunta.query.join(Dominio).filter(
            Dominio.tipo_assessment_id == tipo_assessment_id,
            Dominio.ativo == True,
            Pergunta.ativo == True
        ).count()
        
        respondente.progresso = round((respondente.respostas_count / total_perguntas * 100) if total_perguntas > 0 else 0, 1)
        
        # Última atividade
        if respostas:
            respondente.ultima_atividade = max(r.data_resposta for r in respostas)
        else:
            respondente.ultima_atividade = None
    
    return render_template('admin/respostas_por_respondente.html',
                         cliente=cliente,
                         tipo_assessment=tipo_assessment,
                         respondentes=respondentes)

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
            try:
                logo_file = save_uploaded_file(form.logo.data, 'logos')
                if logo_file:
                    logo_path = logo_file
            except Exception as e:
                flash('Erro ao fazer upload do logo.', 'danger')
        
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

@admin_bp.route('/clientes/<int:cliente_id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_cliente(cliente_id):
    """Edita um cliente existente"""
    cliente = Cliente.query.get_or_404(cliente_id)
    form = ClienteForm(obj=cliente)
    
    if request.method == 'POST' and form.validate_on_submit():
        # Processar upload do logo se fornecido
        if form.logo.data:
            try:
                logo_file = save_uploaded_file(form.logo.data, 'logos')
                if logo_file:
                    # Remover logo anterior se existir
                    if cliente.logo_path:
                        try:
                            import os
                            old_logo_path = os.path.join('static/uploads', cliente.logo_path)
                            if os.path.exists(old_logo_path):
                                os.remove(old_logo_path)
                        except:
                            pass  # Continuar mesmo se não conseguir remover o arquivo antigo
                    cliente.logo_path = logo_file
            except Exception as e:
                flash('Erro ao fazer upload do logo.', 'danger')
        
        # Atualizar dados do cliente
        cliente.nome = form.nome.data.strip()
        cliente.razao_social = form.razao_social.data.strip()
        cliente.cnpj = form.cnpj.data.strip() if form.cnpj.data else None
        cliente.localidade = form.localidade.data.strip() if form.localidade.data else None
        cliente.segmento = form.segmento.data.strip() if form.segmento.data else None
        
        try:
            db.session.commit()
            flash('Cliente atualizado com sucesso!', 'success')
            return redirect(url_for('admin.clientes'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar cliente.', 'danger')
    
    return render_template('admin/editar_cliente.html', form=form, cliente=cliente)

@admin_bp.route('/clientes/<int:cliente_id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_cliente(cliente_id):
    """Exclui um cliente"""
    cliente = Cliente.query.get_or_404(cliente_id)
    
    try:
        # Remover logo se existir
        if cliente.logo_path:
            try:
                import os
                logo_path = os.path.join('static/uploads', cliente.logo_path)
                if os.path.exists(logo_path):
                    os.remove(logo_path)
            except:
                pass  # Continuar mesmo se não conseguir remover o arquivo
        
        db.session.delete(cliente)
        db.session.commit()
        flash('Cliente excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao excluir cliente.', 'danger')
    
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
    
    print(f"DEBUG: Associando assessment - Cliente ID: {cliente_id}, Tipo ID: {tipo_assessment_id}")
    
    if not tipo_assessment_id:
        print("DEBUG: Tipo de assessment não informado")
        return jsonify({'success': False, 'message': 'Tipo de assessment não informado'})
    
    try:
        tipo_assessment_id = int(tipo_assessment_id)
    except (ValueError, TypeError):
        print(f"DEBUG: Tipo de assessment inválido: {tipo_assessment_id}")
        return jsonify({'success': False, 'message': 'Tipo de assessment inválido'})
    
    # Verificar se já existe associação
    associacao_existente = db.session.query(ClienteAssessment).filter_by(
        cliente_id=cliente_id,
        tipo_assessment_id=tipo_assessment_id
    ).first()
    
    print(f"DEBUG: Associação existente: {associacao_existente}")
    
    if associacao_existente:
        if not associacao_existente.ativo:
            associacao_existente.ativo = True
            db.session.commit()
            print("DEBUG: Assessment reativado")
            return jsonify({'success': True, 'message': 'Assessment reativado'})
        else:
            print("DEBUG: Assessment já associado")
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
        print("DEBUG: Nova associação criada com sucesso")
        return jsonify({'success': True, 'message': 'Assessment associado com sucesso'})
    except Exception as e:
        db.session.rollback()
        print(f"DEBUG: Erro ao criar associação: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao associar assessment: {str(e)}'})

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
    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
    
    assessments_data = []
    for cliente in clientes:
        # Para cada tipo de assessment associado ao cliente
        tipos_assessment = cliente.get_tipos_assessment()
        
        for tipo_assessment in tipos_assessment:
            # Calcular estatísticas por tipo de assessment
            total_perguntas = Pergunta.query.join(Dominio).filter(
                Dominio.tipo_assessment_id == tipo_assessment.id,
                Dominio.ativo == True,
                Pergunta.ativo == True
            ).count()
            
            # Contar respostas de todos os respondentes do cliente para este tipo
            respostas = Resposta.query.join(Respondente).join(Pergunta).join(Dominio).filter(
                Respondente.cliente_id == cliente.id,
                Dominio.tipo_assessment_id == tipo_assessment.id,
                Respondente.ativo == True
            ).all()
            
            respostas_dadas = len(respostas)
            progresso = round((respostas_dadas / total_perguntas * 100) if total_perguntas > 0 else 0, 1)
            concluido = progresso >= 100
            
            # Calcular média geral das respostas
            if respostas:
                media_geral = sum(r.nota for r in respostas) / len(respostas)
            else:
                media_geral = 0
            
            # Contar respondentes ativos
            respondentes_count = cliente.contar_respondentes()
            
            assessments_data.append({
                'cliente': cliente,
                'tipo_assessment': tipo_assessment,
                'total_perguntas': total_perguntas,
                'respostas_dadas': respostas_dadas,
                'progresso': progresso,
                'concluido': concluido,
                'media_geral': round(media_geral, 2),
                'respondentes_count': respondentes_count
            })
    
    return render_template('admin/assessments.html', assessments_data=assessments_data)

@admin_bp.route('/configuracoes')
@login_required
@admin_required
def configuracoes():
    """Configurações simplificadas do sistema"""
    from models.logo import Logo
    from forms.admin_forms import LogoForm
    from forms.configuracao_forms import ConfiguracaoForm
    from models.configuracao import Configuracao
    
    try:
        # Formulários
        logo_form = LogoForm()
        config_form = ConfiguracaoForm()
        
        # Logo atual
        try:
            logo_atual = Logo.get_logo_ativo()
        except:
            logo_atual = None
        
        # Carregar configurações atuais (com valores padrão seguros)
        try:
            cores = Configuracao.get_cores_sistema()
            escala = Configuracao.get_escala_pontuacao()
            
            # Preencher formulário com valores salvos
            config_form.cor_primaria.data = cores.get('primaria', '#0d6efd')
            config_form.cor_secundaria.data = cores.get('secundaria', '#6c757d')
            config_form.cor_fundo.data = cores.get('fundo', '#ffffff')
            config_form.cor_texto.data = cores.get('texto', '#212529')
            
            try:
                for i in range(6):
                    nome_field = getattr(config_form, f'escala_{i}_nome', None)
                    cor_field = getattr(config_form, f'escala_{i}_cor', None)
                    if nome_field and cor_field and i in escala:
                        nome_field.data = escala[i]['nome']
                        cor_field.data = escala[i]['cor']
            except Exception as e:
                logging.warning(f"Erro ao carregar escala: {e}")
                # Continuar mesmo se a escala der erro
                
        except Exception as e:
            import logging
            logging.error(f"Erro ao carregar configurações: {e}")
            # Usar valores padrão
        
        return render_template('admin/configuracoes.html',
                             logo_form=logo_form,
                             config_form=config_form,
                             logo_atual=logo_atual)
    except Exception as e:
        import logging
        logging.error(f"Erro na página de configurações: {e}")
        flash('Erro ao carregar configurações.', 'danger')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/configuracoes/salvar', methods=['POST'])
@login_required
@admin_required
def salvar_configuracoes():
    """Salvar configurações do sistema"""
    from forms.configuracao_forms import ConfiguracaoForm
    from models.configuracao import Configuracao
    
    form = ConfiguracaoForm()
    
    # Verificar se é restaurar padrões
    if request.form.get('reset') == 'true':
        try:
            # Remover todas as configurações atuais
            Configuracao.query.delete()
            db.session.commit()
            
            # Reinicializar com valores padrão
            Configuracao.inicializar_configuracoes_padrao()
            
            flash('Configurações restauradas para os valores padrão!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Erro ao restaurar configurações.', 'danger')
        
        return redirect(url_for('admin.configuracoes'))
    
    if form.validate_on_submit():
        try:
            import logging
            logging.info(f"Salvando configurações")
            
            # Salvar apenas as cores básicas primeiro (mais simples)
            configuracoes = [
                ('cor_primaria', form.cor_primaria.data),
                ('cor_secundaria', form.cor_secundaria.data),
                ('cor_fundo', form.cor_fundo.data),
                ('cor_texto', form.cor_texto.data),
            ]
            
            # Tentar salvar escala também (se existir)
            try:
                escala_configs = []
                for i in range(6):
                    nome_field = getattr(form, f'escala_{i}_nome', None)
                    cor_field = getattr(form, f'escala_{i}_cor', None)
                    if nome_field and cor_field and nome_field.data and cor_field.data:
                        escala_configs.append((f'escala_{i}_nome', nome_field.data))
                        escala_configs.append((f'escala_{i}_cor', cor_field.data))
                configuracoes.extend(escala_configs)
            except Exception as e:
                logging.warning(f"Erro ao processar escala: {e}")
                # Continuar mesmo se a escala der erro
            
            # Salvar cada configuração usando SQL direto
            for chave, valor in configuracoes:
                if valor:  # Só salvar se tiver valor
                    try:
                        from sqlalchemy import text
                        # Tentar atualizar primeiro
                        result = db.session.execute(
                            text("UPDATE configuracoes SET valor = :valor WHERE chave = :chave"),
                            {'valor': valor, 'chave': chave}
                        )
                        
                        # Se não atualizou nenhuma linha, inserir
                        if result.rowcount == 0:
                            db.session.execute(
                                text("INSERT INTO configuracoes (chave, valor, tipo) VALUES (:chave, :valor, 'string')"),
                                {'chave': chave, 'valor': valor}
                            )
                    except Exception as e2:
                        logging.error(f"Erro ao salvar {chave}: {e2}")
                        continue
            
            db.session.commit()
            flash('Configurações salvas com sucesso!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao salvar configurações. Tente novamente.', 'danger')
    else:
        # Exibir erros de validação apenas para campos importantes
        for field, errors in form.errors.items():
            if field in ['cor_primaria', 'cor_secundaria', 'cor_fundo', 'cor_texto']:
                for error in errors:
                    flash(f'{field}: {error}', 'danger')
    
    return redirect(url_for('admin.configuracoes'))

@admin_bp.route('/configuracoes/restaurar', methods=['POST'])
@login_required
@admin_required
def restaurar_configuracoes():
    """Restaurar configurações padrão"""
    from models.configuracao import Configuracao
    
    try:
        # Remover todas as configurações atuais
        Configuracao.query.delete()
        db.session.commit()
        
        # Reinicializar com valores padrão
        Configuracao.inicializar_configuracoes_padrao()
        
        flash('Configurações restauradas para os valores padrão!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao restaurar configurações.', 'danger')
    
    return redirect(url_for('admin.configuracoes'))

@admin_bp.route('/upload_logo', methods=['POST'])
@login_required
@admin_required
def upload_logo():
    """Upload do logo da empresa"""
    from forms.admin_forms import LogoForm
    from models.logo import Logo
    
    form = LogoForm()
    
    if form.validate_on_submit():
        file = form.logo.data
        
        if file and allowed_file(file.filename):
            try:
                # Salvar o arquivo
                filename = save_uploaded_file(file, 'logos')
                caminho_arquivo = f'logos/{filename}'
                
                # Desativar logo anterior
                Logo.query.update({'ativo': False})
                
                # Criar novo registro de logo
                logo = Logo(
                    caminho_arquivo=caminho_arquivo,
                    nome_original=file.filename,
                    tamanho=0,  # Não precisa calcular tamanho
                    tipo_mime=file.content_type,
                    ativo=True
                )
                
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


@admin_bp.route('/projetos')
@login_required
@admin_required
def projetos():
    """Lista todos os projetos do sistema"""
    import logging
    try:
        from models.projeto import Projeto
        projetos = Projeto.query.filter_by(ativo=True).order_by(Projeto.data_criacao.desc()).all()
        
        # Adicionar dados calculados para cada projeto
        for projeto in projetos:
            projeto.progresso = projeto.get_progresso_geral()
            projeto.respondentes_count = len(projeto.get_respondentes_ativos())
            projeto.tipos_count = len(projeto.get_tipos_assessment())
        
        return render_template('admin/projetos/listar.html', projetos=projetos)
        
    except Exception as e:
        logging.error(f"Erro ao carregar projetos: {e}")
        flash('Erro ao carregar lista de projetos.', 'danger')
        return redirect(url_for('admin.dashboard'))



