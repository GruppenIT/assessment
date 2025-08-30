"""
Modelo para autenticação de dois fatores (2FA)
"""

from app import db
from datetime import datetime
import pyotp
import qrcode
import io
import base64

class TwoFactor(db.Model):
    __tablename__ = 'two_factor'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    respondente_id = db.Column(db.Integer, db.ForeignKey('respondentes.id'), nullable=True)
    secret_key = db.Column(db.String(32), nullable=False)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    backup_codes = db.Column(db.Text)  # Códigos de backup separados por vírgula
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    activated_at = db.Column(db.DateTime)
    last_used = db.Column(db.DateTime)
    
    # Relacionamentos
    usuario = db.relationship('Usuario', backref='two_factor_config', foreign_keys=[usuario_id])
    respondente = db.relationship('Respondente', backref='two_factor_config', foreign_keys=[respondente_id])
    
    def __init__(self, usuario_id=None, respondente_id=None):
        self.usuario_id = usuario_id
        self.respondente_id = respondente_id
        self.secret_key = pyotp.random_base32()
        self.backup_codes = self.generate_backup_codes()
    
    def generate_backup_codes(self):
        """Gera códigos de backup únicos"""
        import secrets
        codes = []
        for _ in range(10):
            code = ''.join([str(secrets.randbelow(10)) for _ in range(8)])
            codes.append(code)
        return ','.join(codes)
    
    def get_backup_codes_list(self):
        """Retorna códigos de backup como lista"""
        if self.backup_codes:
            return self.backup_codes.split(',')
        return []
    
    def use_backup_code(self, code):
        """Usa um código de backup (remove da lista)"""
        codes = self.get_backup_codes_list()
        if code in codes:
            codes.remove(code)
            self.backup_codes = ','.join(codes)
            self.last_used = datetime.utcnow()
            return True
        return False
    
    def get_user_identifier(self):
        """Retorna identificação do usuário (email)"""
        if self.usuario:
            return self.usuario.email
        elif self.respondente:
            return self.respondente.email
        return "usuario@sistema.com"
    
    def get_user_name(self):
        """Retorna nome do usuário"""
        if self.usuario:
            return self.usuario.nome
        elif self.respondente:
            return self.respondente.nome
        return "Usuário"
    
    def get_totp_uri(self):
        """Gera URI para QR Code do TOTP"""
        issuer_name = "Sistema de Avaliações"
        account_name = f"{self.get_user_identifier()} ({self.get_user_name()})"
        
        totp = pyotp.TOTP(self.secret_key)
        return totp.provisioning_uri(
            name=account_name,
            issuer_name=issuer_name
        )
    
    def get_qr_code_data_uri(self):
        """Gera QR Code como Data URI para exibição no HTML"""
        uri = self.get_totp_uri()
        
        # Criar QR Code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        
        # Gerar imagem
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Converter para base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def verify_token(self, token):
        """Verifica token TOTP"""
        totp = pyotp.TOTP(self.secret_key)
        
        # Verificar token com janela expandida para compensar diferenças de tempo
        # valid_window=1 permite tokens do período anterior e próximo (3 períodos total)
        if totp.verify(token, valid_window=1):
            self.last_used = datetime.utcnow()
            return True
        
        return False
    
    def activate(self):
        """Ativa 2FA após primeira verificação bem-sucedida"""
        self.is_active = True
        self.activated_at = datetime.utcnow()
    
    def reset(self):
        """Reseta configuração 2FA (gera nova chave secreta)"""
        self.secret_key = pyotp.random_base32()
        self.backup_codes = self.generate_backup_codes()
        self.is_active = False
        self.activated_at = None
        self.last_used = None
    
    @staticmethod
    def get_or_create_for_user(usuario_id=None, respondente_id=None):
        """Busca ou cria configuração 2FA para usuário"""
        if usuario_id:
            config = TwoFactor.query.filter_by(usuario_id=usuario_id).first()
            if not config:
                config = TwoFactor(usuario_id=usuario_id)
                db.session.add(config)
                db.session.commit()
        elif respondente_id:
            config = TwoFactor.query.filter_by(respondente_id=respondente_id).first()
            if not config:
                config = TwoFactor(respondente_id=respondente_id)
                db.session.add(config)
                db.session.commit()
        else:
            return None
            
        return config
    
    @staticmethod
    def is_enabled_for_user(usuario_id=None, respondente_id=None):
        """Verifica se 2FA está ativo para o usuário"""
        if usuario_id:
            config = TwoFactor.query.filter_by(usuario_id=usuario_id, is_active=True).first()
        elif respondente_id:
            config = TwoFactor.query.filter_by(respondente_id=respondente_id, is_active=True).first()
        else:
            return False
            
        return config is not None