from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import logging
from app import db
from models.usuario import Usuario
from models.cliente import Cliente, ClienteAssessment
from models.respondente import Respondente
from models.assessment_version import AssessmentTipo
from models.dominio import Dominio
from models.pergunta import Pergunta
from models.resposta import Resposta
from models.logo import Logo
from models.configuracao import Configuracao
from forms.admin_forms import DominioForm, PerguntaForm, LogoForm
from forms.cliente_forms import ClienteForm, ResponenteForm, TipoAssessmentForm, ImportacaoCSVForm
from forms.configuracao_forms import ConfiguracaoForm
from utils.auth_utils import admin_required
from utils.two_factor_utils import reset_user_2fa, get_user_2fa_config
from utils.upload_utils import allowed_file, save_uploaded_file
from utils.csv_utils import processar_csv_importacao, gerar_template_csv

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Dashboard principal do administrador com informações completas e fuso horário"""
    
    from models.projeto import Projeto
    from datetime import datetime, timedelta
    from sqlalchemy import func
    import pytz
    
    try:
        # Obter fuso horário configurado
        fuso_horario = Configuracao.get_fuso_horario() or 'America/Sao_Paulo'
        tz = pytz.timezone(fuso_horario)
        agora_local = datetime.now(tz)
        
        # Determinar momento do dia no fuso local
        hora = agora_local.hour
        if hora < 12:
            momento_do_dia = "Bom dia"
        elif hora < 18:
            momento_do_dia = "Boa tarde"
        else:
            momento_do_dia = "Boa noite"
        
        # === ESTATÍSTICAS PRINCIPAIS ===
        stats = {
            'total_clientes': Cliente.query.filter_by(ativo=True).count(),
            'total_respondentes': Respondente.query.filter_by(ativo=True).count(),
            'total_projetos': Projeto.query.filter_by(ativo=True).count(),
            'total_tipos': AssessmentTipo.query.filter_by(ativo=True).count(),
            'total_respostas': Resposta.query.count()
        }
        
        # Clientes criados este mês (no fuso local)
        inicio_mes_local = agora_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        inicio_mes_utc = inicio_mes_local.astimezone(pytz.UTC).replace(tzinfo=None)
        stats['clientes_mes'] = Cliente.query.filter(
            Cliente.data_criacao >= inicio_mes_utc,
            Cliente.ativo == True
        ).count()
        
        # Calcular progresso médio dos projetos
        projetos_ativos = Projeto.query.filter_by(ativo=True).all()
        if projetos_ativos:
            progressos = [projeto.get_progresso_geral() for projeto in projetos_ativos]
            stats['progresso_medio'] = int(sum(progressos) / len(progressos))
            stats['projetos_pendentes'] = len([p for p in progressos if p < 100])
        else:
            stats['progresso_medio'] = 0
            stats['projetos_pendentes'] = 0
        
        # === ATIVIDADES RECENTES (NOVO SISTEMA DE AUDITORIA) ===
        from models.auditoria import Auditoria
        
        # Obter estatísticas de auditoria
        stats_auditoria = Auditoria.estatisticas_dashboard()
        stats.update(stats_auditoria)
        
        # Obter atividades recentes detalhadas
        atividades_recentes = Auditoria.obter_atividades_recentes(limite=20)
        
        # === ATIVIDADE RECENTE (últimos 7 dias) ===
        sete_dias_atras = agora_local - timedelta(days=7)
        sete_dias_utc = sete_dias_atras.astimezone(pytz.UTC).replace(tzinfo=None)
        
        # Atividade por dia
        atividade_diaria = db.session.query(
            func.date(Resposta.data_resposta).label('data'),
            func.count(Resposta.id).label('respostas'),
            func.count(func.distinct(Resposta.respondente_id)).label('respondentes_ativos')
        ).filter(
            Resposta.data_resposta >= sete_dias_utc
        ).group_by(
            func.date(Resposta.data_resposta)
        ).order_by(
            func.date(Resposta.data_resposta).desc()
        ).all()
        
        # === PROJETOS DETALHADOS ===
        projetos_stats = db.session.query(
            Projeto.id,
            Projeto.nome,
            Projeto.data_criacao,
            Cliente.nome.label('cliente_nome'),
            func.count(func.distinct(Resposta.pergunta_id)).label('perguntas_respondidas'),
            func.count(func.distinct(Resposta.respondente_id)).label('respondentes_ativos'),
            func.max(Resposta.data_resposta).label('ultima_atividade')
        ).outerjoin(
            Cliente, Projeto.cliente_id == Cliente.id
        ).outerjoin(
            Resposta, Projeto.id == Resposta.projeto_id
        ).filter(
            Projeto.ativo == True
        ).group_by(
            Projeto.id, Projeto.nome, Projeto.data_criacao, Cliente.nome
        ).order_by(
            Projeto.data_criacao.desc()
        ).limit(10).all()
        
        # Calcular progresso e converter datas para fuso local
        projetos_detalhados = []
        for projeto_stat in projetos_stats:
            projeto = Projeto.query.get(projeto_stat.id)
            progresso = projeto.get_progresso_geral() if projeto else 0
            
            # Converter datas para fuso horário local
            data_criacao_local = None
            ultima_atividade_local = None
            
            if projeto_stat.data_criacao:
                data_criacao_utc = projeto_stat.data_criacao.replace(tzinfo=pytz.UTC)
                data_criacao_local = data_criacao_utc.astimezone(tz)
            
            if projeto_stat.ultima_atividade:
                ultima_atividade_utc = projeto_stat.ultima_atividade.replace(tzinfo=pytz.UTC)
                ultima_atividade_local = ultima_atividade_utc.astimezone(tz)
            
            projetos_detalhados.append({
                'projeto': projeto_stat,
                'progresso': progresso,
                'data_criacao_local': data_criacao_local,
                'ultima_atividade_local': ultima_atividade_local
            })
        
        # === TIPOS DE ASSESSMENT - ESTATÍSTICAS (Sistema Novo) ===
        tipos_stats = []
        for tipo in AssessmentTipo.query.filter_by(ativo=True).all():
            # Buscar versão ativa
            versao_ativa = tipo.get_versao_ativa()
            if versao_ativa:
                # Contar domínios e perguntas desta versão
                from models.assessment_version import AssessmentDominio
                dominios_count = AssessmentDominio.query.filter_by(versao_id=versao_ativa.id, ativo=True).count()
                perguntas_count = db.session.query(Pergunta).join(
                    AssessmentDominio, Pergunta.dominio_versao_id == AssessmentDominio.id
                ).filter(
                    AssessmentDominio.versao_id == versao_ativa.id,
                    AssessmentDominio.ativo == True,
                    Pergunta.ativo == True
                ).count()
                
                # Contar projetos usando esta versão
                projetos_usando = db.session.execute(
                    db.text("""
                        SELECT COUNT(DISTINCT p.id) 
                        FROM projetos p 
                        JOIN projeto_assessments pa ON p.id = pa.projeto_id 
                        WHERE pa.versao_assessment_id = :versao_id AND p.ativo = true
                    """), {'versao_id': versao_ativa.id}
                ).scalar() or 0
                
                # Contar respostas para esta versão
                total_respostas = db.session.execute(
                    db.text("""
                        SELECT COUNT(r.id) 
                        FROM respostas r 
                        JOIN projetos p ON r.projeto_id = p.id 
                        JOIN projeto_assessments pa ON p.id = pa.projeto_id 
                        WHERE pa.versao_assessment_id = :versao_id
                    """), {'versao_id': versao_ativa.id}
                ).scalar() or 0
            else:
                dominios_count = 0
                perguntas_count = 0
                projetos_usando = 0
                total_respostas = 0
            
            tipos_stats.append({
                'nome': tipo.nome,
                'descricao': tipo.descricao,
                'projetos_usando': projetos_usando,
                'total_respostas': total_respostas,
                'dominios_count': dominios_count,
                'perguntas_count': perguntas_count
            })
        
        # === CLIENTES MAIS ATIVOS ===
        clientes_stats = db.session.query(
            Cliente.id,
            Cliente.nome,
            Cliente.razao_social,
            func.count(func.distinct(Projeto.id)).label('projetos_count'),
            func.count(func.distinct(Respondente.id)).label('respondentes_count'),
            func.count(Resposta.id).label('respostas_count'),
            func.max(Resposta.data_resposta).label('ultima_atividade')
        ).outerjoin(
            Projeto, Cliente.id == Projeto.cliente_id
        ).outerjoin(
            Respondente, Cliente.id == Respondente.cliente_id
        ).outerjoin(
            Resposta, Projeto.id == Resposta.projeto_id
        ).filter(
            Cliente.ativo == True
        ).group_by(
            Cliente.id, Cliente.nome, Cliente.razao_social
        ).order_by(
            func.count(Resposta.id).desc()
        ).limit(5).all()
        
        # Converter última atividade dos clientes para fuso local
        clientes_detalhados = []
        for cliente_stat in clientes_stats:
            ultima_atividade_local = None
            if cliente_stat.ultima_atividade:
                ultima_atividade_utc = cliente_stat.ultima_atividade.replace(tzinfo=pytz.UTC)
                ultima_atividade_local = ultima_atividade_utc.astimezone(tz)
            
            clientes_detalhados.append({
                'cliente': cliente_stat,
                'ultima_atividade_local': ultima_atividade_local
            })
        
        # === ALERTAS INTELIGENTES ===
        alertas = []
        
        # Projetos sem respondentes
        from models.projeto import ProjetoRespondente
        projetos_com_respondentes = db.session.query(ProjetoRespondente.projeto_id).distinct()
        projetos_sem_respondentes = db.session.query(Projeto).filter(
            Projeto.ativo == True,
            ~Projeto.id.in_(projetos_com_respondentes)
        ).count()
        
        if projetos_sem_respondentes > 0:
            alertas.append({
                'tipo': 'warning',
                'icone': 'fa-users',
                'titulo': 'Projetos sem Respondentes',
                'mensagem': f'{projetos_sem_respondentes} projeto(s) ainda não possuem respondentes associados',
                'acao_url': url_for('projeto.listar'),
                'acao_texto': 'Gerenciar Projetos'
            })
        
        # Clientes sem projetos
        clientes_sem_projetos = Cliente.query.filter_by(ativo=True).filter(
            ~Cliente.id.in_(
                db.session.query(Projeto.cliente_id).filter(Projeto.ativo == True)
            )
        ).count()
        
        if clientes_sem_projetos > 0:
            alertas.append({
                'tipo': 'info',
                'icone': 'fa-building',
                'titulo': 'Clientes sem Projetos',
                'mensagem': f'{clientes_sem_projetos} cliente(s) ainda não possuem projetos',
                'acao_url': url_for('projeto.listar'),
                'acao_texto': 'Criar Projeto'
            })
        
        return render_template('admin/dashboard.html',
                             momento_do_dia=momento_do_dia,
                             stats=stats,
                             atividade_diaria=atividade_diaria,
                             projetos_detalhados=projetos_detalhados,
                             tipos_stats=tipos_stats,
                             clientes_detalhados=clientes_detalhados,
                             alertas=alertas,
                             atividades_recentes=atividades_recentes,
                             agora_local=agora_local,
                             fuso_horario=fuso_horario)
                             
    except Exception as e:
        import logging
        logging.error(f"Erro no dashboard: {e}")
        flash('Erro ao carregar dashboard. Tente novamente.', 'danger')
        # Retornar dados básicos em caso de erro
        stats = {
            'total_clientes': 0,
            'total_respondentes': 0,
            'total_projetos': 0,
            'total_tipos': 0,
            'total_respostas': 0,
            'progresso_medio': 0,
            'projetos_pendentes': 0,
            'clientes_mes': 0
        }
        return render_template('admin/dashboard.html', 
                             momento_do_dia="Olá",
                             stats=stats,
                             atividade_diaria=[],
                             projetos_detalhados=[],
                             tipos_stats=[],
                             clientes_detalhados=[],
                             alertas=[],
                             agora_local=datetime.now(),
                             fuso_horario="UTC")

@admin_bp.route('/clientes')
@login_required
@admin_required
def clientes():
    """Lista todos os clientes do sistema"""
    from models.cliente import Cliente
    from models.projeto import Projeto
    from models.respondente import Respondente
    from sqlalchemy import func
    
    # Buscar todos os clientes com estatísticas
    clientes = db.session.query(Cliente).filter_by(ativo=True).all()
    
    clientes_data = []
    for cliente in clientes:
        # Contar projetos do cliente
        projetos_count = Projeto.query.filter_by(cliente_id=cliente.id, ativo=True).count()
        
        # Contar respondentes do cliente
        respondentes_count = Respondente.query.filter_by(cliente_id=cliente.id, ativo=True).count()
        
        clientes_data.append({
            'cliente': cliente,
            'projetos_count': projetos_count,
            'respondentes_count': respondentes_count
        })
    
    return render_template('admin/clientes.html', clientes=clientes_data)

@admin_bp.route('/clientes/<int:cliente_id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_cliente(cliente_id):
    """Edita um cliente existente"""
    from models.cliente import Cliente
    from forms.cliente_forms import ClienteForm
    from flask import request, flash, redirect, url_for
    
    cliente = Cliente.query.get_or_404(cliente_id)
    form = ClienteForm(obj=cliente)
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            # Atualizar dados do cliente
            cliente.nome = form.nome.data
            cliente.razao_social = form.razao_social.data
            cliente.cnpj = form.cnpj.data
            cliente.localidade = form.localidade.data
            cliente.segmento = form.segmento.data
            
            # Processar upload de logo se houver
            if form.logo.data:
                from utils.upload_utils import save_uploaded_file
                filename = save_uploaded_file(form.logo.data, 'logos')
                if filename:
                    cliente.logo_path = filename
            
            db.session.commit()
            flash(f'Cliente "{cliente.nome}" atualizado com sucesso!', 'success')
            return redirect(url_for('admin.clientes'))
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar cliente. Tente novamente.', 'danger')
            logging.error(f"Erro ao atualizar cliente: {e}")
    
    return render_template('admin/editar_cliente.html', form=form, cliente=cliente)

@admin_bp.route('/clientes/<int:cliente_id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_cliente(cliente_id):
    """Exclui um cliente (soft delete)"""
    from models.cliente import Cliente
    from flask import flash, redirect, url_for
    
    cliente = Cliente.query.get_or_404(cliente_id)
    
    try:
        # Soft delete - apenas marca como inativo
        cliente.ativo = False
        db.session.commit()
        flash(f'Cliente "{cliente.nome}" excluído com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Erro ao excluir cliente. Tente novamente.', 'danger')
        logging.error(f"Erro ao excluir cliente: {e}")
    
    return redirect(url_for('admin.clientes'))

@admin_bp.route('/clientes/<int:cliente_id>/respondentes')
@login_required
@admin_required
def respondentes_cliente(cliente_id):
    """Lista e gerencia respondentes de um cliente específico"""
    from models.cliente import Cliente
    from models.respondente import Respondente
    from models.projeto import Projeto
    from sqlalchemy import func
    
    cliente = Cliente.query.get_or_404(cliente_id)
    
    # Buscar respondentes do cliente
    respondentes = Respondente.query.filter_by(cliente_id=cliente_id, ativo=True).all()
    
    # Buscar projetos do cliente para associações
    projetos = Projeto.query.filter_by(cliente_id=cliente_id, ativo=True).all()
    
    # Estatísticas por respondente
    respondentes_data = []
    for respondente in respondentes:
        # Contar projetos associados
        projetos_associados = db.session.query(func.count(Projeto.id)).filter(
            Projeto.respondentes.any(id=respondente.id)
        ).scalar() or 0
        
        # Contar respostas dadas
        from models.resposta import Resposta
        respostas_count = Resposta.query.filter_by(respondente_id=respondente.id).count()
        
        # Verificar configuração 2FA do respondente
        config_2fa = get_user_2fa_config(respondente)
        
        respondentes_data.append({
            'respondente': respondente,
            'projetos_associados': projetos_associados,
            'respostas_count': respostas_count,
            'config_2fa': config_2fa
        })
    
    return render_template('admin/respondentes_cliente.html', 
                         cliente=cliente, 
                         respondentes=respondentes_data,
                         projetos=projetos)

@admin_bp.route('/clientes/<int:cliente_id>/respondentes/criar', methods=['GET', 'POST'])
@login_required
@admin_required
def criar_respondente(cliente_id):
    """Cria um novo respondente para um cliente específico"""
    from models.cliente import Cliente
    from forms.cliente_forms import ResponenteForm
    from flask import request, flash, redirect, url_for
    
    cliente = Cliente.query.get_or_404(cliente_id)
    form = ResponenteForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            # Criar novo respondente
            respondente = Respondente(
                nome=form.nome.data,
                email=form.email.data,
                login=form.login.data,
                cargo=form.cargo.data,
                setor=form.setor.data,
                cliente_id=cliente_id,
                ativo=form.ativo.data,
                forcar_troca_senha=form.forcar_troca_senha.data
            )
            
            # Hash da senha
            from werkzeug.security import generate_password_hash
            respondente.senha_hash = generate_password_hash(form.senha.data)
            
            db.session.add(respondente)
            db.session.commit()
            
            flash(f'Respondente "{respondente.nome}" criado com sucesso!', 'success')
            return redirect(url_for('admin.respondentes_cliente', cliente_id=cliente_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao criar respondente. Tente novamente.', 'danger')
            logging.error(f"Erro ao criar respondente: {e}")
    
    return render_template('admin/criar_respondente.html', form=form, cliente=cliente)

@admin_bp.route('/respondentes/<int:respondente_id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_respondente(respondente_id):
    """Edita um respondente existente"""
    from forms.cliente_forms import ResponenteForm
    from flask import request, flash, redirect, url_for
    
    respondente = Respondente.query.get_or_404(respondente_id)
    form = ResponenteForm(obj=respondente)
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            # Atualizar dados do respondente
            respondente.nome = form.nome.data
            respondente.email = form.email.data
            respondente.login = form.login.data
            respondente.cargo = form.cargo.data
            respondente.setor = form.setor.data
            respondente.ativo = form.ativo.data
            respondente.forcar_troca_senha = form.forcar_troca_senha.data
            
            # Atualizar senha se fornecida
            if form.senha.data:
                from werkzeug.security import generate_password_hash
                respondente.senha_hash = generate_password_hash(form.senha.data)
            
            db.session.commit()
            flash(f'Respondente "{respondente.nome}" atualizado com sucesso!', 'success')
            return redirect(url_for('admin.respondentes_cliente', cliente_id=respondente.cliente_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar respondente. Tente novamente.', 'danger')
            logging.error(f"Erro ao atualizar respondente: {e}")
    
    return render_template('admin/editar_respondente.html', form=form, respondente=respondente)

@admin_bp.route('/respondentes/<int:respondente_id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_respondente(respondente_id):
    """Exclui um respondente (soft delete)"""
    from flask import flash, redirect, url_for
    
    respondente = Respondente.query.get_or_404(respondente_id)
    cliente_id = respondente.cliente_id
    
    try:
        # Soft delete - apenas marca como inativo
        respondente.ativo = False
        db.session.commit()
        flash(f'Respondente "{respondente.nome}" excluído com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Erro ao excluir respondente. Tente novamente.', 'danger')
        logging.error(f"Erro ao excluir respondente: {e}")
    
    return redirect(url_for('admin.respondentes_cliente', cliente_id=cliente_id))

@admin_bp.route('/reset-respondente-2fa/<int:respondente_id>', methods=['POST'])
@admin_required
def reset_respondente_2fa(respondente_id):
    """Reset do 2FA de um respondente por parte do administrador"""
    
    respondente = Respondente.query.get_or_404(respondente_id)
    cliente_id = respondente.cliente_id
    
    try:
        # Obter configuração 2FA do respondente
        config_2fa = get_user_2fa_config(respondente)
        
        if not config_2fa or not config_2fa.is_active:
            flash('Respondente não possui 2FA ativo.', 'warning')
            return redirect(url_for('admin.respondentes_cliente', cliente_id=cliente_id))
        
        # Resetar 2FA
        if reset_user_2fa(respondente):
            # Tentar registrar na auditoria (se disponível)
            try:
                from models.auditoria import registrar_auditoria
                registrar_auditoria(
                    acao='admin_reset_2fa_respondente',
                    usuario_tipo='admin',
                    usuario_id=current_user.id,
                    usuario_nome=current_user.nome,
                    detalhes=f'Admin resetou 2FA do respondente {respondente.nome} ({respondente.email})',
                    ip_address=request.remote_addr
                )
            except ImportError:
                # Sistema de auditoria não disponível
                logging.info(f'Admin {current_user.nome} resetou 2FA do respondente {respondente.nome}')
            except Exception as e:
                logging.error(f'Erro ao registrar auditoria: {e}')
            
            flash(f'2FA do respondente {respondente.nome} foi resetado com sucesso. Ele precisará configurar novamente no próximo login.', 'success')
        else:
            flash('Erro ao resetar 2FA do respondente.', 'danger')
            
    except Exception as e:
        logging.error(f'Erro ao resetar 2FA do respondente: {e}')
        flash('Erro interno ao resetar 2FA. Tente novamente.', 'danger')
    
    return redirect(url_for('admin.respondentes_cliente', cliente_id=cliente_id))

@admin_bp.route('/grupos')
@login_required
@admin_required
def listar_grupos():
    """Listar todos os grupos únicos de assessments públicos (agrupados por TAG + TIPO)"""
    from models.assessment_publico import AssessmentPublico
    from sqlalchemy import func
    
    # Buscar todos os grupos únicos (não nulos) com contagem
    # MUDANÇA CONCEITUAL: Agrupamento por (grupo, tipo_assessment_id)
    grupos_query = db.session.query(
        AssessmentPublico.grupo,
        AssessmentPublico.tipo_assessment_id,
        func.count(AssessmentPublico.id).label('total_assessments'),
        func.max(AssessmentPublico.data_conclusao).label('ultima_atividade')
    ).filter(
        AssessmentPublico.grupo.isnot(None),
        AssessmentPublico.data_conclusao.isnot(None)  # Apenas assessments concluídos
    ).group_by(
        AssessmentPublico.grupo,
        AssessmentPublico.tipo_assessment_id
    ).order_by(
        func.max(AssessmentPublico.data_conclusao).desc()
    ).all()
    
    # Converter para lista de dicionários com dados do tipo
    grupos = []
    for grupo, tipo_id, total, ultima in grupos_query:
        # Buscar informações do tipo de assessment
        tipo = AssessmentTipo.query.get(tipo_id)
        
        grupos.append({
            'nome': grupo,
            'tipo_id': tipo_id,
            'tipo_nome': tipo.nome if tipo else 'Desconhecido',
            'total_assessments': total,
            'ultima_atividade': ultima
        })
    
    return render_template('admin/grupos_lista.html', grupos=grupos)

def calcular_estatisticas_grupo(grupo_nome, tipo_assessment_id):
    """Função auxiliar para calcular estatísticas de um grupo (reutilizável)
    
    MUDANÇA CONCEITUAL: Agora filtra por (grupo + tipo_assessment_id)
    """
    from models.assessment_publico import AssessmentPublico
    from models.assessment_version import AssessmentDominio
    from sqlalchemy import func
    
    # Buscar todos os assessments concluídos deste grupo + tipo
    assessments = AssessmentPublico.query.filter_by(
        grupo=grupo_nome,
        tipo_assessment_id=tipo_assessment_id
    ).filter(
        AssessmentPublico.data_conclusao.isnot(None)
    ).all()
    
    if not assessments:
        return None
    
    # Calcular estatísticas gerais
    pontuacoes_gerais = [a.calcular_pontuacao_geral() for a in assessments]
    pontuacao_media_geral = sum(pontuacoes_gerais) / len(pontuacoes_gerais) if pontuacoes_gerais else 0
    
    # Identificar todos os domínios únicos respondidos
    dominios_dict = {}
    
    for assessment in assessments:
        try:
            for dominio in assessment.get_dominios_respondidos():
                if dominio.id not in dominios_dict:
                    dominios_dict[dominio.id] = {
                        'dominio': dominio,
                        'pontuacoes': []
                    }
                
                pontuacao_dominio = assessment.calcular_pontuacao_dominio(dominio.id)
                dominios_dict[dominio.id]['pontuacoes'].append(pontuacao_dominio)
        except Exception as e:
            logging.error(f"Erro ao processar domínios do assessment {assessment.id}: {e}")
            continue
    
    # Calcular médias por domínio
    dominios_estatisticas = []
    for dominio_data in dominios_dict.values():
        pontuacoes = dominio_data['pontuacoes']
        media = sum(pontuacoes) / len(pontuacoes) if pontuacoes else 0
        minima = min(pontuacoes) if pontuacoes else 0
        maxima = max(pontuacoes) if pontuacoes else 0
        
        dominios_estatisticas.append({
            'dominio': dominio_data['dominio'],
            'media': round(media, 1),
            'minima': round(minima, 1),
            'maxima': round(maxima, 1),
            'total_respostas': len(pontuacoes)
        })
    
    # Ordenar por média decrescente
    dominios_estatisticas.sort(key=lambda x: x['media'], reverse=True)
    
    # Estatísticas adicionais
    estatisticas = {
        'total_assessments': len(assessments),
        'pontuacao_media_geral': round(pontuacao_media_geral, 1),
        'pontuacao_minima': round(min(pontuacoes_gerais), 1) if pontuacoes_gerais else 0,
        'pontuacao_maxima': round(max(pontuacoes_gerais), 1) if pontuacoes_gerais else 0,
        'primeira_resposta': min(a.data_conclusao for a in assessments if a.data_conclusao),
        'ultima_resposta': max(a.data_conclusao for a in assessments if a.data_conclusao)
    }
    
    # Tipos de assessment utilizados
    tipos_utilizados = {}
    for assessment in assessments:
        tipo = assessment.tipo_assessment
        if tipo and tipo.id not in tipos_utilizados:
            tipos_utilizados[tipo.id] = {
                'tipo': tipo,
                'quantidade': 0
            }
        if tipo:
            tipos_utilizados[tipo.id]['quantidade'] += 1
    
    return {
        'estatisticas': estatisticas,
        'dominios_estatisticas': dominios_estatisticas,
        'tipos_utilizados': list(tipos_utilizados.values())
    }

@admin_bp.route('/grupos/<string:grupo_nome>/<int:tipo_id>')
@login_required
@admin_required
def estatisticas_grupo(grupo_nome, tipo_id):
    """Exibir estatísticas médias de um grupo específico (TAG + TIPO)"""
    logging.info(f"===== ACESSANDO ESTATÍSTICAS DO GRUPO: '{grupo_nome}' (Tipo: {tipo_id}) =====")
    
    try:
        # Buscar informações do tipo
        tipo = AssessmentTipo.query.get(tipo_id)
        if not tipo:
            flash(f'Tipo de assessment #{tipo_id} não encontrado.', 'danger')
            return redirect(url_for('admin.listar_grupos'))
        
        dados = calcular_estatisticas_grupo(grupo_nome, tipo_id)
        
        if not dados:
            flash(f'Nenhum assessment concluído encontrado para o grupo "{grupo_nome}" (tipo: {tipo.nome}).', 'warning')
            return redirect(url_for('admin.listar_grupos'))
        
        return render_template('admin/grupos_estatisticas.html',
                             grupo_nome=grupo_nome,
                             tipo_id=tipo_id,
                             tipo_nome=tipo.nome,
                             estatisticas=dados['estatisticas'],
                             dominios_estatisticas=dados['dominios_estatisticas'],
                             tipos_utilizados=dados['tipos_utilizados'])
    
    except Exception as e:
        logging.error(f"Erro ao exibir estatísticas do grupo '{grupo_nome}' (tipo {tipo_id}): {e}")
        import traceback
        logging.error(traceback.format_exc())
        flash(f'Erro ao carregar estatísticas do grupo "{grupo_nome}". Por favor, contate o administrador.', 'danger')
        return redirect(url_for('admin.listar_grupos'))

@admin_bp.route('/grupos/<string:grupo_nome>/<int:tipo_id>/api')
@login_required
@admin_required
def estatisticas_grupo_api(grupo_nome, tipo_id):
    """API para retornar estatísticas de um grupo em JSON (para auto-refresh)"""
    from flask import jsonify
    
    try:
        dados = calcular_estatisticas_grupo(grupo_nome, tipo_id)
        
        if not dados:
            return jsonify({'error': 'Nenhum assessment encontrado'}), 404
        
        # Converter objetos para dicionários serializáveis
        dominios_json = []
        for item in dados['dominios_estatisticas']:
            dominios_json.append({
                'nome': item['dominio'].nome,
                'media': item['media'],
                'minima': item['minima'],
                'maxima': item['maxima'],
                'total_respostas': item['total_respostas']
            })
        
        tipos_json = []
        for item in dados['tipos_utilizados']:
            tipos_json.append({
                'nome': item['tipo'].nome,
                'quantidade': item['quantidade']
            })
        
        # Converter datas para string
        estatisticas_json = dados['estatisticas'].copy()
        if estatisticas_json.get('primeira_resposta'):
            estatisticas_json['primeira_resposta'] = estatisticas_json['primeira_resposta'].strftime('%d/%m/%Y %H:%M')
        if estatisticas_json.get('ultima_resposta'):
            estatisticas_json['ultima_resposta'] = estatisticas_json['ultima_resposta'].strftime('%d/%m/%Y %H:%M')
        
        return jsonify({
            'estatisticas': estatisticas_json,
            'dominios_estatisticas': dominios_json,
            'tipos_utilizados': tipos_json
        })
    
    except Exception as e:
        logging.error(f"Erro ao buscar estatísticas API do grupo '{grupo_nome}': {e}")
        return jsonify({'error': str(e)}), 500