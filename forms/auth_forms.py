from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class LoginForm(FlaskForm):
    """Formulário de login"""
    email = StringField('Email ou Login', validators=[
        DataRequired(message='Email ou Login é obrigatório')
    ], render_kw={'placeholder': 'Digite seu email ou login'})
    
    senha = PasswordField('Senha', validators=[
        DataRequired(message='Senha é obrigatória')
    ], render_kw={'placeholder': 'Digite sua senha'})
    
    lembrar = BooleanField('Lembrar de mim')
    
    submit = SubmitField('Entrar')

class CadastroForm(FlaskForm):
    """Formulário de cadastro de clientes"""
    nome_empresa = StringField('Nome da Empresa', validators=[
        DataRequired(message='Nome da empresa é obrigatório'),
        Length(min=2, max=200, message='Nome da empresa deve ter entre 2 e 200 caracteres')
    ], render_kw={'placeholder': 'Digite o nome da empresa'})
    
    nome = StringField('Nome do Responsável', validators=[
        DataRequired(message='Nome do responsável é obrigatório'),
        Length(min=2, max=100, message='Nome deve ter entre 2 e 100 caracteres')
    ], render_kw={'placeholder': 'Digite o nome do responsável'})
    
    email = EmailField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Digite um email válido'),
        Length(max=120, message='Email deve ter no máximo 120 caracteres')
    ], render_kw={'placeholder': 'Digite o email'})
    
    senha = PasswordField('Senha', validators=[
        DataRequired(message='Senha é obrigatória'),
        Length(min=6, message='Senha deve ter pelo menos 6 caracteres')
    ], render_kw={'placeholder': 'Digite uma senha'})
    
    confirmar_senha = PasswordField('Confirmar Senha', validators=[
        DataRequired(message='Confirmação de senha é obrigatória'),
        EqualTo('senha', message='As senhas devem ser iguais')
    ], render_kw={'placeholder': 'Digite a senha novamente'})
    
    submit = SubmitField('Criar Conta')

class AlterarSenhaForm(FlaskForm):
    """Formulário para alterar senha"""
    senha_atual = PasswordField('Senha Atual', validators=[
        DataRequired(message='Senha atual é obrigatória')
    ], render_kw={'placeholder': 'Digite sua senha atual'})
    
    nova_senha = PasswordField('Nova Senha', validators=[
        DataRequired(message='Nova senha é obrigatória'),
        Length(min=6, message='Nova senha deve ter pelo menos 6 caracteres')
    ], render_kw={'placeholder': 'Digite a nova senha'})
    
    confirmar_nova_senha = PasswordField('Confirmar Nova Senha', validators=[
        DataRequired(message='Confirmação de nova senha é obrigatória'),
        EqualTo('nova_senha', message='As senhas devem ser iguais')
    ], render_kw={'placeholder': 'Digite a nova senha novamente'})
    
    submit = SubmitField('Alterar Senha')
