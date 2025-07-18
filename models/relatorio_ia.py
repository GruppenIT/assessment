"""
Modelo para armazenar relatórios gerados por IA
"""

from app import db
from datetime import datetime
import json

class RelatorioIA(db.Model):
    """Modelo para armazenar relatórios gerados por IA"""
    
    __tablename__ = 'relatorios_ia'
    
    id = db.Column(db.Integer, primary_key=True)
    projeto_id = db.Column(db.Integer, db.ForeignKey('projetos.id'), nullable=False)
    introducao = db.Column(db.Text)
    analises_dominios = db.Column(db.Text)  # JSON string
    consideracoes_finais = db.Column(db.Text)
    assistant_name = db.Column(db.String(100))
    data_geracao = db.Column(db.DateTime, default=datetime.utcnow)
    versao = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='gerado')  # gerado, erro, processando
    
    # Relacionamentos
    projeto = db.relationship('Projeto', backref='relatorios_ia')
    
    def __repr__(self):
        return f'<RelatorioIA {self.id} - Projeto {self.projeto_id}>'
    
    def get_analises_dominios(self):
        """Retorna análises dos domínios como objeto Python"""
        if self.analises_dominios:
            try:
                return json.loads(self.analises_dominios)
            except:
                return []
        return []
    
    def set_analises_dominios(self, analises):
        """Define análises dos domínios a partir de objeto Python"""
        self.analises_dominios = json.dumps(analises, ensure_ascii=False)
    
    @staticmethod
    def get_by_projeto(projeto_id):
        """Retorna o relatório mais recente de um projeto"""
        return RelatorioIA.query.filter_by(projeto_id=projeto_id).order_by(
            RelatorioIA.data_geracao.desc()
        ).first()
    
    @staticmethod
    def criar_relatorio(projeto_id, dados_relatorio):
        """Cria um novo relatório IA"""
        relatorio = RelatorioIA(
            projeto_id=projeto_id,
            introducao=dados_relatorio.get('introducao'),
            consideracoes_finais=dados_relatorio.get('consideracoes_finais'),
            assistant_name=dados_relatorio.get('assistant_name')
        )
        
        # Definir análises dos domínios
        relatorio.set_analises_dominios(dados_relatorio.get('analises_dominios', []))
        
        # Verificar se houve erro
        if dados_relatorio.get('erro'):
            relatorio.status = 'erro'
            relatorio.introducao = dados_relatorio['erro']
        
        db.session.add(relatorio)
        db.session.commit()
        
        return relatorio
    
    def to_dict(self):
        """Converte o relatório para dicionário"""
        return {
            'id': self.id,
            'projeto_id': self.projeto_id,
            'introducao': self.introducao,
            'analises_dominios': self.get_analises_dominios(),
            'consideracoes_finais': self.consideracoes_finais,
            'assistant_name': self.assistant_name,
            'data_geracao': self.data_geracao.isoformat() if self.data_geracao else None,
            'versao': self.versao,
            'status': self.status
        }