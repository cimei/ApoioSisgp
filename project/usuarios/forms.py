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

**Campos definidos em cada formulário de *Users*:**

"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField,\
                    TextAreaField, IntegerField
from wtforms.fields.html5 import DateField

from wtforms.validators import DataRequired, Email, EqualTo
from wtforms import ValidationError
from flask import flash

from flask_login import current_user
from project import db
from project.models import users

class LoginForm(FlaskForm):

    email    = StringField('E-mail: ', validators=[DataRequired(message="Informe seu e-mail registrado!"),Email()])
    password = PasswordField('Senha: ', validators=[DataRequired(message="Informe sua senha!")])
    submit   = SubmitField('Entrar')

class RegistrationForm(FlaskForm):

    email        = StringField('E-mail: ', validators=[DataRequired(message="Informe seu e-mail!"),Email()])
    username     = StringField('Nome do usuário: ', validators=[DataRequired(message="Informe um nome de usuário!")])
    password     = PasswordField('Senha: ', validators=[DataRequired(message="Informe uma senha!"),EqualTo('pass_confirm',message='Senhas devem ser iguais!')])
    pass_confirm = PasswordField('Confirmar Senha: ', validators=[DataRequired(message="Confirme a senha!")])
    submit       = SubmitField('Registrar-se')

    def check_email(self,field):
        if users.query.filter_by(userEmail=field.data).first():
            flash('Este e-mail já foi registrado!','erro')
            raise ValidationError('Este e-mail já foi registrado!')

    def check_username(self,field):
        if users.query.filter_by(userNome=field.data).first():
            flash('Este nome de usuário já foi registrado! Por favor, escolha outro.','erro')
            raise ValidationError('Este nome de usuário já foi registrado!')


class UpdateUserForm(FlaskForm):

    email    = StringField('E-mail: ', validators=[DataRequired(message="Informe um e-mail!"),Email()])
    username = StringField('Usuário: ', validators=[DataRequired(message="Informe um nome de usuário!")])
    submit   = SubmitField('Atualizar')

    def validate_email(self,field):
        if users.query.filter_by(userEmail=field.data).first() and field.data != current_user.userEmail:
            flash('Este e-mail já foi registrado!','erro')
            raise ValidationError('Este e-mail já foi registrado!')

    def validate_username(self,field):
        if users.query.filter_by(userNome=field.data).first() and field.data != current_user.userNome:
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

    ativo        = BooleanField('Usuário está ativo?')

    submit       = SubmitField('Atualizar')

class LogForm(FlaskForm):

    data_ini = DateField('Data Inicial: ', format='%Y-%m-%d')
    data_fim = DateField('Data Final: ', format='%Y-%m-%d')
    submit   = SubmitField('Procurar')

class DefGestor(FlaskForm):

    gestor = SelectField('Gestor do SISGP:',coerce=int)
    
    submit = SubmitField('Submeter')