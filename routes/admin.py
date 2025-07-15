from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
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
        fuso_horario = Configuracao.get_fuso_horario()
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
            stats['progresso_medio'] = sum(progressos) / len(progressos)
            stats['projetos_pendentes'] = len([p for p in progressos if p < 100])
        else:
            stats['progresso_medio'] = 0
            stats['projetos_pendentes'] = 0
        
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
                    cliente.logo = filename
            
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
        
        respondentes_data.append({
            'respondente': respondente,
            'projetos_associados': projetos_associados,
            'respostas_count': respostas_count
        })
    
    return render_template('admin/respondentes_cliente.html', 
                         cliente=cliente, 
                         respondentes=respondentes_data,
                         projetos=projetos)