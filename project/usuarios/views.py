"""
.. topic:: users (views)

    users são as pessoas que podem acessar o ApoioSisgp.

    O registro é feito por meio da respectiva opção no menu do aplicativo, com o preenchimento dos dados
    básicos do usuário. Este registro precisa ser confirmado com o token enviado pelo sistema, por e-mail,
    ao usúario.

    Para entrar no aplicativo, o usuário se idenfica com seu e-mail e informa sua senha pessoal.

    Para alterar sua senha, seja por motivo de esquecimento, ou simplemente porque quer alterá-la, 
    o procedimento envolve o envio de um e-mail do sistema para seu endereço de e-mail registrado, 
    com o token que abre uma tela para registro de nova senha. Este token tem validade de uma hora.

.. topic:: Ações relacionadas aos usuários:

    * Funções auxiliares:
        * registra_log_auto: Registra principais ações do usuário.
        * send_async_email: Envia e-mail de forma assincrona
        * send_email: Prepara e-mail
        * send_confirmation_email: Dados para e-mail de confirmação
        * send_password_reset_email: Dados para e-mail de troca de senha
    * register: Registro de usuário
    * confirm: Gera novo link de confirmação de e-mail para usuário novo.
    * confirm_email: Trata retorno da confirmação
    * reset: Trata pedido de troca de senha
    * reset_with_token: Realiza troca de senha via token em e-mail
    * troca_senha: Troca a senha em tela
    * login: Entrada de usuário
    * primeiro_user: registro do primeiro usuário de forma direta
    * logout: Saída de usuário
    * view_users: Visão dos usuários
    * update_user: Atualizar dados do usuário
    * log: Log de atividades
        
"""
# views.py na pasta users

from itsdangerous import URLSafeTimedSerializer
from flask import render_template, url_for, flash, redirect, request, Blueprint, abort
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from threading import Thread
from datetime import datetime, date, timedelta, time
from werkzeug.security import generate_password_hash
from sqlalchemy import func
from sqlalchemy.sql import label
from sqlalchemy.orm import aliased
from collections import Counter

from project import db, mail, app
from project.models import users, Log_Auto, catdom, Pessoas

from project.usuarios.forms import RegistrationForm, LoginForm, EmailForm, PasswordForm, AdminForm,\
                                LogForm, TrocaPasswordForm
                                

usuarios = Blueprint('usuarios',__name__)


# função para registrar comits no log
def registra_log_auto(user_id,msg):
    """
    +---------------------------------------------------------------------------------------+
    |Função que registra ação do usuário na tabela log_auto.                                |
    |INPUT: user_id e msg                                                                   |
    +---------------------------------------------------------------------------------------+
    """

    reg_log = Log_Auto(data_hora  = datetime.now(),
                       user_id    = user_id,
                       msg        = msg)

    db.session.add(reg_log)

 
    db.session.commit()
  

    return

# helper function para envio de email em outra thread
def send_async_email(msg):
    """+--------------------------------------------------------------------------------------+
       |Executa o envio de e-mails de forma assíncrona.                                       |
       +--------------------------------------------------------------------------------------+
    """
    with app.app_context():
        mail.send(msg)

# helper function para enviar e-mail
def send_email(subject, recipients, text_body, html_body):
    """+--------------------------------------------------------------------------------------+
       |Envia e-mails.                                                                        |
       +--------------------------------------------------------------------------------------+
    """
    msg = Message(subject, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    thr = Thread(target=send_async_email, args=[msg])
    thr.start()

# helper function que prepara email de conformação de endereço de e-mail
def send_confirmation_email(user_email):
    """+--------------------------------------------------------------------------------------+
       |Preparação dos dados para e-mail de confirmação de usuário                            |
       +--------------------------------------------------------------------------------------+
    """
    confirm_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    confirm_url = url_for(
        'usuarios.confirm_email',
        token=confirm_serializer.dumps(user_email, salt='email-confirmation-salt'),
        _external=True)

    html = render_template(
        'email_confirmation.html',
        confirm_url=confirm_url)

    send_email('Confirme seu endereço de e-mail', [user_email],'', html)

# helper function que prepara email com token para resetar a senha
def send_password_reset_email(user_email):
    """+--------------------------------------------------------------------------------------+
       |Preparação dos dados para e-mail de troca de senha.                                   |
       +--------------------------------------------------------------------------------------+
    """
    password_reset_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    password_reset_url = url_for(
        'usuarios.reset_with_token',
        token = password_reset_serializer.dumps(user_email, salt='password-reset-salt'),
        _external=True)

    html = render_template(
        'email_senha_atualiza.html',
        password_reset_url=password_reset_url)

    send_email('Atualização de senha solicitada', [user_email],'', html)

# registrar

@usuarios.route('/register', methods=['GET','POST'])
def register():
    """+--------------------------------------------------------------------------------------+
       |Efetua o registro de um usuário. Este recebe o aviso para verificar sua caixa de      |
       |e-mails, pois o aplicativo envia uma mensagem sobre a confirmação do registro.        |
       +--------------------------------------------------------------------------------------+
    """
    usuarios_qtd = users.query.count()

    form = RegistrationForm()

    if form.validate_on_submit():

        if form.check_username(form.username) and form.check_email(form.email):

            user = users(userNome                   = form.username.data,
                        userEmail                  = form.email.data,
                        plaintext_password         = form.password.data,
                        email_confirmation_sent_on = datetime.now(),
                        userAtivo                  = False,
                        userEnvia                  = False)

            db.session.add(user)
            db.session.commit()

            last_id = db.session.query(users.id).order_by(users.id.desc()).first()

            registra_log_auto(last_id[0],'Usuário '+ form.username.data +' registrado.')

            send_confirmation_email(user.userEmail)
            
            flash('Usuário '+ form.username.data +' registrado! Verifique sua caixa de e-mail para confirmar o endereço.','sucesso')
            
            return redirect(url_for('core.index'))
        
    if usuarios_qtd == 0:
        flash('Não foram encontrados usuários no sistema. O primeiro será registrado de forma direta.','erro')
        return redirect(url_for('usuarios.primeiro_user'))    

    return render_template('register.html',form=form)

# gera novo link para confirmação de email

@usuarios.route('/<int:userId>/confirm')
def confirm(userId):
    """+--------------------------------------------------------------------------------------+
       |Gera novo link de confirmação de e-mail para usuário novo.                            |
       +--------------------------------------------------------------------------------------+
    """
    user = db.session.query(users.userEmail).filter(users.id == userId).first()

    send_confirmation_email(user.userEmail)

    registra_log_auto(current_user.id,'Novo e-mail de confirmação enviado para '+ user.userEmail +'.')

    flash('Novo e-mail de confirmação enviado para '+ user.userEmail +'.','sucesso')

    return redirect(url_for('usuarios.view_users'))

# confirmar registro

@usuarios.route('/confirm/<token>')
def confirm_email(token):
    """+--------------------------------------------------------------------------------------+
       |Trata o retorno do e-mail de confirmação de registro, verificano se o token enviado   |
       |é válido (igual ao enviado no momento do registro e tem menos de 1 hora de vida).     |
       +--------------------------------------------------------------------------------------+
    """
    try:
        confirm_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        email = confirm_serializer.loads(token, salt='email-confirmation-salt', max_age=3600)
    except:
        flash('O link de confirmação é inválido ou expirou.', 'erro')
        return redirect(url_for('usuarios.login'))

    user = users.query.filter_by(userEmail=email).first()

    if user.email_confirmed:
        flash('Confirmação já realizada. Por favor, faça o login.', 'erro')
    else:
        user.email_confirmed = True
        user.email_confirmed_on = datetime.now()

        db.session.commit()
        flash('Obrigado por confirmar seu endereço de e-mail! Caso já tenha uma janela do sistema aberta, pode fechar a anterior.','sucesso')

    return redirect(url_for('usuarios.login'))

# gera token para resetar senha

@usuarios.route('/reset', methods=["GET", "POST"])
def reset():
    """+--------------------------------------------------------------------------------------+
       |Trata o pedido de troca de senha. Enviando um e-mail para o usuário.                  |
       |O usuário deve estar registrado (com registro confirmado) antes de poder efetuar uma  |
       |troca de senha.                                                                       |
       |O aplicativo envia uma mensagem ao usuário sobre o procedimento de troca de senha.    |
       +--------------------------------------------------------------------------------------+
    """
    form = EmailForm()

    if form.validate_on_submit():
        try:
            user = users.query.filter_by(userEmail=form.email.data).first_or_404()
        except:
            flash('Endereço de e-mail inválido!', 'erro')
            return render_template('email.html', form=form)

        if user.email_confirmed:
            send_password_reset_email(user.userEmail)
            flash('Verifique a caixa de entrada de seu e-mail. Uma mensagem com o link de atualização de senha foi enviado.', 'sucesso')
        else:
            flash('Seu endereço de e-mail precisa ser confirmado antes de tentar efetuar uma troca de senha.', 'erro')
        return redirect(url_for('usuarios.login'))

    return render_template('email.html', form=form)

# trocar ou gerar nova senha

@usuarios.route('/reset/<token>', methods=["GET", "POST"])
def reset_with_token(token):
    """+--------------------------------------------------------------------------------------+
       |Trata o retorno do e-mail enviado ao usuário com token de troca de senha.             |
       |Verifica se o token é válido.                                                         |
       |Abre tela para o usuário informar nova senha.                                         |
       +--------------------------------------------------------------------------------------+
    """
    try:
        password_reset_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        email = password_reset_serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash('O link de atualização de senha é inválido ou expirou.', 'erro')
        return redirect(url_for('usuarios.login'))

    form = PasswordForm()

    if form.validate_on_submit():
        try:
            user = users.query.filter_by(userEmail=email).first_or_404()
        except:
            flash('Endereço de e-mail inválido!', 'erro')
            return redirect(url_for('usuarios.login'))

        user.password_hash = generate_password_hash(form.password.data)

        db.session.commit()

        registra_log_auto(user.id,'Senha alterada.')

        flash('Sua senha foi atualizada!', 'sucesso')

        return redirect(url_for('usuarios.login'))

    return render_template('troca_senha_com_token.html', form=form, token=token)


# trocar ou gerar nova senha via app

@usuarios.route('/troca_senha', methods=["GET", "POST"])
def troca_senha():
    """+--------------------------------------------------------------------------------------+
       |Abre tela para o usuário informar nova senha.                                         |
       +--------------------------------------------------------------------------------------+
    """

    form = TrocaPasswordForm()

    if form.validate_on_submit():

        if current_user.ativo != 1:
            flash('Usuário deve ser ativado antes de poder trocar senha!', 'erro')
            return redirect(url_for('users.login'))

        if current_user.check_password(form.password_atual.data):    

            current_user.password_hash = generate_password_hash(form.password_nova.data)

            db.session.commit()

            registra_log_auto(current_user.id,None,'sen')

            logout_user()

            flash('Sua senha foi atualizada!', 'sucesso')
            return redirect(url_for('users.login'))

    return render_template('troca_senha.html', form=form)



# login

@usuarios.route('/login', methods=['GET','POST'])
def login():
    """+--------------------------------------------------------------------------------------+
       |Fornece a tela para que o usuário entre no sistema (login).                           |
       |O acesso é feito por e-mail e senha cadastrados.                                      |
       |Antes do primeiro acesso após o registro, o usuário precisa cofirmar este registro    |
       |para poder fazer o login, conforme mensagem enviada.                                  |
       +--------------------------------------------------------------------------------------+
    """
    
    usuarios_qtd = users.query.count()
    
    form = LoginForm()

    if form.validate_on_submit():

        user = users.query.filter_by(userEmail=form.email.data).first()

        if user is not None:

            if user.check_password(form.password.data):

                if user.email_confirmed:

                    user.last_logged_in = user.current_logged_in
                    user.current_logged_in = datetime.now()
                    db.session.commit()

                    login_user(user)

                    flash('Login bem sucedido!','sucesso')

                    next = request.args.get('next')

                    if next == None or not next[0] == '/':
                        next = url_for('core.index')

                    return redirect(next)

                else:
                    flash('Endereço de e-mail não confirmado ainda!','erro')

            else:
                flash('Senha não confere, favor verificar!','erro')

        else:
            flash('E-mail informado não encontrado, favor verificar!','erro')

    if usuarios_qtd == 0:
        flash('Não foram encontrados usuários no sistema. O primeiro será registrado de forma direta.','erro')
        return redirect(url_for('usuarios.primeiro_user'))
    
    return render_template('login.html',form=form)

# procedimentos para o primeiro usuário

@usuarios.route('/primeiro_user', methods=['GET','POST'])
def primeiro_user():
    """+--------------------------------------------------------------------------------------+
       |Opção de cadastro do primeiro usuário no caso em que a mensageria não esteja          |
       |Funcionando. Verifica-se se a tabela users está vazia e permite o cadastro do         |
       |usuáro a acessar o sistema após sua instalação.                                       |
       +--------------------------------------------------------------------------------------+
    """

    usuarios_qtd = users.query.count()

    form = RegistrationForm()

    if form.validate_on_submit():

        if usuarios_qtd == 0:

            user = users(userNome                  = form.username.data,
                        userEmail                  = form.email.data,
                        plaintext_password         = form.password.data,
                        email_confirmation_sent_on = datetime.now(),
                        userAtivo                  = True,
                        userEnvia                  = False)

            db.session.add(user)
            db.session.commit()

            user.email_confirmed = True
            user.email_confirmed_on = datetime.now()

            db.session.commit()

            registra_log_auto(user.id,'Primeiro usuário '+ user.userNome +' registrado e confirmado de forma direta.')
        
            flash('Primeiro usuário '+ user.userNome +' registrado e confirmado de forma direta!','sucesso')
            
            return redirect(url_for('usuarios.login'))

        else:
            flash('Já existem usuários registrados!','erro')
            return redirect(url_for('core.index'))

    return render_template('register.html',form=form)


# logout

@usuarios.route('/logout')
def logout():
    """+--------------------------------------------------------------------------------------+
       |Efetua a saída do usuário do sistema.                                                 |
       +--------------------------------------------------------------------------------------+
    """
    logout_user()
    return redirect(url_for("core.index"))


# Lista dos usuários vista pelo admin

@usuarios.route('/view_users')
@login_required
def view_users():
    """+--------------------------------------------------------------------------------------+
       |Mostra lista dos usuários cadastrados.                                                |
       +--------------------------------------------------------------------------------------+
    """
    lista = users.query.order_by(users.id).all()

    return render_template('view_users.html', lista=lista)

#
## alterações em users 

@usuarios.route("/<int:user_id>/update_user", methods=['GET', 'POST'])
@login_required
def update_user(user_id):
    """
    +----------------------------------------------------------------------------------------------+
    |Permite ao admin atualizar dados de um user.                                                  |
    |                                                                                              |
    |Recebe o id do user como parâmetro.                                                           |
    +----------------------------------------------------------------------------------------------+
    """

    user = users.query.get_or_404(user_id)

    form = AdminForm()

    if form.validate_on_submit():

        if current_user.userAtivo:

            user.userAtivo = form.ativo.data
            user.userEnvia = form.envia.data

            if not user.email_confirmed and form.ativo.data:
                user.email_confirmed = True
                user.email_confirmed_on = datetime.now()

            db.session.commit()

            registra_log_auto(current_user.id,'Usuário '+ user.userNome +' alterado.')

            flash('Usuário '+ user.userNome +' alterado!','sucesso')

            return redirect(url_for('usuarios.view_users'))

        else:

            flash('O seu usuário precisa ser ativado para esta operação!','erro')

            return redirect(url_for('usuarios.view_users'))


    # traz a informação atual do usuário
    elif request.method == 'GET':

        form.ativo.data = user.userAtivo
        form.envia.data = user.userEnvia

    return render_template('update_user.html', title='Update', name=user.userNome,
                            form=form)

#
# mostra log

@usuarios.route("/<tipo>/log", methods=['GET', 'POST'])
@login_required
def log (tipo):
    """+--------------------------------------------------------------------------------------+
       |Mostra a atividade no sistema em função dos principais commits.                       |
       |                                                                                      |
       +--------------------------------------------------------------------------------------+
    """

    form = LogForm()

    if form.validate_on_submit():

        data_ini = form.data_ini.data
        data_fim = form.data_fim.data
        
        if tipo == 'geral':

            log = db.session.query(Log_Auto.id,
                                   Log_Auto.data_hora,
                                   users.userNome,
                                   Log_Auto.msg)\
                            .join(users, Log_Auto.user_id == users.id)\
                            .filter(Log_Auto.data_hora >= datetime.combine(data_ini,time.min),
                                    Log_Auto.data_hora <= datetime.combine(data_fim,time.max))\
                            .order_by(Log_Auto.id.desc())\
                            .all()
        
        elif tipo == 'envio':
            
            log = db.session.query(Log_Auto.id,
                                   Log_Auto.data_hora,
                                   users.userNome,
                                   Log_Auto.msg)\
                            .join(users, Log_Auto.user_id == users.id)\
                            .filter(Log_Auto.data_hora >= datetime.combine(data_ini,time.min),
                                    Log_Auto.data_hora <= datetime.combine(data_fim,time.max),
                                    Log_Auto.msg.like('*%'))\
                            .order_by(Log_Auto.id.desc())\
                            .all()                    

        return render_template('user_log.html', log=log, name=current_user.userNome,
                               form=form, tipo=tipo)


    # traz a log das últimas 24 horas e registra entrada manual de log, se for o caso.
    else:
        
        if tipo == 'geral':

            log = db.session.query(Log_Auto.id,
                                Log_Auto.data_hora,
                                users.userNome,
                                Log_Auto.msg)\
                            .join(users, Log_Auto.user_id == users.id)\
                            .filter(Log_Auto.data_hora >= (datetime.now()-timedelta(days=1)))\
                            .order_by(Log_Auto.id.desc())\
                            .all()
                            
        elif tipo == 'envio':
            
            log = db.session.query(Log_Auto.id,
                                Log_Auto.data_hora,
                                users.userNome,
                                Log_Auto.msg)\
                            .join(users, Log_Auto.user_id == users.id)\
                            .filter(Log_Auto.data_hora >= (datetime.now()-timedelta(days=1)),
                                    Log_Auto.msg.like('*%'))\
                            .order_by(Log_Auto.id.desc())\
                            .all()

        return render_template('user_log.html', log=log, name=current_user.userNome,
                           form=form, tipo=tipo)

#








