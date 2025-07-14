from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_required, current_user
from models.usuario import Usuario
from models.cliente import Cliente
from models.respondente import Respondente
from models.dominio import Dominio
from models.pergunta import Pergunta
from models.resposta import Resposta
from models.tipo_assessment import TipoAssessment
from utils.auth_utils import admin_required
from utils.pdf_utils import gerar_relatorio_pdf
from app import db
from datetime import datetime

relatorio_bp = Blueprint('relatorio', __name__, url_prefix='/relatorio')

@relatorio_bp.route('/gerar_pdf/<int:cliente_id>/<int:tipo_assessment_id>')
@login_required
@admin_required
def gerar_pdf(cliente_id, tipo_assessment_id):
    """Gera relatório PDF para um cliente específico"""
    try:
        print(f"DEBUG: Iniciando geração de PDF para cliente {cliente_id}, tipo {tipo_assessment_id}")
        cliente = Cliente.query.get_or_404(cliente_id)
        tipo_assessment = TipoAssessment.query.get_or_404(tipo_assessment_id)
        print(f"DEBUG: Cliente encontrado: {cliente.nome}")
        print(f"DEBUG: Tipo assessment encontrado: {tipo_assessment.nome}")
        
        # Verificar se o cliente tem acesso a este tipo de assessment
        if not cliente.tem_acesso_assessment(tipo_assessment_id):
            flash('Cliente não tem acesso a este tipo de assessment.', 'danger')
            return redirect(url_for('admin.assessments'))
        
        # Buscar dados para o relatório
        dominios = tipo_assessment.get_dominios_ativos()
        respondentes = Respondente.query.filter_by(cliente_id=cliente_id, ativo=True).all()
        
        # Calcular estatísticas por domínio
        estatisticas_dominios = []
        for dominio in dominios:
            perguntas = dominio.get_perguntas_ativas()
            total_perguntas = len(perguntas)
            
            if total_perguntas == 0:
                continue
                
            # Buscar todas as respostas para este domínio
            respostas = []
            for pergunta in perguntas:
                respostas_pergunta = Resposta.query.filter_by(pergunta_id=pergunta.id).join(Respondente).filter(
                    Respondente.cliente_id == cliente_id,
                    Respondente.ativo == True
                ).all()
                respostas.extend(respostas_pergunta)
            
            # Calcular estatísticas
            if respostas:
                media_dominio = sum(r.nota for r in respostas) / len(respostas)
                respondidas = len(respostas)
                percentual_completude = (respondidas / (total_perguntas * len(respondentes))) * 100 if respondentes else 0
            else:
                media_dominio = 0
                respondidas = 0
                percentual_completude = 0
            
            estatisticas_dominios.append({
                'dominio': dominio,
                'media': round(media_dominio, 2),
                'respondidas': respondidas,
                'total_possivel': total_perguntas * len(respondentes),
                'percentual_completude': round(percentual_completude, 1)
            })
        
        # Calcular estatísticas gerais
        todas_respostas = Resposta.query.join(Pergunta).join(Dominio).join(Respondente).filter(
            Dominio.tipo_assessment_id == tipo_assessment_id,
            Respondente.cliente_id == cliente_id,
            Respondente.ativo == True
        ).all()
        
        if todas_respostas:
            media_geral = sum(r.nota for r in todas_respostas) / len(todas_respostas)
            nivel_maturidade = calcular_nivel_maturidade(media_geral)
        else:
            media_geral = 0
            nivel_maturidade = "Não avaliado"
        
        # Dados para o relatório
        dados_relatorio = {
            'cliente': cliente,
            'tipo_assessment': tipo_assessment,
            'respondentes': respondentes,
            'estatisticas_dominios': estatisticas_dominios,
            'media_geral': round(media_geral, 2),
            'nivel_maturidade': nivel_maturidade,
            'total_respondentes': len(respondentes),
            'data_geracao': datetime.now(),
            'total_respostas': len(todas_respostas)
        }
        
        # Gerar PDF
        print("DEBUG: Iniciando geração do PDF...")
        pdf_content = gerar_relatorio_pdf(dados_relatorio)
        print(f"DEBUG: PDF gerado com sucesso! Tamanho: {len(pdf_content)} bytes")
        
        # Criar resposta com o PDF
        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="Assessment_{cliente.nome}_{tipo_assessment.nome}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        
        print("DEBUG: Resposta PDF criada com sucesso")
        return response
        
    except Exception as e:
        print(f"Erro ao gerar PDF: {str(e)}")
        flash('Erro ao gerar relatório PDF.', 'danger')
        return redirect(url_for('admin.assessments'))

def calcular_nivel_maturidade(media):
    """Calcula o nível de maturidade baseado na média"""
    if media >= 4.5:
        return "Otimizado (Nível 5)"
    elif media >= 3.5:
        return "Avançado (Nível 4)"
    elif media >= 2.5:
        return "Intermediário (Nível 3)"
    elif media >= 1.5:
        return "Básico (Nível 2)"
    elif media >= 0.5:
        return "Inicial (Nível 1)"
    else:
        return "Inexistente (Nível 0)"

@relatorio_bp.route('/visualizar/<int:cliente_id>/<int:tipo_assessment_id>')
@login_required
@admin_required
def visualizar(cliente_id, tipo_assessment_id):
    """Visualiza o relatório online"""
    try:
        cliente = Cliente.query.get_or_404(cliente_id)
        tipo_assessment = TipoAssessment.query.get_or_404(tipo_assessment_id)
        
        # Verificar se o cliente tem acesso a este tipo de assessment
        if not cliente.tem_acesso_assessment(tipo_assessment_id):
            flash('Cliente não tem acesso a este tipo de assessment.', 'danger')
            return redirect(url_for('admin.assessments'))
        
        # Buscar dados para o relatório (mesmo código do PDF)
        dominios = tipo_assessment.get_dominios_ativos()
        respondentes = Respondente.query.filter_by(cliente_id=cliente_id, ativo=True).all()
        
        # Calcular estatísticas por domínio
        estatisticas_dominios = []
        for dominio in dominios:
            perguntas = dominio.get_perguntas_ativas()
            total_perguntas = len(perguntas)
            
            if total_perguntas == 0:
                continue
                
            # Buscar todas as respostas para este domínio
            respostas = []
            for pergunta in perguntas:
                respostas_pergunta = Resposta.query.filter_by(pergunta_id=pergunta.id).join(Respondente).filter(
                    Respondente.cliente_id == cliente_id,
                    Respondente.ativo == True
                ).all()
                respostas.extend(respostas_pergunta)
            
            # Calcular estatísticas
            if respostas:
                media_dominio = sum(r.nota for r in respostas) / len(respostas)
                respondidas = len(respostas)
                percentual_completude = (respondidas / (total_perguntas * len(respondentes))) * 100 if respondentes else 0
            else:
                media_dominio = 0
                respondidas = 0
                percentual_completude = 0
            
            estatisticas_dominios.append({
                'dominio': dominio,
                'media': round(media_dominio, 2),
                'respondidas': respondidas,
                'total_possivel': total_perguntas * len(respondentes),
                'percentual_completude': round(percentual_completude, 1)
            })
        
        # Calcular estatísticas gerais
        todas_respostas = Resposta.query.join(Pergunta).join(Dominio).join(Respondente).filter(
            Dominio.tipo_assessment_id == tipo_assessment_id,
            Respondente.cliente_id == cliente_id,
            Respondente.ativo == True
        ).all()
        
        if todas_respostas:
            media_geral = sum(r.nota for r in todas_respostas) / len(todas_respostas)
            nivel_maturidade = calcular_nivel_maturidade(media_geral)
        else:
            media_geral = 0
            nivel_maturidade = "Não avaliado"
        
        # Dados para o template
        dados_relatorio = {
            'cliente': cliente,
            'tipo_assessment': tipo_assessment,
            'respondentes': respondentes,
            'estatisticas_dominios': estatisticas_dominios,
            'media_geral': round(media_geral, 2),
            'nivel_maturidade': nivel_maturidade,
            'total_respondentes': len(respondentes),
            'data_geracao': datetime.now(),
            'total_respostas': len(todas_respostas)
        }
        
        return render_template('relatorio/visualizar.html', dados=dados_relatorio)
        
    except Exception as e:
        print(f"Erro ao visualizar relatório: {str(e)}")
        flash('Erro ao visualizar relatório.', 'danger')
        return redirect(url_for('admin.assessments'))