"""

.. topic:: **Usuários (formulários)**

   Os formulários do módulo *Users* recebem dados informados pelo usuário para seu registro
   inicial, para entrar no sistema (login), para atualização de registro, bem como os dados
   para atualização de senha.

   Para o tratamento de usuários, foram definidos 5 formulários:

   * LoginForm: utilizado para entrar (login) no sistema.
   * RegistrationForm: utilizado para o registro de um novo usuário.
   * UpdateUserForm: utilizado para que um usuário possa atualizar seus dados.
   * EmailForm: utilizado para um usuário informar seu e-mail quando precisar trocar sua senha.
   * PasswordForm: utilizado quando o usuário eferuar a troca de senha.
   * LogForm: para que o usuário informe o intervalo de datas para resgatar registros do log
   * VerForm: para o registro de atualização no sistema.
   * RelForm: datas para geração de relatório de atividades.


**Campos definidos em cada formulário de *Users*:**

"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo
from wtforms import ValidationError
from flask_wtf.file import FileField, FileAllowed
from flask import flash

from flask_login import current_user
from project import db
from project.models import User, Coords

class LoginForm(FlaskForm):

    email    = StringField('E-mail: ', validators=[DataRequired(message="Informe seu e-mail registrado!"),Email()])
    password = PasswordField('Senha: ', validators=[DataRequired(message="Informe sua senha!")])
    submit   = SubmitField('Entrar')

class RegistrationForm(FlaskForm):

    #coords = db.session.query(Coords.sigla)\
    #                  .order_by(Coords.sigla).all()
    #lista_coords = [(c[0],c[0]) for c in coords]
    #lista_coords.insert(0,('',''))

    email        = StringField('E-mail: ', validators=[DataRequired(message="Informe seu e-mail!"),Email()])
    username     = StringField('Usuário: ', validators=[DataRequired(message="Informe um nome de usuário!")])
    password     = PasswordField('Senha: ', validators=[DataRequired(message="Informe uma senha!"),EqualTo('pass_confirm',message='Senhas devem ser iguais!')])
    pass_confirm = PasswordField('Confirmar Senha: ', validators=[DataRequired(message="Confirme a senha!")])
    coord        = StringField('Coordenação:',validators=[DataRequired(message="Informe a Coordenação!")])
    #coord        = SelectField('Coordenação:',choices= lista_coords, validators=[DataRequired(message="Escolha uma Coordenção!")])
    despacha     = BooleanField('Você é o coordenador, chefe de serviço ou o seu substituto?')
    despacha2    = BooleanField('Você é o coordenador-geral ou o seu substituto?')
    submit       = SubmitField('Registrar-se')

    def check_email(self,field):
        if User.query.filter_by(email=field.data).first():
            flash('Este e-mail já foi registrado!','erro')
            raise ValidationError('Este e-mail já foi registrado!')

    def check_username(self,field):
        if User.query.filter_by(username=field.data).first():
            flash('Este nome de usuário já foi registrado! Por favor, escolha outro.','erro')
            raise ValidationError('Este nome de usuário já foi registrado!')


class UpdateUserForm(FlaskForm):

    email    = StringField('E-mail: ', validators=[DataRequired(message="Informe um e-mail!"),Email()])
    username = StringField('Usuário: ', validators=[DataRequired(message="Informe um nome de usuário!")])
    submit   = SubmitField('Atualizar')

    def validate_email(self,field):
        if User.query.filter_by(email=field.data).first() and field.data != current_user.email:
            flash('Este e-mail já foi registrado!','erro')
            raise ValidationError('Este e-mail já foi registrado!')

    def validate_username(self,field):
        if User.query.filter_by(username=field.data).first() and field.data != current_user.username:
            flash('Este nome de usuário já foi registrado! Por favor, escolha outro.','erro')
            raise ValidationError('Este nome de usuário já foi registrado!')

class EmailForm(FlaskForm):

    email    = StringField('E-mail: ', validators=[DataRequired(message="Informe seu e-mail!"),Email()])
    submit   = SubmitField('Enviar')

class PasswordForm(FlaskForm):

    password     = PasswordField('Senha: ', validators=[DataRequired(message="Forneça uma senha!"),EqualTo('pass_confirm',message='Senhas devem ser iguais!')])
    pass_confirm = PasswordField('Confirmar senha: ', validators=[DataRequired(message="Confirme a senha!")])
    submit       = SubmitField('Enviar')

class AdminForm(FlaskForm):

    coords = db.session.query(Coords.sigla)\
                      .order_by(Coords.sigla).all()
    lista_coords = [(c[0],c[0]) for c in coords]
    lista_coords.insert(0,('',''))

    coord        = SelectField('Coordenação:',choices= lista_coords, validators=[DataRequired(message="Escolha uma Coordenção!")])
    despacha     = BooleanField('É coordenador(a), chefe de serviço ou substituto(a)?')
    despacha2    = BooleanField('É coordenador(a)-geral ou substituto(a)?')
    role         = SelectField('Role: ',choices=[('user','user'),('admin','admin')] ,validators=[DataRequired(message="Informe o papel do usuário!")])
    cargo_func   = StringField('Cargo e Função: ')
    ativo        = BooleanField('Usuário está ativo?')
    submit       = SubmitField('Atualizar')

class LogForm(FlaskForm):

    data_ini = DateField('Data Inicial: ', format='%d/%m/%Y')
    data_fim = DateField('Data Final: ', format='%d/%m/%Y')
    log_part = StringField('Obs. usuário: ')
    submit   = SubmitField('Procurar')

class LogFormMan(FlaskForm):

    entrada_log = TextAreaField('Entrada no Diário: ')
    submit   = SubmitField('Registrar')

class VerForm(FlaskForm):

    ver          = StringField('Versão: ')
    nome_sistema = StringField('Nome do sistema: ')
    descritivo   = TextAreaField('Descritivo: ')
    submit       = SubmitField('Registrar')

class RelForm(FlaskForm):

    data_ini = DateField('Data Inicial: ', format='%d/%m/%Y')
    data_fim = DateField('Data Final: ', format='%d/%m/%Y')
    submit   = SubmitField('Gerar Relatório')
