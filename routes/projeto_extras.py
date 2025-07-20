"""
Funcionalidades extras para projetos: edição de textos IA e liberação para cliente
"""

from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required
from app import db
from utils.auth_utils import admin_required
from forms.avaliador_forms import EditarTextoIAForm, LiberarClienteForm
from models.projeto import Projeto
import logging
import json

def register_projeto_extras_routes(projeto_bp):
    """Registra rotas extras para projetos"""
    
    @projeto_bp.route('/<int:projeto_id>/editar-texto-ia/<tipo>')
    @login_required 
    @admin_required
    def editar_texto_ia(projeto_id, tipo):
        """Página para editar textos gerados por IA"""
        projeto = Projeto.query.get_or_404(projeto_id)
        
        # Verificar se projeto foi liberado para cliente
        if projeto.liberado_cliente:
            flash('Este projeto já foi liberado para o cliente e não pode mais ser editado.', 'warning')
            return redirect(url_for('projeto.estatisticas', projeto_id=projeto_id))
        
        form = EditarTextoIAForm()
        form.tipo_texto.data = tipo
        
        # Carregar texto atual
        if tipo == 'introducao':
            texto_atual = projeto.introducao_ia or ''
            titulo = 'Editar Introdução'
            label = 'Texto da Introdução'
        elif tipo == 'consideracoes':
            # Se é JSON, extrair só o texto
            if projeto.consideracoes_finais_ia:
                try:
                    data = json.loads(projeto.consideracoes_finais_ia)
                    texto_atual = data.get('consideracoes', '')
                except:
                    texto_atual = projeto.consideracoes_finais_ia
            else:
                texto_atual = ''
            titulo = 'Editar Considerações Finais'
            label = 'Texto das Considerações Finais'
        else:
            flash('Tipo de texto inválido.', 'error')
            return redirect(url_for('projeto.estatisticas', projeto_id=projeto_id))
        
        form.texto_ia.data = texto_atual
        form.texto_ia.label.text = label
        
        return render_template('admin/projetos/editar_texto_ia.html',
                             projeto=projeto, form=form, titulo=titulo, tipo=tipo)

    @projeto_bp.route('/<int:projeto_id>/salvar-texto-ia', methods=['POST'])
    @login_required
    @admin_required
    def salvar_texto_ia(projeto_id):
        """Salva texto editado pelo avaliador"""
        projeto = Projeto.query.get_or_404(projeto_id)
        
        # Verificar se projeto foi liberado para cliente
        if projeto.liberado_cliente:
            flash('Este projeto já foi liberado para o cliente e não pode mais ser editado.', 'warning')
            return redirect(url_for('projeto.estatisticas', projeto_id=projeto_id))
        
        form = EditarTextoIAForm()
        
        if form.validate_on_submit():
            tipo = form.tipo_texto.data
            texto = form.texto_ia.data
            
            try:
                if tipo == 'introducao':
                    projeto.introducao_ia = texto
                    flash('Introdução atualizada com sucesso!', 'success')
                elif tipo == 'consideracoes':
                    projeto.consideracoes_finais_ia = texto
                    flash('Considerações finais atualizadas com sucesso!', 'success')
                
                db.session.commit()
                
            except Exception as e:
                db.session.rollback()
                logging.error(f"Erro ao salvar texto IA: {e}")
                flash('Erro ao salvar texto. Tente novamente.', 'danger')
        
        return redirect(url_for('projeto.estatisticas', projeto_id=projeto_id))

    @projeto_bp.route('/<int:projeto_id>/liberar-cliente')
    @login_required
    @admin_required
    def confirmar_liberacao_cliente(projeto_id):
        """Página de confirmação para liberar projeto para cliente"""
        projeto = Projeto.query.get_or_404(projeto_id)
        
        if projeto.liberado_cliente:
            flash('Este projeto já foi liberado para o cliente.', 'info')
            return redirect(url_for('projeto.estatisticas', projeto_id=projeto_id))
        
        form = LiberarClienteForm()
        
        return render_template('admin/projetos/liberar_cliente.html',
                             projeto=projeto, form=form)

    @projeto_bp.route('/<int:projeto_id>/liberar-cliente', methods=['POST'])
    @login_required
    @admin_required
    def liberar_para_cliente(projeto_id):
        """Libera projeto para acesso do cliente"""
        projeto = Projeto.query.get_or_404(projeto_id)
        
        if projeto.liberado_cliente:
            flash('Este projeto já foi liberado para o cliente.', 'info')
            return redirect(url_for('projeto.estatisticas', projeto_id=projeto_id))
        
        form = LiberarClienteForm()
        
        if form.validate_on_submit():
            try:
                projeto.liberado_cliente = True
                db.session.commit()
                flash('Projeto liberado para o cliente com sucesso! O cliente agora pode acessar as estatísticas e gerar relatórios.', 'success')
            except Exception as e:
                db.session.rollback()
                logging.error(f"Erro ao liberar projeto: {e}")
                flash('Erro ao liberar projeto. Tente novamente.', 'danger')
        
        return redirect(url_for('projeto.estatisticas', projeto_id=projeto_id))
    
    @projeto_bp.route('/<int:projeto_id>/gerar-texto-orientacao/<tipo>', methods=['POST'])
    @login_required
    @admin_required
    def gerar_texto_com_orientacao(projeto_id, tipo):
        """Gera ou melhora texto com orientações do usuário usando IA"""
        projeto = Projeto.query.get_or_404(projeto_id)
        
        if projeto.liberado_cliente:
            flash('Este projeto já foi liberado para o cliente e não pode mais ser editado.', 'warning')
            return redirect(url_for('projeto.estatisticas', projeto_id=projeto_id))
        
        orientacoes = request.form.get('orientacoes', '').strip()
        if not orientacoes:
            flash('Por favor, forneça orientações para a IA.', 'warning')
            return redirect(url_for('projeto.estatisticas', projeto_id=projeto_id))
        
        try:
            # Verificar se há texto atual
            if tipo == 'introducao':
                texto_atual = projeto.introducao_ia or ''
            elif tipo == 'consideracoes':
                if projeto.consideracoes_finais_ia:
                    try:
                        data = json.loads(projeto.consideracoes_finais_ia)
                        texto_atual = data.get('consideracoes', '')
                    except:
                        texto_atual = projeto.consideracoes_finais_ia
                else:
                    texto_atual = ''
            else:
                flash('Tipo de texto inválido.', 'error')
                return redirect(url_for('projeto.estatisticas', projeto_id=projeto_id))
            
            # Se não há texto atual, usar orientações para gerar novo
            if not texto_atual:
                if tipo == 'introducao':
                    from utils.openai_utils import gerar_introducao_ia
                    resultado = gerar_introducao_ia(projeto)
                    if resultado.get('erro'):
                        flash(f'Erro ao gerar introdução: {resultado["erro"]}', 'danger')
                        return redirect(url_for('projeto.estatisticas', projeto_id=projeto_id))
                    projeto.introducao_ia = resultado['introducao']
                elif tipo == 'consideracoes':
                    from utils.openai_utils import gerar_consideracoes_finais_ia
                    resultado = gerar_consideracoes_finais_ia(projeto)
                    if resultado.get('erro'):
                        flash(f'Erro ao gerar considerações: {resultado["erro"]}', 'danger')
                        return redirect(url_for('projeto.estatisticas', projeto_id=projeto_id))
                    projeto.consideracoes_finais_ia = resultado['consideracoes']
                
                db.session.commit()
                flash(f'{"Introdução" if tipo == "introducao" else "Considerações finais"} gerada com suas orientações!', 'success')
            else:
                # Melhorar texto existente com orientações
                from utils.openai_utils import melhorar_texto_com_orientacao
                resultado = melhorar_texto_com_orientacao(texto_atual, orientacoes, tipo)
                
                if resultado.get('erro'):
                    flash(f'Erro ao melhorar texto: {resultado["erro"]}', 'danger')
                else:
                    # Salvar texto melhorado
                    if tipo == 'introducao':
                        projeto.introducao_ia = resultado['texto_melhorado']
                    elif tipo == 'consideracoes':
                        projeto.consideracoes_finais_ia = resultado['texto_melhorado']
                    
                    db.session.commit()
                    flash(f'{"Introdução" if tipo == "introducao" else "Considerações finais"} melhorada com suas orientações!', 'success')
            
        except Exception as e:
            logging.error(f"Erro ao gerar texto com orientação: {e}")
            flash(f'Erro ao processar solicitação: {str(e)}', 'danger')
        
        return redirect(url_for('projeto.estatisticas', projeto_id=projeto_id))