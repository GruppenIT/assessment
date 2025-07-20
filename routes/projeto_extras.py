"""
Funcionalidades extras para projetos: edição de textos IA e liberação para cliente
"""

from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required
from app import db
from utils.auth_utils import admin_required
from forms.avaliador_forms import EditarTextoIAForm, LiberarClienteForm
from models.projeto import Projeto
import logging
import json
import openai

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

    @projeto_bp.route('/<int:projeto_id>/melhorar_texto_ia', methods=['POST'])
    @login_required
    @admin_required
    def melhorar_texto_ia(projeto_id):
        """Melhorar texto com IA usando orientações específicas"""
        try:
            projeto = Projeto.query.get_or_404(projeto_id)
            
            # Verificar se projeto não está liberado
            if projeto.liberado_cliente:
                return jsonify({'success': False, 'message': 'Projeto já foi liberado para o cliente e não pode ser modificado.'}), 400
            
            tipo_texto = request.form.get('tipo_texto')
            orientacoes = request.form.get('orientacoes', '').strip()
            
            if not tipo_texto or not orientacoes:
                return jsonify({'success': False, 'message': 'Tipo de texto e orientações são obrigatórios.'}), 400
            
            # Verificar se há OpenAI configurado
            from models.parametro_sistema import ParametroSistema
            openai_key = ParametroSistema.get_valor('openai_api_key')
            if not openai_key:
                return jsonify({'success': False, 'message': 'Chave da OpenAI não configurada. Configure em Parâmetros do Sistema.'}), 400
            
            # Obter texto atual
            if tipo_texto == 'consideracoes':
                texto_atual = projeto.consideracoes_finais_ia
                if not texto_atual:
                    return jsonify({'success': False, 'message': 'Nenhuma consideração final encontrada para melhorar.'}), 400
            elif tipo_texto == 'introducao':
                texto_atual = projeto.introducao_ia
                if not texto_atual:
                    return jsonify({'success': False, 'message': 'Nenhuma introdução encontrada para melhorar.'}), 400
            else:
                return jsonify({'success': False, 'message': 'Tipo de texto inválido.'}), 400
            
            # Preparar prompt para melhoria
            prompt_melhoria = f"""Você é um consultor especialista em segurança da informação que precisa melhorar um texto técnico.

TEXTO ATUAL:
{texto_atual}

ORIENTAÇÕES ESPECÍFICAS PARA MELHORIA:
{orientacoes}

INSTRUÇÕES:
1. Mantenha o mesmo contexto e informações técnicas do texto original
2. Aplique as orientações específicas fornecidas
3. Use linguagem profissional e técnica apropriada
4. Mantenha a estrutura e o tom adequados para um relatório executivo
5. NÃO use formatação markdown - apenas texto puro com quebras de linha
6. Mantenha todas as informações relevantes do texto original
7. Melhore conforme as orientações, mas sem alterar dados ou fatos técnicos

Retorne apenas o texto melhorado, sem explicações adicionais ou formatação markdown."""
            
            # Chamar OpenAI
            import openai
            openai.api_key = openai_key
            
            response = openai.chat.completions.create(
                model="gpt-4o",  # modelo mais recente
                messages=[
                    {"role": "system", "content": "Você é um consultor especialista em segurança da informação, responsável por melhorar textos técnicos de relatórios executivos."},
                    {"role": "user", "content": prompt_melhoria}
                ],
                max_tokens=4000,
                temperature=0.7
            )
            
            texto_melhorado = response.choices[0].message.content
            if texto_melhorado:
                texto_melhorado = texto_melhorado.strip()
            
            # Atualizar o projeto com o texto melhorado
            if tipo_texto == 'consideracoes':
                projeto.consideracoes_finais_ia = texto_melhorado
            elif tipo_texto == 'introducao':
                projeto.introducao_ia = texto_melhorado
            
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': f'Texto melhorado com sucesso!',
                'texto_melhorado': texto_melhorado
            })
            
        except Exception as e:
            logging.error(f"Erro ao melhorar texto: {e}")
            return jsonify({'success': False, 'message': f'Erro ao melhorar texto: {str(e)}'}), 500