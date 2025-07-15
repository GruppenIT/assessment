from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from datetime import datetime
from models.respondente import Respondente
from models.cliente import Cliente
from models.tipo_assessment import TipoAssessment
from models.dominio import Dominio
from models.pergunta import Pergunta
from models.resposta import Resposta
from forms.assessment_forms import RespostaForm
from utils.auth_utils import respondente_required
from app import db

respondente_bp = Blueprint('respondente', __name__)

@respondente_bp.route('/auto-login')
def auto_login():
    """Auto login de teste para respondente Rodrigo"""
    respondente = Respondente.query.filter_by(login='rodrigo.gruppen').first()
    if respondente:
        login_user(respondente)
        session['user_type'] = 'respondente'
        return redirect(url_for('respondente.dashboard'))
    else:
        return "Respondente não encontrado"

@respondente_bp.route('/auto-login-marcelo')
def auto_login_marcelo():
    """Auto login de teste para respondente Marcelo"""
    respondente = Respondente.query.filter_by(login='marcelo.gruppen').first()
    if respondente:
        login_user(respondente)
        session['user_type'] = 'respondente'
        return redirect(url_for('respondente.dashboard'))
    else:
        return "Respondente não encontrado"

# Login removido - agora usa o login unificado em /auth/login

@respondente_bp.route('/dashboard')
@respondente_required
def dashboard():
    """Dashboard do respondente"""    
    if not isinstance(current_user, Respondente):
        return redirect(url_for('auth.login'))
    
    try:
        # Obter projetos do respondente
        from models.projeto import ProjetoRespondente, ProjetoAssessment
        projetos_respondente = ProjetoRespondente.query.filter_by(
            respondente_id=current_user.id,
            ativo=True
        ).all()
        
        projetos_data = []
        for pr in projetos_respondente:
            projeto = pr.projeto
            if not projeto.ativo:
                continue
                
            # Tipos de assessment do projeto
            tipos_assessment = projeto.get_tipos_assessment()
            
            # Calcular progresso colaborativo para cada tipo do projeto
            progressos = {}
            for tipo in tipos_assessment:
                from models.pergunta import Pergunta
                from models.dominio import Dominio
                from models.resposta import Resposta
                
                # Total de perguntas do tipo
                total_perguntas = Pergunta.query.join(Dominio).filter(
                    Dominio.tipo_assessment_id == tipo.id,
                    Dominio.ativo == True,
                    Pergunta.ativo == True
                ).count()
                
                # Perguntas únicas respondidas por qualquer respondente (colaborativo)
                perguntas_respondidas = db.session.query(Pergunta.id).join(
                    Resposta, Pergunta.id == Resposta.pergunta_id
                ).join(Dominio).filter(
                    Resposta.projeto_id == projeto.id,
                    Dominio.tipo_assessment_id == tipo.id,
                    Dominio.ativo == True,
                    Pergunta.ativo == True
                ).distinct().count()
                
                percentual = round((perguntas_respondidas / total_perguntas * 100) if total_perguntas > 0 else 0, 1)
                
                progressos[tipo.id] = {
                    'percentual': percentual,
                    'respondidas': perguntas_respondidas,
                    'total': total_perguntas
                }
            
            projetos_data.append({
                'projeto': projeto,
                'tipos_assessment': tipos_assessment,
                'progressos': progressos,
                'progresso_geral': projeto.get_progresso_geral()  # Usar progresso geral colaborativo
            })
        
        return render_template('respondente/dashboard_projetos.html',
                             respondente=current_user,
                             projetos_data=projetos_data)
                             
    except Exception as e:
        flash('Erro ao carregar dashboard. Entre em contato com o suporte.', 'danger')
        return redirect(url_for('auth.login'))

@respondente_bp.route('/assessment/<int:projeto_id>/<int:tipo_assessment_id>')
@login_required
def assessment(projeto_id, tipo_assessment_id):
    """Assessment de um tipo específico dentro de um projeto"""
    if not isinstance(current_user, Respondente):
        return redirect(url_for('auth.login'))
    
    # Verificar se o respondente tem acesso a este projeto
    from models.projeto import ProjetoRespondente, ProjetoAssessment
    projeto_respondente = ProjetoRespondente.query.filter_by(
        projeto_id=projeto_id,
        respondente_id=current_user.id,
        ativo=True
    ).first()
    
    if not projeto_respondente:
        flash('Acesso negado a este projeto.', 'danger')
        return redirect(url_for('respondente.dashboard'))
    
    # Verificar se o tipo de assessment está no projeto
    projeto_assessment = ProjetoAssessment.query.filter_by(
        projeto_id=projeto_id,
        tipo_assessment_id=tipo_assessment_id
    ).first()
    
    if not projeto_assessment:
        flash('Este tipo de assessment não está disponível neste projeto.', 'danger')
        return redirect(url_for('respondente.dashboard'))
    
    projeto = projeto_respondente.projeto
    tipo_assessment = TipoAssessment.query.get_or_404(tipo_assessment_id)
    dominios = tipo_assessment.get_dominios_ativos()
    
    # Buscar TODAS as respostas do projeto (colaborativo entre respondentes)
    respostas_existentes = {}
    from models.resposta import Resposta
    respostas = Resposta.query.filter_by(
        projeto_id=projeto_id  # Todas as respostas do projeto, não só do respondente atual
    ).all()
    for resposta in respostas:
        respostas_existentes[resposta.pergunta_id] = {
            'nota': resposta.nota,
            'comentario': resposta.comentario,
            'respondente_nome': resposta.respondente.nome if resposta.respondente else 'Desconhecido'
        }
    
    # Criar forms_data para compatibilidade com o template
    forms_data = {}
    for dominio in dominios:
        for pergunta in dominio.get_perguntas_ativas():
            forms_data[pergunta.id] = {
                'pergunta_id': pergunta.id,
                'nota': respostas_existentes.get(pergunta.id, {}).get('nota', 0),
                'comentario': respostas_existentes.get(pergunta.id, {}).get('comentario', ''),
                'respondente_nome': respostas_existentes.get(pergunta.id, {}).get('respondente_nome', ''),
                'resposta': respostas_existentes.get(pergunta.id) if pergunta.id in respostas_existentes else None
            }

    return render_template('respondente/assessment.html',
                         projeto=projeto,
                         tipo_assessment=tipo_assessment, 
                         dominios=dominios,
                         forms_data=forms_data,
                         respostas_existentes=respostas_existentes)

@respondente_bp.route('/assessment/salvar', methods=['POST'])
@login_required
def salvar_resposta():
    """Salva uma resposta via AJAX"""
    if not isinstance(current_user, Respondente):
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403
    
    try:
        data = request.get_json()
        pergunta_id = data.get('pergunta_id')
        projeto_id = data.get('projeto_id')
        nota = data.get('nota')
        comentario = data.get('comentario', '')
        
        # Validar pergunta
        pergunta = Pergunta.query.get(pergunta_id)
        if not pergunta:
            return jsonify({'success': False, 'message': 'Pergunta não encontrada'}), 404
        
        # Verificar acesso ao projeto
        from models.projeto import ProjetoRespondente
        projeto_respondente = ProjetoRespondente.query.filter_by(
            projeto_id=projeto_id,
            respondente_id=current_user.id,
            ativo=True
        ).first()
        
        if not projeto_respondente:
            return jsonify({'success': False, 'message': 'Acesso negado ao projeto'}), 403
        
        # Buscar resposta existente para a pergunta (qualquer respondente do projeto)
        resposta = Resposta.query.filter_by(
            pergunta_id=pergunta_id,
            projeto_id=projeto_id  # Qualquer resposta do projeto para esta pergunta
        ).first()
        
        # Se nota for None, remover resposta (funcionalidade de "desresponder")
        if nota is None:
            if resposta:
                db.session.delete(resposta)
                db.session.commit()
                return jsonify({'success': True, 'message': 'Resposta removida', 'action': 'removed'})
            else:
                return jsonify({'success': True, 'message': 'Nenhuma resposta para remover'})
        
        # Atualizar ou criar resposta
        if resposta:
            resposta.nota = nota
            resposta.comentario = comentario
            resposta.data_atualizacao = datetime.utcnow()
        else:
            # Buscar um usuário admin padrão para compatibilidade
            from models.usuario import Usuario
            admin_user = Usuario.query.first()
            if not admin_user:
                return jsonify({'success': False, 'message': 'Nenhum usuário admin encontrado'}), 500
            
            resposta = Resposta(
                usuario_id=admin_user.id,  # Para compatibilidade com o banco
                respondente_id=current_user.id,
                pergunta_id=pergunta_id,
                projeto_id=projeto_id,  # Associar resposta ao projeto
                nota=nota,
                comentario=comentario
            )
            db.session.add(resposta)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Resposta salva com sucesso', 'action': 'saved'})
        
    except Exception as e:
        db.session.rollback()
        print(f"DEBUG: Erro ao salvar resposta: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@respondente_bp.route('/assessment/finalizar', methods=['POST'])
@login_required
def finalizar_assessment():
    """Finalizar assessment do respondente"""
    try:
        if not isinstance(current_user, Respondente):
            return jsonify({'success': False, 'message': 'Usuário não autorizado'}), 401
        
        # Verificar se o respondente tem respostas
        total_respostas = Resposta.query.filter_by(respondente_id=current_user.id).count()
        
        if total_respostas == 0:
            return jsonify({'success': False, 'message': 'Nenhuma resposta encontrada'}), 400
        
        # Verificar se tem assessments completos
        tipos_assessment = current_user.cliente.get_tipos_assessment()
        algum_completo = False
        
        for tipo in tipos_assessment:
            progresso = current_user.get_progresso_assessment(tipo.id)
            if progresso['percentual'] >= 100:
                algum_completo = True
                break
        
        if not algum_completo:
            return jsonify({'success': False, 'message': 'Você deve completar pelo menos um assessment antes de finalizar'}), 400
        
        # Atualizar data de conclusão do respondente
        current_user.data_conclusao = datetime.utcnow()
        db.session.commit()
        
        print(f"DEBUG: Assessment finalizado pelo respondente {current_user.nome} - {current_user.email}")
        
        return jsonify({
            'success': True, 
            'message': 'Assessment finalizado com sucesso',
            'data_conclusao': current_user.data_conclusao.isoformat()
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"DEBUG: Erro ao finalizar assessment: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@respondente_bp.route('/logout')
@login_required
def logout():
    """Logout do respondente"""
    logout_user()
    session.pop('user_type', None)
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('respondente.login'))