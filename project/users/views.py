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
    * Registrar versão do sistema: admin_reg_ver
    * Visão dos usuários pelo admin: admin_view_users
    * Log de atividades: user_log
    * Registro de observações do usuário no log: user_obs
    * Relatório de atividades: user_rel

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
from project.models import User, Demanda, Despacho, Providencia, Coords, Log_Auto,\
                           Log_Desc, Plano_Trabalho, Sistema
from project.users.forms import RegistrationForm, LoginForm, UpdateUserForm, EmailForm, PasswordForm, AdminForm,\
                                LogForm, LogFormMan, VerForm, RelForm
from project.users.picture_handler import add_profile_pic
from project.demandas.views import registra_log_auto

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

        version = db.session.query(User.sversion).first()

        user = User(email                      = form.email.data,
                    username                   = form.username.data,
                    plaintext_password         = form.password.data,
                    despacha                   = form.despacha.data,
                    despacha2                  = form.despacha2.data,
                    coord                      = form.coord.data,
                    email_confirmation_sent_on = datetime.now(),
                    ativo                      = False,
                    sversion = version[0])

        db.session.add(user)
        db.session.commit()

        last_id = db.session.query(User.id).order_by(User.id.desc()).first()

        registra_log_auto(last_id[0],None,'usu')

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

        registra_log_auto(current_user.id,None,'sen')

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
                    #db.session.add(user)
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

        registra_log_auto(current_user.id,None,'usu')

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

@users.route('/user_posts/<filtro>/<username>')
def user_posts (username,filtro):
    """+--------------------------------------------------------------------------------------+
       |Mostra as demandas de um usuário quando seu nome é selecionado em uma tela de         |
       |consulta de demandas.                                                                 |
       |Recebe o nome do usuário como parâmetro e o tipo de consulta (filtro)                 |
       +--------------------------------------------------------------------------------------+
    """

    qtd = 0

    page = request.args.get('page',1,type=int)

    com_despacho_novo = []

    user = None

    if filtro == 'nc':

        user = User.query.filter_by(username=username).first_or_404()

        # demandas = Demanda.query.filter_by(author=user,conclu=False)\
                         # .order_by(Demanda.data.desc())\
                         # .paginate(page=page,per_page=10)

        demandas = db.session.query(Demanda.id,
                                    Demanda.programa,
                                    Demanda.sei,
                                    Demanda.convênio,
                                    Demanda.ano_convênio,
                                    Demanda.tipo,
                                    Demanda.data,
                                    Demanda.user_id,
                                    Demanda.titulo,
                                    Demanda.desc,
                                    Demanda.necessita_despacho,
                                    Demanda.conclu,
                                    Demanda.data_conclu,
                                    Demanda.necessita_despacho_cg,
                                    Demanda.urgencia,
                                    Demanda.data_env_despacho,
                                    Demanda.nota,
                                    Plano_Trabalho.atividade_sigla)\
                             .outerjoin(Plano_Trabalho, Plano_Trabalho.id == Demanda.programa)\
                             .filter(Demanda.author == user, Demanda.conclu == False)\
                             .order_by(Demanda.data.desc())\
                             .paginate(page=page,per_page=10)

        # verificar se tem despacho novo
        for demanda in demandas.items:

            providencias = db.session.query(Providencia.data,
                                            label('tipo','PROV - '+ Providencia.texto))\
                                            .filter(Providencia.demanda_id == demanda.id)\
                                            .order_by(Providencia.data.desc()).all()

            despachos = db.session.query(Despacho.data,
                                         label('tipo','DESP - '+Despacho.texto))\
                                        .filter_by(demanda_id=demanda.id)\
                                        .order_by(Despacho.data.desc()).all()

            pro_des = providencias + despachos
            pro_des.sort(key=lambda ordem: ordem.data,reverse=True)

            if pro_des != []:
                if pro_des[0].tipo[0:6] == 'DESP -':
                    com_despacho_novo.append(demanda.id)

    elif filtro == 'conclu':

        demandas = db.session.query(Demanda.id,
                                    Demanda.programa,
                                    Demanda.sei,
                                    Demanda.convênio,
                                    Demanda.ano_convênio,
                                    Demanda.tipo,
                                    Demanda.data,
                                    Demanda.user_id,
                                    Demanda.titulo,
                                    Demanda.desc,
                                    Demanda.necessita_despacho,
                                    Demanda.conclu,
                                    Demanda.data_conclu,
                                    Demanda.necessita_despacho_cg,
                                    Demanda.urgencia,
                                    Demanda.data_env_despacho,
                                    Demanda.nota,
                                    Plano_Trabalho.atividade_sigla)\
                                    .outerjoin(Plano_Trabalho, Plano_Trabalho.id == Demanda.programa)\
                                    .filter(Demanda.conclu == True)\
                                    .order_by(Demanda.data_conclu.desc())\
                                    .paginate(page=page,per_page=10)

    else:

        user = User.query.filter_by(username=username).first_or_404()

        demandas = db.session.query(Demanda.id,
                                    Demanda.programa,
                                    Demanda.sei,
                                    Demanda.convênio,
                                    Demanda.ano_convênio,
                                    Demanda.tipo,
                                    Demanda.data,
                                    Demanda.user_id,
                                    Demanda.titulo,
                                    Demanda.desc,
                                    Demanda.necessita_despacho,
                                    Demanda.conclu,
                                    Demanda.data_conclu,
                                    Demanda.necessita_despacho_cg,
                                    Demanda.urgencia,
                                    Demanda.data_env_despacho,
                                    Demanda.nota,
                                    Plano_Trabalho.atividade_sigla)\
                                    .outerjoin(Plano_Trabalho, Plano_Trabalho.id == Demanda.programa)\
                                    .filter(Demanda.author == user)\
                                    .order_by(Demanda.data.desc())\
                                    .paginate(page=page,per_page=10)

    qtd = demandas.total

    return render_template('user_demandas.html',demandas=demandas,user=user, filtro=filtro, qtd = qtd, com_despacho_novo=com_despacho_novo)

#
# lista plano de trabalho (atividades) de um usuário

@users.route('/user_pt/int:<user_id>')
def user_pt (user_id):
    """+--------------------------------------------------------------------------------------+
       |Mostra as atividades designadas a um usuário no plano de trabalho da                  |
       |coordenação.                                                                          |
       |Recebe o id do usuário como parâmetro.                                                |
       +--------------------------------------------------------------------------------------+
    """

    user = User.query.get_or_404(user_id)

    User1 = aliased(User)
    User2 = aliased(User)

    atividades_1 = db.session.query(Plano_Trabalho.id,
                                    Plano_Trabalho.atividade_sigla,
                                    Plano_Trabalho.atividade_desc,
                                    Plano_Trabalho.natureza,
                                    Plano_Trabalho.meta,
                                    label('resp1',User1.username),
                                    label('resp2',User2.username))\
                                    .join(User1, Plano_Trabalho.respon_1 == User1.id)\
                                    .join(User2, Plano_Trabalho.respon_2 == User2.id)\
                                    .filter(Plano_Trabalho.respon_1 == user_id)\
                                    .order_by(Plano_Trabalho.natureza,Plano_Trabalho.atividade_sigla).all()

    quantidade_1 = len(atividades_1)

    carga_1 = db.session.query(label('total',func.sum(Plano_Trabalho.meta)))\
                        .filter(Plano_Trabalho.respon_1 == user_id).all()

    atividades_2 = db.session.query(Plano_Trabalho.id,
                                    Plano_Trabalho.atividade_sigla,
                                    Plano_Trabalho.atividade_desc,
                                    Plano_Trabalho.natureza,
                                    Plano_Trabalho.meta,
                                    label('resp1',User1.username),
                                    label('resp2',User2.username))\
                                    .join(User1, Plano_Trabalho.respon_1 == User1.id)\
                                    .join(User2, Plano_Trabalho.respon_2 == User2.id)\
                                    .filter(Plano_Trabalho.respon_2 == user_id)\
                                    .order_by(Plano_Trabalho.natureza,Plano_Trabalho.atividade_sigla).all()

    quantidade_2 = len(atividades_2)

    carga_2 = db.session.query(label('total',func.sum(Plano_Trabalho.meta)))\
                        .filter(Plano_Trabalho.respon_2 == user_id).all()


    return render_template('user_pt.html',user=user, atividades_1=atividades_1, atividades_2=atividades_2,\
                            quantidade_1=quantidade_1, quantidade_2=quantidade_2, carga_1=carga_1[0][0], carga_2=carga_2[0][0])

# admim registra nova versão do sistema no banco de dadosSEI

@users.route('/admin_reg_ver', methods=['GET', 'POST'])
@login_required

def admin_reg_ver():
    """+--------------------------------------------------------------------------------------+
       |O admin atualiza no banco de dados (tabela Users) a versão do sistema após uma        |
       |atualização.                                                                          |
       +--------------------------------------------------------------------------------------+
    """
    if current_user.role[0:5] != 'admin':
        abort(403)
    else:
        users   = User.query.order_by(User.id).all()
        sistema = Sistema.query.first()

        form = VerForm()

        if form.validate_on_submit():

            for user in users:

                user.sversion = form.ver.data

            db.session.commit()

            sistema.nome_sistema = form.nome_sistema.data
            sistema.descritivo   = form.descritivo.data

            registra_log_auto(current_user.id,None,'ver')

            flash('Dados gerais do sistema atualizados!','sucesso')

            return redirect(url_for('core.index'))

        # traz a versão atual
        elif request.method == 'GET':

            form.ver.data          = users[0].sversion
            form.nome_sistema.data = sistema.nome_sistema
            form.descritivo.data   = sistema.descritivo

        return render_template('admin_reg_ver.html', title='Update', form=form)


# Lista dos usuários vista pelo admin

@users.route('/admin_view_users')
@login_required

def admin_view_users():
    """+--------------------------------------------------------------------------------------+
       |Mostra lista dos usuários cadastrados.                                                |
       |Visto somente por admin.                                                              |
       +--------------------------------------------------------------------------------------+
    """
    if current_user.role[0:5] != 'admin':
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
    if current_user.role[0:5] != 'admin':

        abort(403)

    else:

        user = User.query.get_or_404(user_id)

        form = AdminForm()

        if form.validate_on_submit():

            user.coord      = form.coord.data
            user.despacha   = form.despacha.data
            user.despacha2  = form.despacha2.data
            user.role       = form.role.data
            user.cargo_func = form.cargo_func.data
            user.ativo      = form.ativo.data

            db.session.commit()

            registra_log_auto(current_user.id,None,'adm')

            flash('Usuário atualizado!','sucesso')

            return redirect(url_for('users.admin_view_users'))

        # traz a informação atual do usuário
        elif request.method == 'GET':

            form.coord.data      = user.coord
            form.despacha.data   = user.despacha
            form.despacha2.data  = user.despacha2
            form.role.data       = user.role
            form.cargo_func.data = user.cargo_func
            form.ativo.data      = user.ativo

        return render_template('admin_update_user.html', title='Update', name=user.username,
                               form=form)

#
# diário do usuário

@users.route("/<usu>/user_log", methods=['GET', 'POST'])
@login_required
def user_log (usu):
    """+--------------------------------------------------------------------------------------+
       |Mostra a atividade do usuário em função dos principais commits.                       |
       |                                                                                      |
       +--------------------------------------------------------------------------------------+
    """

    if usu == 'todos':
        user_id = '%'
    else:
        user_id = current_user.id

    form = LogForm()
    form2 = LogFormMan()

    if form.validate_on_submit():

        data_ini = form.data_ini.data
        data_fim = form.data_fim.data
        log_part = form.log_part.data

        log = db.session.query(Log_Auto.id,
                               Log_Auto.data_hora,
                               Log_Auto.demanda_id,
                               Log_Auto.tipo_registro,
                               Log_Desc.desc_registro,
                               User.username)\
                        .outerjoin(Log_Desc, Log_Auto.tipo_registro == Log_Desc.tipo_registro)\
                        .join(User, Log_Auto.user_id == User.id)\
                        .filter(Log_Auto.user_id.like(user_id),
                                Log_Auto.data_hora >= datetime.combine(data_ini,time.min),
                                Log_Auto.data_hora <= datetime.combine(data_fim,time.max),
                                Log_Auto.tipo_registro.like('%'+log_part+'%'))\
                        .all()

        # cria lista com ocorrências de tipo de registro

        l_log = [entrada.desc_registro for entrada in log]

        # conta entradas no log por tipo de registro, gerando um dicionário classificado

        agregado = {k: v for k, v in sorted(Counter(l_log).items(), key=lambda item: item[1])}

        return render_template('user_log.html', log=log, name=current_user.username,
                               form=form, usu=usu, agregado=agregado)


    # traz a log das últimas 24 horas e registra entrada manual de log, se for o caso.
    else:

        log = db.session.query(Log_Auto.id,
                               Log_Auto.data_hora,
                               Log_Auto.demanda_id,
                               Log_Auto.tipo_registro,
                               Log_Desc.desc_registro,
                               User.username)\
                        .outerjoin(Log_Desc, Log_Auto.tipo_registro == Log_Desc.tipo_registro)\
                        .join(User, Log_Auto.user_id == User.id)\
                        .filter(Log_Auto.user_id.like(user_id),
                                Log_Auto.data_hora >= (datetime.now()-timedelta(days=1)))\
                        .all()

        # cria lista com ocorrências de tipo de registro

        l_log = [entrada.desc_registro for entrada in log]

        # conta entradas no log por tipo de registro, gerando um dicionário classificado

        agregado = {k: v for k, v in sorted(Counter(l_log).items(), key=lambda item: item[1])}


        return render_template('user_log.html', log=log, name=current_user.username,
                           form=form, form2=form2, usu=usu, agregado=agregado)

#
# registro de observações do usuário no log

@users.route("/user_obs", methods=['GET','POST'])
@login_required
def user_obs():
    """+--------------------------------------------------------------------------------------+
       |Permite o registro de observação do usário no log.                                    |
       |                                                                                      |
       +--------------------------------------------------------------------------------------+
    """

    form = LogFormMan()

    if form.validate_on_submit():

        if form.entrada_log.data != '':

            registra_log_auto(current_user.id,None,'man: '+form.entrada_log.data)

            form.entrada_log.data = ''

        return redirect(url_for('users.user_log',usu='*'))

    return render_template('user_obs.html', form=form)

#
# gerar relatório de atividades

@users.route("/user_rel", methods=['GET','POST'])
@login_required
def user_rel():
    """+--------------------------------------------------------------------------------------+
       |Permite gerar html do relatório de atividades no período informado.                   |
       |                                                                                      |
       +--------------------------------------------------------------------------------------+
    """

    form = RelForm()

    if form.validate_on_submit():

        coordenador = db.session.query(User.username,
                                       User.cargo_func,
                                       User.email)\
                                .filter(User.cargo_func == 'Coordenador(a)').first_or_404()
        coordenador_geral = db.session.query(User.username,
                                             User.cargo_func,
                                             User.email)\
                                       .filter(User.cargo_func == 'Coordenador(a)-Geral').first_or_404()

        data_ini = form.data_ini.data
        data_fim = form.data_fim.data

        log = db.session.query(Log_Auto.id,
                               Log_Auto.data_hora,
                               Log_Auto.demanda_id,
                               Log_Auto.tipo_registro,
                               Log_Desc.desc_registro,
                               User.username,
                               Demanda.programa,
                               Demanda.sei,
                               Demanda.conclu)\
                        .outerjoin(Log_Desc, Log_Desc.tipo_registro == Log_Auto.tipo_registro)\
                        .join(User, User.id == Log_Auto.user_id)\
                        .outerjoin(Demanda, Demanda.id == Log_Auto.demanda_id)\
                        .filter(Log_Auto.user_id.like(current_user.id),
                                Log_Auto.data_hora >= datetime.combine(data_ini,time.min),
                                Log_Auto.data_hora <= datetime.combine(data_fim,time.max))\
                        .subquery()

        atividades = db.session.query(log,
                                      Plano_Trabalho.atividade_sigla)\
                               .outerjoin(Plano_Trabalho, Plano_Trabalho.id == log.c.programa)\
                               .all()

        registra_log_auto(current_user.id,None,'rel')

        return render_template('form_atividades.html', log=log, atividades = atividades,
                                data_ini=data_ini.strftime('%x'), data_fim=data_fim.strftime('%x'),
                                coordenador=coordenador, coordenador_geral=coordenador_geral)

    return render_template('user_inf_datas.html', form=form)
