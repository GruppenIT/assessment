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
    respondente = Respondente.query.filter_by(login='rodrigo.melnick').first()
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
    
    # Atualizar último acesso
    from datetime import datetime
    current_user.ultimo_acesso = datetime.now()
    db.session.commit()
    
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
            
            # Obter assessments do projeto para calcular progresso
            assessments_projeto = projeto.assessments
            for assessment in assessments_projeto:
                from models.pergunta import Pergunta
                from models.dominio import Dominio
                from models.resposta import Resposta
                from models.assessment_version import AssessmentDominio
                
                # Determinar tipo e total de perguntas baseado no sistema
                if assessment.versao_assessment_id:
                    # Novo sistema de versionamento
                    versao = assessment.versao_assessment
                    tipo = versao.tipo
                    
                    # Total de perguntas da versão
                    total_perguntas = db.session.query(Pergunta).join(
                        AssessmentDominio, Pergunta.dominio_versao_id == AssessmentDominio.id
                    ).filter(
                        AssessmentDominio.versao_id == versao.id,
                        AssessmentDominio.ativo == True,
                        Pergunta.ativo == True
                    ).count()
                    
                    # Perguntas respondidas do projeto
                    perguntas_respondidas = db.session.query(Pergunta.id).join(
                        Resposta, Pergunta.id == Resposta.pergunta_id
                    ).join(
                        AssessmentDominio, Pergunta.dominio_versao_id == AssessmentDominio.id
                    ).filter(
                        Resposta.projeto_id == projeto.id,
                        AssessmentDominio.versao_id == versao.id,
                        AssessmentDominio.ativo == True,
                        Pergunta.ativo == True
                    ).distinct().count()
                    
                elif assessment.tipo_assessment_id:
                    # Sistema antigo
                    tipo = assessment.tipo_assessment
                    
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
                else:
                    # Sistema sem dados válidos
                    continue
                
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

@respondente_bp.route('/projeto/<int:projeto_id>/estatisticas')
@login_required
@respondente_required
def visualizar_estatisticas(projeto_id):
    """Visualizar estatísticas liberadas de um projeto"""
    if not isinstance(current_user, Respondente):
        return redirect(url_for('auth.login'))
    
    # Verificar se o respondente tem acesso a este projeto
    from models.projeto import ProjetoRespondente, Projeto
    projeto_respondente = ProjetoRespondente.query.filter_by(
        projeto_id=projeto_id,
        respondente_id=current_user.id,
        ativo=True
    ).first()
    
    if not projeto_respondente:
        flash('Acesso negado a este projeto.', 'danger')
        return redirect(url_for('respondente.dashboard'))
    
    projeto = Projeto.query.get_or_404(projeto_id)
    
    # Verificar se o projeto foi liberado para o cliente
    if not projeto.liberado_cliente:
        flash('As estatísticas deste projeto ainda não foram liberadas.', 'warning')
        return redirect(url_for('respondente.dashboard'))
    
    # Importar modelos necessários
    from models.resposta import Resposta
    from models.pergunta import Pergunta
    from models.dominio import Dominio
    from models.assessment_version import AssessmentDominio, AssessmentVersao, AssessmentTipo
    from models.tipo_assessment import TipoAssessment
    from datetime import datetime
    import pytz
    from utils.timezone_utils import format_datetime_local
    
    # Dados do projeto já foram carregados
    # Agora vamos buscar todos os dados estatísticos como na página admin
    
    # Buscar respondentes do projeto
    respondentes_projeto = [pr.respondente for pr in projeto.respondentes if pr.ativo]
    
    # Calcular estatísticas por assessment
    estatisticas_assessments = {}
    
    for projeto_assessment in projeto.assessments:
        if not projeto_assessment.finalizado:
            continue
            
        # Determinar tipo e versão
        tipo = None
        versao = None
        
        if projeto_assessment.versao_assessment_id:
            versao = projeto_assessment.versao_assessment
            tipo = versao.tipo
            dominios_query = AssessmentDominio.query.filter_by(versao_id=versao.id, ativo=True)
        elif projeto_assessment.tipo_assessment_id:
            tipo = projeto_assessment.tipo_assessment
            dominios_query = Dominio.query.filter_by(tipo_assessment_id=tipo.id, ativo=True)
        
        if not tipo:
            continue
        
        # Estatísticas por domínio
        dominios_stats = []
        todas_respostas = []
        
        for dominio in dominios_query.order_by('ordem'):
            # Buscar perguntas do domínio
            if versao:
                perguntas_dominio = Pergunta.query.filter_by(
                    dominio_versao_id=dominio.id,
                    ativo=True
                ).order_by(Pergunta.ordem).all()
            else:
                perguntas_dominio = Pergunta.query.filter_by(
                    dominio_id=dominio.id,
                    ativo=True
                ).order_by(Pergunta.ordem).all()
            
            # Buscar respostas do domínio para este projeto
            respostas_dominio = []
            for pergunta in perguntas_dominio:
                resposta = Resposta.query.filter_by(
                    projeto_id=projeto.id,
                    pergunta_id=pergunta.id
                ).order_by(Resposta.data_resposta.desc()).first()
                
                if resposta:
                    respostas_dominio.append(resposta.nota)
                    todas_respostas.append(resposta.nota)
            
            # Calcular média do domínio
            if respostas_dominio:
                media_dominio = sum(respostas_dominio) / len(respostas_dominio)
            else:
                media_dominio = 0
            
            dominios_stats.append({
                'dominio': dominio,
                'media': media_dominio,
                'total_perguntas': len(perguntas_dominio),
                'respostas_dadas': len(respostas_dominio),
                'respostas': respostas_dominio
            })
        
        # Score geral do assessment
        score_geral = sum(todas_respostas) / len(todas_respostas) if todas_respostas else 0
        
        estatisticas_assessments[tipo.id] = {
            'tipo': tipo,
            'versao': versao,
            'dominios': dominios_stats,
            'score_geral': score_geral,
            'total_respostas': len(todas_respostas)
        }
    
    return render_template('respondente/estatisticas.html',
                         projeto=projeto,
                         respondente=current_user,
                         respondentes_projeto=respondentes_projeto,
                         estatisticas_assessments=estatisticas_assessments)

@respondente_bp.route('/projeto/<int:projeto_id>/relatorio-pdf')
@login_required
@respondente_required
def gerar_relatorio_pdf(projeto_id):
    """Gera relatório PDF para o cliente"""
    if not isinstance(current_user, Respondente):
        return redirect(url_for('auth.login'))
    
    # Verificar se o respondente tem acesso a este projeto
    from models.projeto import ProjetoRespondente, Projeto
    projeto_respondente = ProjetoRespondente.query.filter_by(
        projeto_id=projeto_id,
        respondente_id=current_user.id,
        ativo=True
    ).first()
    
    if not projeto_respondente:
        flash('Acesso negado a este projeto.', 'danger')
        return redirect(url_for('respondente.dashboard'))
    
    projeto = Projeto.query.get_or_404(projeto_id)
    
    # Verificar se o projeto foi liberado para o cliente
    if not projeto.liberado_cliente:
        flash('O relatório deste projeto ainda não foi liberado.', 'warning')
        return redirect(url_for('respondente.dashboard'))
    
    try:
        from utils.pdf_relatorio import gerar_relatorio_pdf_completo
        from datetime import datetime
        
        # Gerar o PDF completo
        filename = gerar_relatorio_pdf_completo(projeto)
        
        from flask import send_file
        return send_file(
            filename,
            as_attachment=True,
            download_name=f"relatorio_assessment_{projeto.nome.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        flash(f'Erro ao gerar o relatório PDF: {str(e)}', 'danger')
        return redirect(url_for('respondente.visualizar_estatisticas', projeto_id=projeto.id))

@respondente_bp.route('/assessment/<int:projeto_id>/<int:tipo_assessment_id>')
@login_required
def assessment(projeto_id, tipo_assessment_id):
    """Assessment de um tipo específico dentro de um projeto"""
    if not isinstance(current_user, Respondente):
        return redirect(url_for('auth.login'))
    
    # Atualizar último acesso
    from datetime import datetime
    current_user.ultimo_acesso = datetime.now()
    db.session.commit()
    
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
        projeto_id=projeto_id
    ).first()
    
    if not projeto_assessment:
        flash('Este tipo de assessment não está disponível neste projeto.', 'danger')
        return redirect(url_for('respondente.dashboard'))
    
    # Determinar o tipo de assessment baseado no sistema usado
    if projeto_assessment.versao_assessment_id:
        # Novo sistema de versionamento
        versao = projeto_assessment.versao_assessment
        tipo_assessment = versao.tipo
        if tipo_assessment.id != tipo_assessment_id:
            flash('Este tipo de assessment não está disponível neste projeto.', 'danger')
            return redirect(url_for('respondente.dashboard'))
    elif projeto_assessment.tipo_assessment_id:
        # Sistema antigo
        if projeto_assessment.tipo_assessment_id != tipo_assessment_id:
            flash('Este tipo de assessment não está disponível neste projeto.', 'danger')
            return redirect(url_for('respondente.dashboard'))
        tipo_assessment = projeto_assessment.tipo_assessment
    else:
        flash('Este tipo de assessment não está disponível neste projeto.', 'danger')
        return redirect(url_for('respondente.dashboard'))
    
    projeto = projeto_respondente.projeto
    
    # Verificar se o assessment ainda pode ser editado
    pode_editar = projeto_assessment.pode_editar()
    
    # Obter domínios baseado no sistema usado
    if projeto_assessment.versao_assessment_id:
        # Novo sistema de versionamento - domínios da versão
        dominios = projeto_assessment.versao_assessment.get_dominios_ativos()
    else:
        # Sistema antigo - domínios do tipo
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

    # Calcular progresso do assessment
    progresso_assessment = projeto_assessment.get_progresso_percentual()
    todas_respondidas = progresso_assessment >= 100
    
    return render_template('respondente/assessment.html',
                         projeto=projeto,
                         projeto_assessment=projeto_assessment,
                         tipo_assessment=tipo_assessment, 
                         dominios=dominios,
                         forms_data=forms_data,
                         respostas_existentes=respostas_existentes,
                         pode_editar=pode_editar,
                         progresso_assessment=progresso_assessment,
                         todas_respondidas=todas_respondidas)

@respondente_bp.route('/assessment/finalizar/<int:projeto_id>/<int:tipo_assessment_id>', methods=['POST'])
@login_required
def finalizar_assessment(projeto_id, tipo_assessment_id):
    """Finaliza um assessment, bloqueando edições futuras"""
    if not isinstance(current_user, Respondente):
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403
    
    # Verificar acesso ao projeto
    from models.projeto import ProjetoRespondente, ProjetoAssessment
    projeto_respondente = ProjetoRespondente.query.filter_by(
        projeto_id=projeto_id,
        respondente_id=current_user.id,
        ativo=True
    ).first()
    
    if not projeto_respondente:
        return jsonify({'success': False, 'message': 'Acesso negado a este projeto'}), 403
    
    # Buscar o assessment específico
    projeto_assessment = ProjetoAssessment.query.filter_by(
        projeto_id=projeto_id
    ).first()
    
    if not projeto_assessment:
        return jsonify({'success': False, 'message': 'Assessment não encontrado'}), 404
    
    # Verificar se ainda pode ser editado
    if not projeto_assessment.pode_editar():
        return jsonify({'success': False, 'message': 'Este assessment já foi finalizado'}), 400
    
    # Verificar se todas as perguntas foram respondidas
    progresso = projeto_assessment.get_progresso_percentual()
    if progresso < 100:
        return jsonify({
            'success': False, 
            'message': f'Para finalizar, todas as perguntas devem ser respondidas. Progresso atual: {progresso:.1f}%'
        }), 400
    
    # Finalizar o assessment
    try:
        projeto_assessment.finalizar()
        
        # Verificar se o projeto está totalmente finalizado
        projeto = projeto_respondente.projeto
        finalizados, total = projeto.get_assessments_finalizados()
        
        message = f'Assessment finalizado com sucesso! ({finalizados}/{total} assessments finalizados)'
        if projeto.is_totalmente_finalizado():
            message = 'Todos os assessments foram finalizados! Aguarde o envio do relatório.'
        
        return jsonify({
            'success': True, 
            'message': message,
            'redirect': url_for('respondente.dashboard')
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': 'Erro ao finalizar assessment'}), 500

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
        from models.projeto import ProjetoRespondente, ProjetoAssessment
        projeto_respondente = ProjetoRespondente.query.filter_by(
            projeto_id=projeto_id,
            respondente_id=current_user.id,
            ativo=True
        ).first()
        
        if not projeto_respondente:
            return jsonify({'success': False, 'message': 'Acesso negado ao projeto'}), 403
        
        # Verificar se o assessment ainda pode ser editado
        projeto_assessment = ProjetoAssessment.query.filter_by(
            projeto_id=projeto_id
        ).first()
        
        if projeto_assessment and not projeto_assessment.pode_editar():
            return jsonify({'success': False, 'message': 'Este assessment foi finalizado e não pode ser editado'}), 403
        
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

@respondente_bp.route('/logout')
@login_required
def logout():
    """Logout do respondente"""
    logout_user()
    session.pop('user_type', None)
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('respondente.login'))