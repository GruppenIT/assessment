"""
Modelo para parâmetros do sistema
"""

from app import db
from datetime import datetime
import json
from cryptography.fernet import Fernet
import os
import base64

class ParametroSistema(db.Model):
    __tablename__ = 'parametros_sistema'
    
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.Text)
    valor_criptografado = db.Column(db.Text)  # Para dados sensíveis
    tipo = db.Column(db.String(50), default='string')  # string, json, encrypted
    descricao = db.Column(db.String(255))
    categoria = db.Column(db.String(50))
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get_chave_criptografia():
        """Gera ou recupera a chave de criptografia"""
        chave_env = os.environ.get('CRYPTO_KEY')
        if chave_env:
            return chave_env.encode()
        
        # Usar uma chave fixa para o ambiente (não recomendado para produção)
        # Em produção, deve-se usar uma variável de ambiente
        chave_fixa = "ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg="
        return chave_fixa.encode()
    
    @staticmethod
    def get_valor(chave, valor_padrao=None):
        """Recupera um valor do sistema"""
        import logging
        
        parametro = ParametroSistema.query.filter_by(chave=chave).first()
        if not parametro:
            logging.debug(f"Parâmetro '{chave}' não encontrado no banco")
            return valor_padrao
        
        if parametro.tipo == 'encrypted' and parametro.valor_criptografado:
            try:
                fernet = Fernet(ParametroSistema.get_chave_criptografia())
                valor_descriptografado = fernet.decrypt(parametro.valor_criptografado.encode())
                resultado = valor_descriptografado.decode()
                
                # Log detalhado para debugging OpenAI
                if chave == 'openai_api_key':
                    logging.debug(f"OpenAI API key descriptografada com sucesso. Tamanho: {len(resultado)}")
                    logging.debug(f"OpenAI API key format check: starts_with_sk={resultado.startswith('sk-')}")
                
                return resultado
            except Exception as e:
                logging.error(f"Erro ao descriptografar parâmetro '{chave}': {e}")
                return valor_padrao
        elif parametro.tipo == 'json' and parametro.valor:
            try:
                return json.loads(parametro.valor)
            except Exception as e:
                logging.error(f"Erro ao parsing JSON do parâmetro '{chave}': {e}")
                return valor_padrao
        else:
            return parametro.valor or valor_padrao
    
    @staticmethod
    def set_valor(chave, valor, tipo='string', descricao=None, categoria=None):
        """Define um valor no sistema"""
        parametro = ParametroSistema.query.filter_by(chave=chave).first()
        if not parametro:
            parametro = ParametroSistema(chave=chave)
            db.session.add(parametro)
        
        parametro.tipo = tipo
        parametro.descricao = descricao
        parametro.categoria = categoria
        parametro.data_atualizacao = datetime.utcnow()
        
        if tipo == 'encrypted':
            fernet = Fernet(ParametroSistema.get_chave_criptografia())
            valor_criptografado = fernet.encrypt(valor.encode())
            parametro.valor_criptografado = valor_criptografado.decode()
            parametro.valor = None
        elif tipo == 'json':
            parametro.valor = json.dumps(valor)
            parametro.valor_criptografado = None
        else:
            parametro.valor = valor
            parametro.valor_criptografado = None
        
        db.session.commit()
        return parametro
    
    @staticmethod
    def get_fuso_horario():
        """Recupera o fuso horário configurado"""
        return ParametroSistema.get_valor('fuso_horario', 'America/Sao_Paulo')
    
    @staticmethod
    def get_openai_config():
        """Recupera configurações do OpenAI"""
        api_key = ParametroSistema.get_valor('openai_api_key', '')
        assistant_name = ParametroSistema.get_valor('openai_assistant_name', '')
        
        return {
            'api_key': api_key,
            'assistant_name': assistant_name,
            'api_key_configured': bool(api_key and api_key.strip())
        }
    
    @staticmethod
    def set_openai_config(api_key, assistant_name):
        """Define configurações do OpenAI"""
        if api_key:
            ParametroSistema.set_valor('openai_api_key', api_key, 'encrypted', 
                                     'Chave da API OpenAI', 'integracao')
        if assistant_name:
            ParametroSistema.set_valor('openai_assistant_name', assistant_name, 'string',
                                     'Nome do Assistant GPT', 'integracao')
    
    def get_valor_display(self):
        """Retorna o valor para exibição (ofuscando dados sensíveis)"""
        if self.tipo == 'encrypted' and self.valor_criptografado:
            return '••••••••••••'
        elif self.tipo == 'json' and self.valor:
            try:
                data = json.loads(self.valor)
                return str(data)[:100] + '...' if len(str(data)) > 100 else str(data)
            except:
                return self.valor[:100] + '...' if len(self.valor) > 100 else self.valor
        else:
            return self.valor[:100] + '...' if self.valor and len(self.valor) > 100 else self.valor