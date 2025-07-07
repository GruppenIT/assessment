from app import db
from datetime import datetime

class Logo(db.Model):
    """Modelo para armazenar o logo da empresa"""
    
    __tablename__ = 'logos'
    
    id = db.Column(db.Integer, primary_key=True)
    caminho_arquivo = db.Column(db.String(255), nullable=False, comment='Caminho do arquivo do logo')
    nome_original = db.Column(db.String(255), comment='Nome original do arquivo')
    tamanho = db.Column(db.Integer, comment='Tamanho do arquivo em bytes')
    tipo_mime = db.Column(db.String(50), comment='Tipo MIME do arquivo')
    data_upload = db.Column(db.DateTime, default=datetime.utcnow, comment='Data do upload')
    ativo = db.Column(db.Boolean, default=True, comment='Se o logo está ativo')
    
    def __repr__(self):
        return f'<Logo {self.caminho_arquivo}>'
    
    def to_dict(self):
        """Converte o logo para dicionário"""
        return {
            'id': self.id,
            'caminho_arquivo': self.caminho_arquivo,
            'nome_original': self.nome_original,
            'tamanho': self.tamanho,
            'tipo_mime': self.tipo_mime,
            'data_upload': self.data_upload.isoformat() if self.data_upload else None,
            'ativo': self.ativo
        }
    
    @staticmethod
    def get_logo_ativo():
        """Retorna o logo ativo atual"""
        return Logo.query.filter_by(ativo=True).first()
    
    def desativar_outros(self):
        """Desativa todos os outros logos"""
        Logo.query.filter(Logo.id != self.id).update({'ativo': False})
        db.session.commit()
