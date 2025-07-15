from datetime import datetime
from app import db

class Configuracao(db.Model):
    """Modelo para configurações simplificadas do sistema"""
    
    __tablename__ = 'configuracoes'
    
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(100), unique=True, nullable=False, comment='Chave da configuração')
    valor = db.Column(db.Text, comment='Valor da configuração')
    descricao = db.Column(db.String(500), comment='Descrição da configuração')
    tipo = db.Column(db.String(50), default='string', comment='Tipo do valor (string, color)')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, comment='Data de criação')
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='Data da última atualização')
    
    def __repr__(self):
        return f'<Configuracao {self.chave}={self.valor}>'
    
    @staticmethod
    def get_valor(chave, default=None):
        """Obter valor de uma configuração"""
        config = Configuracao.query.filter_by(chave=chave).first()
        return config.valor if config else default
    
    @staticmethod
    def set_valor(chave, valor, descricao=None, tipo='string'):
        """Definir valor de uma configuração"""
        try:
            config = Configuracao.query.filter_by(chave=chave).first()
            
            if config:
                config.valor = valor
                config.data_atualizacao = datetime.utcnow()
            else:
                config = Configuracao(
                    chave=chave,
                    valor=valor,
                    descricao=descricao,
                    tipo=tipo
                )
                db.session.add(config)
            
            db.session.commit()
            return config
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_cores_sistema():
        """Obter cores do sistema configuradas"""
        try:
            cores = {
                'primaria': Configuracao.get_valor('cor_primaria', '#1a73e8'),
                'secundaria': Configuracao.get_valor('cor_secundaria', '#445063'),
                'fundo': Configuracao.get_valor('cor_fundo', '#ffffff'),
                'texto': Configuracao.get_valor('cor_texto', '#212529')
            }
            return cores
        except Exception:
            # Retornar cores padrão em caso de erro
            return {
                'primaria': '#1a73e8',
                'secundaria': '#445063', 
                'fundo': '#ffffff',
                'texto': '#212529'
            }
    
    @staticmethod
    def get_escala_pontuacao():
        """Obter configurações da escala de pontuação (0-5)"""
        try:
            escala = {}
            cores_padrao = ['#dc3545', '#fd7e14', '#ffc107', '#20c997', '#0dcaf0', '#198754']
            nomes_padrao = ['Inexistente', 'Inicial', 'Básico', 'Intermediário', 'Avançado', 'Otimizado']
            
            for i in range(6):
                escala[i] = {
                    'nome': Configuracao.get_valor(f'escala_{i}_nome', nomes_padrao[i]),
                    'cor': Configuracao.get_valor(f'escala_{i}_cor', cores_padrao[i])
                }
            return escala
        except Exception:
            # Retornar escala padrão em caso de erro
            escala = {}
            cores_padrao = ['#dc3545', '#fd7e14', '#ffc107', '#20c997', '#0dcaf0', '#198754']
            nomes_padrao = ['Inexistente', 'Inicial', 'Básico', 'Intermediário', 'Avançado', 'Otimizado']
            
            for i in range(6):
                escala[i] = {
                    'nome': nomes_padrao[i],
                    'cor': cores_padrao[i]
                }
            return escala
    
    @staticmethod
    def inicializar_configuracoes_padrao():
        """Inicializar configurações padrão do sistema"""
        import logging
        
        try:
            # Verificar se já existem configurações
            count = db.session.query(Configuracao).count()
            if count > 0:
                return
            
            configuracoes_padrao = [
                # Cores básicas do sistema
                ('cor_primaria', '#1a73e8', 'Cor primária do sistema', 'color'),
                ('cor_secundaria', '#445063', 'Cor secundária do sistema', 'color'),
                ('cor_fundo', '#ffffff', 'Cor de fundo', 'color'),
                ('cor_texto', '#212529', 'Cor do texto', 'color'),
                
                # Escala de pontuação (0-5) - Nomes
                ('escala_0_nome', 'Inexistente', 'Nome para pontuação 0', 'string'),
                ('escala_1_nome', 'Inicial', 'Nome para pontuação 1', 'string'),
                ('escala_2_nome', 'Básico', 'Nome para pontuação 2', 'string'),
                ('escala_3_nome', 'Intermediário', 'Nome para pontuação 3', 'string'),
                ('escala_4_nome', 'Avançado', 'Nome para pontuação 4', 'string'),
                ('escala_5_nome', 'Otimizado', 'Nome para pontuação 5', 'string'),
                
                # Escala de pontuação (0-5) - Cores
                ('escala_0_cor', '#dc3545', 'Cor para pontuação 0', 'color'),
                ('escala_1_cor', '#fd7e14', 'Cor para pontuação 1', 'color'),
                ('escala_2_cor', '#ffc107', 'Cor para pontuação 2', 'color'),
                ('escala_3_cor', '#20c997', 'Cor para pontuação 3', 'color'),
                ('escala_4_cor', '#0dcaf0', 'Cor para pontuação 4', 'color'),
                ('escala_5_cor', '#198754', 'Cor para pontuação 5', 'color'),
            ]
            
            for chave, valor, descricao, tipo in configuracoes_padrao:
                config = Configuracao(
                    chave=chave,
                    valor=valor,
                    descricao=descricao,
                    tipo=tipo
                )
                db.session.add(config)
            
            db.session.commit()
            logging.info("Configurações padrão inicializadas")
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Erro ao inicializar configurações: {e}")
    
    @staticmethod
    def get_cores_sistema():
        """Retorna as cores configuradas do sistema"""
        return {
            'primaria': Configuracao.get_valor('cor_primaria', '#1a73e8'),
            'secundaria': Configuracao.get_valor('cor_secundaria', '#445063'),
            'fundo': Configuracao.get_valor('cor_fundo', '#ffffff'),
            'texto': Configuracao.get_valor('cor_texto', '#212529')
        }
    
    @staticmethod
    def get_escala_pontuacao():
        """Retorna a configuração da escala de pontuação"""
        escala = {}
        for i in range(6):  # 0 a 5
            escala[i] = {
                'nome': Configuracao.get_valor(f'escala_{i}_nome', f'Nível {i}'),
                'cor': Configuracao.get_valor(f'escala_{i}_cor', '#6c757d')
            }
        return escala