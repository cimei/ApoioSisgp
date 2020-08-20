"""
.. topic:: Usuários (views)

    Usuários registrados são os técnicos que administram suas demandas neste aplicativo.
    Cada usuário tem seu ID, nome, e-mail e senha únicos, podendo ter também uma imagem personalizada
    de perfil, caso deseje.

    O registro é feito por meio da respectiva opção no menu do aplicativo, com o preenchimento dos dados
    básicos do usuário. Este registro precisa ser confirmado com o token enviado pelo sistema, por e-mail,
    ao usúario.

    Para entrar no aplicativo, o usuário se idenfica com seu e-mail e informa sua senha pessoal.

    O usuário pode alterar seus dados de perfil, contudo, para alterar sua senha, seja por motivo de
    esquecimento, ou simplemente porque quer alterá-la, o procedimento envolve o envio de um e-mail
    do sistema para seu endereço de e-mail registrado, com o token que abre uma tela para registro de
    nova senha. Este token tem validade de uma hora.

    As funções relativas ao tratamento de demandas só ficam disponíveis no menu para usuários registrados.

.. topic:: Ações relacionadas aos usuários:

    * Funções auxiliares:
        * Envia e-mail de forma assincrona: send_async_email
        * Prepara e-mail: send_email
        * Dados para e-mail de confirmação: send_confirmation_email
        * Dados para e-mail de troca de senha: send_password_reset_email
    * Registro de usuário: register
    * Trata retorno da confirmação: confirm_email
    * Trata pedido de troca de senha: reset
    * Realiza troca de senha: reset_with_token
    * Entrada de usuário: login
    * Saída de usuário: logout
    * Atualizar dados do usuário: account
    * Demandas de um usuário: user_posts
    * Visão dos usuários pelo admin: admin_view_users

"""
# views.py na pasta users

from itsdangerous import URLSafeTimedSerializer
from flask import render_template, url_for, flash, redirect, request, Blueprint, abort
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from threading import Thread
from datetime import datetime, date
from werkzeug.security import generate_password_hash
from sqlalchemy import func
from sqlalchemy.sql import label

from project import db, mail, app
from project.models import User, Demanda, Despacho, Providencia, Coords
from project.users.forms import RegistrationForm, LoginForm, UpdateUserForm, EmailForm, PasswordForm, AdminForm
from project.users.picture_handler import add_profile_pic

users = Blueprint('users',__name__)

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
        'users.confirm_email',
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
        'users.reset_with_token',
        token = password_reset_serializer.dumps(user_email, salt='password-reset-salt'),
        _external=True)

    html = render_template(
        'email_senha_atualiza.html',
        password_reset_url=password_reset_url)

    send_email('Atualização de senha solicitada', [user_email],'', html)

# registrar

@users.route('/register', methods=['GET','POST'])
def register():
    """+--------------------------------------------------------------------------------------+
       |Efetua o registro de um usuário. Este recebe o aviso para verificar sua caixa de      |
       |e-mails, pois o aplicativo envia uma mensagem sobre a confirmação do registro.        |
       +--------------------------------------------------------------------------------------+
    """
    form = RegistrationForm()

    if form.validate_on_submit():

        form.check_username(form.username)

        form.check_email(form.email)

        user = User(email                      = form.email.data,
                    username                   = form.username.data,
                    plaintext_password         = form.password.data,
                    despacha                   = form.despacha.data,
                    despacha2                  = form.despacha2.data,
                    coord                      = form.coord.data,
                    email_confirmation_sent_on = datetime.now(),
                    ativo                      = False)

        db.session.add(user)
        db.session.commit()

        coords = db.session.query(Coords.sigla).all()

        if (form.coord.data,) not in coords:
            coord = Coords(sigla = form.coord.data)
            db.session.add(coord)
            db.session.commit()

        send_confirmation_email(user.email)
        flash('Usuário registrado! Verifique sua caixa de e-mail para confirmar o endereço.','sucesso')
        return redirect(url_for('core.index'))

    return render_template('register.html',form=form)

# confirmar registro

@users.route('/confirm/<token>')
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
        return redirect(url_for('users.login'))

    user = User.query.filter_by(email=email).first()

    if user.email_confirmed:
        flash('Confirmação já realizada. Por favor, faça o login.', 'erro')
    else:
        user.email_confirmed = True
        user.email_confirmed_on = datetime.now()

        db.session.commit()
        flash('Obrigado por confirmar seu endereço de e-mail! Caso já tenha uma janela do sistema aberta, pode fechar a anterior.','sucesso')

    return redirect(url_for('users.login'))

# gera token para resetar senha

@users.route('/reset', methods=["GET", "POST"])
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
            user = User.query.filter_by(email=form.email.data).first_or_404()
        except:
            flash('Endereço de e-mail inválido!', 'erro')
            return render_template('email.html', form=form)

        if user.email_confirmed:
            send_password_reset_email(user.email)
            flash('Verifique a caixa de entrada de seu e-mail. Uma mensagem com o link de atualização de senha foi enviado.', 'sucesso')
        else:
            flash('Seu endereço de e-mail precisa ser confirmado antes de tentar efetuar uma troca de senha.', 'erro')
        return redirect(url_for('users.login'))

    return render_template('email.html', form=form)

# trocar ou gerar nova senha

@users.route('/reset/<token>', methods=["GET", "POST"])
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
        return redirect(url_for('users.login'))

    form = PasswordForm()

    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=email).first_or_404()
        except:
            flash('Endereço de e-mail inválido!', 'erro')
            return redirect(url_for('users.login'))

        #user.password = form.password.data
        user.password_hash = generate_password_hash(form.password.data)

        db.session.commit()
        flash('Sua senha foi atualizada!', 'sucesso')
        return redirect(url_for('users.login'))

    return render_template('troca_senha_com_token.html', form=form, token=token)


# login

@users.route('/login', methods=['GET','POST'])
def login():
    """+--------------------------------------------------------------------------------------+
       |Fornece a tela para que o usuário entre no sistema (login).                           |
       |O acesso é feito por e-mail e senha cadastrados.                                      |
       |Antes do primeiro acesso após o registro, o usuário precisa cofirmar este registro    |
       |para poder fazer o login, conforme mensagem enviada.                                  |
       +--------------------------------------------------------------------------------------+
    """
    form = LoginForm()

    if form.validate_on_submit():

        user = User.query.filter_by(email=form.email.data).first()

        if user is not None:

            if user.check_password(form.password.data):

                if user.email_confirmed:

                    user.last_logged_in = user.current_logged_in
                    user.current_logged_in = datetime.now()
                    db.session.add(user)
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
            flash('E-mail informado não encontradao, favor verificar!','erro')

    return render_template('login.html',form=form)

# logout

@users.route('/logout')
def logout():
    """+--------------------------------------------------------------------------------------+
       |Efetua a saída do usuário do sistema.                                                 |
       +--------------------------------------------------------------------------------------+
    """
    logout_user()
    return redirect(url_for("core.index"))

# conta (update UserForm)

@users.route('/account', methods=['GET','POST'])
@login_required
def account():
    """+--------------------------------------------------------------------------------------+
       |Permite que o usuário atualize seus dados.                                            |
       |A tela é acessada quando o usuário clica em seu nome na barra de menus.               |
       |Este pode atualizar seu nome de usuário, seu endereço de e-mail e sua imagem          |
       |de perfil .                                                                           |
       |Mostra estatísticas do usuário.                                                       |
       +--------------------------------------------------------------------------------------+
    """
    hoje = date.today()

    form = UpdateUserForm()

    if form.validate_on_submit():

        current_user.username = form.username.data
        current_user.email = form.email.data

        #if form.picture.data:

        #    pic = add_profile_pic(form.picture.data)
        #    current_user.profile_image = pic

        db.session.commit()
        flash('Usuário atualizado!','sucesso')
        return redirect (url_for('users.account'))

    elif request.method == "GET":

        form.username.data = current_user.username
        form.email.data = current_user.email

        # calcula quantidade de demandas do usuário
        user_demandas = db.session.query(Demanda.user_id,func.count(Demanda.user_id)).filter(Demanda.user_id == current_user.id)

        qtd_demandas = user_demandas[0][1]

        # calcula quantidade de demandas concluídas do usuário
        user_demandas_conclu = db.session.query(Demanda.user_id,func.count(Demanda.user_id))\
                                         .filter(Demanda.user_id == current_user.id, Demanda.conclu == '1')

        qtd_demandas_conclu = user_demandas_conclu[0][1]

        if qtd_demandas != 0:
            percent_conclu = round((qtd_demandas_conclu / qtd_demandas) * 100)
        else:
            percent_conclu = 0

        ## calcula a vida média das demandas do usuário
        demandas_datas = db.session.query(Demanda.data,Demanda.data_conclu)\
                                    .filter(Demanda.conclu == '1', Demanda.data_conclu != None, Demanda.user_id == current_user.id)

        vida = 0
        vida_m = 0

        for dia in demandas_datas:
            vida += (dia.data_conclu - dia.data).days

        if len(list(demandas_datas)) > 0:
            vida_m = round(vida/len(list(demandas_datas)))
        else:
            vida_m = 0

        ## calcula o prazo médio dos despachos
        despachos = db.session.query(label('c_data',Despacho.data), Despacho.demanda_id, Demanda.id, label('i_data',Demanda.data))\
                              .outerjoin(Demanda, Despacho.demanda_id == Demanda.id)\
                              .filter(Demanda.user_id == current_user.id)\
                              .all()

        desp = 0
        desp_m = 0

        for despacho in despachos:
            desp += (despacho.c_data - despacho.i_data).days

        if len(list(despachos)) > 0:
            desp_m = round(desp/len(list(despachos)))
        else:
            desp_m = 0

        ## média de demandas, providêndcias e despachos por mês nos últimos 12 meses

        meses = []
        for i in range(12):
            m = hoje.month-i-1
            y = hoje.year
            if m < 1:
                m += 12
                y -= 1
            if m >= 0 and m < 10:
                m = '0' + str(m)
            meses.append((str(m),str(y)))

        demandas_12meses = [Demanda.query.filter(Demanda.data >= mes[1]+'-'+mes[0]+'-01',
                                                 Demanda.data <= mes[1]+'-'+mes[0]+'-31',
                                                 Demanda.user_id == current_user.id).count()
                                                 for mes in meses]

        med_dm = round(sum(demandas_12meses)/len(demandas_12meses))
        max_dm = max(demandas_12meses)
        mes_max_dm = meses[demandas_12meses.index(max_dm)]
        min_dm = min(demandas_12meses)
        mes_min_dm = meses[demandas_12meses.index(min_dm)]

        providencias_12meses = [Providencia.query.filter(Providencia.data >= mes[1]+'-'+mes[0]+'-01',
                                                 Providencia.data <= mes[1]+'-'+mes[0]+'-31',
                                                 Providencia.user_id == current_user.id).count()
                                                 for mes in meses]

        med_pr = round(sum(providencias_12meses)/len(providencias_12meses))
        max_pr = max(providencias_12meses)
        mes_max_pr = meses[providencias_12meses.index(max_pr)]
        min_pr = min(providencias_12meses)
        mes_min_pr = meses[providencias_12meses.index(min_pr)]


    return render_template('account.html',form=form,
                                          qtd_demandas=qtd_demandas,
                                          qtd_demandas_conclu=qtd_demandas_conclu,
                                          percent_conclu=percent_conclu,
                                          vida_m=vida_m,
                                          desp_m=desp_m,
                                          med_dm=med_dm,
                                          max_dm=max_dm,
                                          mes_max_dm=mes_max_dm,
                                          min_dm=min_dm,
                                          mes_min_dm=mes_min_dm,
                                          med_pr=med_pr,
                                          max_pr=max_pr,
                                          mes_max_pr=mes_max_pr,
                                          min_pr=min_pr,
                                          mes_min_pr=mes_min_pr)

# lista das demandas de um usuário

@users.route('/<filtro>/<username>')
def user_posts (username,filtro):
    """+--------------------------------------------------------------------------------------+
       |Mostra as demandas de um usuário quando seu nome é selecionado em uma tela de         |
       |consulta de demandas.                                                                 |
       |Recebe o nome do usuário como parâmetro                                               |
       +--------------------------------------------------------------------------------------+
    """

    qtd = 0

    page = request.args.get('page',1,type=int)

    user = User.query.filter_by(username=username).first_or_404()

    if filtro == 'nc':
        demandas = Demanda.query.filter_by(author=user,conclu=False)\
                                .order_by(Demanda.data.desc())\
                                .paginate(page=page,per_page=10)

    else:
        demandas = Demanda.query.filter_by(author=user)\
                                .order_by(Demanda.data.desc())\
                                .paginate(page=page,per_page=10)

    qtd = demandas.total

    return render_template('user_demandas.html',demandas=demandas,user=user, filtro=filtro, qtd = qtd)

# Lista dos usuários vista pelo admin

@users.route('/admin_view_users')
@login_required

def admin_view_users():
    """+--------------------------------------------------------------------------------------+
       |Mostra lista dos usuários cadastrados.                                                |
       |Visto somente por admin.                                                              |
       +--------------------------------------------------------------------------------------+
    """
    if current_user.role != 'admin':
        abort(403)
    else:
        users = User.query.order_by(User.id).all()
        return render_template('admin_view_users.html', users=users)
    return redirect(url_for('core.index'))

#
## alterações em users pelo admin

@users.route("/<int:user_id>/admin_update_user", methods=['GET', 'POST'])
@login_required
def admin_update_user(user_id):
    """
    +----------------------------------------------------------------------------------------------+
    |Permite ao admin atualizar dados de um user.                                                  |
    |                                                                                              |
    |Recebe o id do user como parâmetro.                                                           |
    +----------------------------------------------------------------------------------------------+
    """
    if current_user.role != 'admin':

        abort(403)

    else:

        user = User.query.get_or_404(user_id)

        form = AdminForm()

        if form.validate_on_submit():

            user.coord      = form.coord.data
            user.despacha   = form.despacha.data
            user.despacha2  = form.despacha2.data
            user.role       = form.role.data
            user.ativo      = form.ativo.data

            db.session.commit()
            flash('Usuário atualizado!')

            return redirect(url_for('users.admin_view_users'))

        # traz a informação atual do usuário
        elif request.method == 'GET':

            form.coord.data     = user.coord
            form.despacha.data  = user.despacha
            form.despacha2.data = user.despacha2
            form.role.data      = user.role
            form.ativo.data     = user.ativo

        return render_template('admin_update_user.html', title='Update', name=user.username,
                               form=form)
