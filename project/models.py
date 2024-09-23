"""
.. topic:: Modelos (tabelas nos bancos de dados)

    Os modelos são classes que definem a estrutura das tabelas dos bancos de dados.

"""
# models.py
import locale
from project import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime, date

from sqlalchemy.dialects.mssql import NUMERIC


@login_manager.user_loader
def load_user(user_id):
    return users.query.get(user_id)


class users(db.Model, UserMixin):

    __tablename__ = 'User'
    __table_args__ = {"schema": "Apoio"}

    id                         = db.Column(db.Integer,primary_key=True)
    userNome                   = db.Column(db.String(64),unique=True,index=True)
    userEmail                  = db.Column(db.String(64),unique=True,index=True)
    password_hash              = db.Column(db.String(128))
    email_confirmation_sent_on = db.Column(db.DateTime, nullable=True)
    email_confirmed            = db.Column(db.Boolean, nullable=True, default=False)
    email_confirmed_on         = db.Column(db.DateTime, nullable=True)
    registered_on              = db.Column(db.DateTime, nullable=True)
    last_logged_in             = db.Column(db.DateTime, nullable=True)
    current_logged_in          = db.Column(db.DateTime, nullable=True)
    userAtivo                  = db.Column(db.Boolean)
    userEnvia                  = db.Column(db.Boolean)
    avaliadorId                = db.Column(db.Integer, nullable=True)
    instituicaoId              = db.Column(db.Integer, nullable=True)
    user_api                   = db.Column(db.String)
    senha_api                  = db.Column(db.String)

    def __init__(self,userNome,userEmail,instituicaoId,plaintext_password,userAtivo,userEnvia,user_api,senha_api,email_confirmation_sent_on=None):

        self.userNome                   = userNome
        self.userEmail                  = userEmail
        self.password_hash              = generate_password_hash(plaintext_password)
        self.email_confirmation_sent_on = email_confirmation_sent_on
        self.email_confirmed            = False
        self.email_confirmed_on         = None
        self.registered_on              = datetime.now()
        self.last_logged_in             = None
        self.current_logged_in          = datetime.now()
        self.userAtivo                  = userAtivo
        self.userEnvia                  = userEnvia
        self.avaliadorId                = None
        self.instituicaoId              = instituicaoId
        self.user_api                   = user_api
        self.senha_api                  = senha_api

    def check_password (self,plaintext_password):

        return check_password_hash(self.password_hash,plaintext_password)

    def __repr__(self):

        return f"{self.userNome};"

## tabela de registro dos principais commits
class Log_Auto(db.Model):

    __tablename__ = 'log_auto'
    __table_args__ = {"schema": "Apoio"}

    id        = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime,nullable=False,default=datetime.now())
    user_id   = db.Column(db.Integer, db.ForeignKey('Apoio.User.id'),nullable=False)
    msg       = db.Column(db.String)


    def __init__(self, data_hora, user_id, msg):

        self.data_hora = data_hora
        self.user_id   = user_id
        self.msg       = msg

    def __repr__(self):

        return f"{self.data_hora};{self.user_id};{self.msg}"        

# unidades

class Unidades(db.Model):

    __tablename__ = 'Unidade'
    __table_args__ = {"schema": "dbo"}

    IdUnidade         = db.Column(db.BigInteger, primary_key = True)
    Sigla             = db.Column(db.String)
    Nome              = db.Column(db.String)
    Excluido          = db.Column(db.Boolean)
    IdUnidadeSuperior = db.Column(db.BigInteger)
    Codigo            = db.Column(db.String)

    def __init__(self, Sigla, Nome, Excluido, IdUnidadeSuperior,Codigo):

        self.Sigla             = Sigla
        self.Nome              = Nome
        self.Excluido          = Excluido
        self.IdUnidadeSuperior = IdUnidadeSuperior
        self.Codigo            = Codigo

    def __repr__ (self):
        return f"{self.Sigla};{self.Nome};{self.Excluido};{self.IdUnidadeSuperior};{self.Codigo}"



# View dos pactos para API 

class VW_Pactos(db.Model):

    __tablename__ = 'vw_pacto'
    __table_args__ = {"schema": "dbo"}

    id_pacto                = db.Column(db.Integer, primary_key = True)
    situacao                = db.Column(db.String)
    matricula_siape         = db.Column(db.String)
    cpf                     = db.Column(db.String)
    nome_participante       = db.Column(db.String)
    cod_unidade_exercicio   = db.Column(db.Integer)
    nome_unidade_exercicio  = db.Column(db.String)
    sigla_unidade_exercicio = db.Column(db.String)
    desc_situacao_pacto     = db.Column(db.String)
    modalidade_execucao     = db.Column(db.Integer)
    carga_horaria_semanal   = db.Column(db.Float)
    data_inicio             = db.Column(db.Date)
    data_fim                = db.Column(db.Date)
    carga_horaria_total     = db.Column(db.Float)
    data_interrupcao        = db.Column(db.Date)
    entregue_no_prazo       = db.Column(db.String)
    horas_homologadas       = db.Column(db.Float)

    def __init__(self, id_pacto, situacao, matricula_siape, cpf, nome_participante, cod_unidade_exercicio, nome_unidade_exercicio, sigla_unidade_exercicio, desc_situacao_pacto,
                       modalidade_execucao, carga_horaria_semanal, data_inicio, data_fim, carga_horaria_total, data_interrupcao, entregue_no_prazo,
                       horas_homologadas):

        self.id_pacto                = id_pacto
        self.situacao                = situacao
        self.matricula_siape         = matricula_siape
        self.cpf                     = cpf
        self.nome_participante       = nome_participante
        self.cod_unidade_exercicio   = cod_unidade_exercicio 
        self.nome_unidade_exercicio  = nome_unidade_exercicio
        self.sigla_unidade_exercicio = sigla_unidade_exercicio
        self.desc_situacao_pacto     = desc_situacao_pacto 
        self.modalidade_execucao     = modalidade_execucao
        self.carga_horaria_semanal   = carga_horaria_semanal
        self.data_inicio             = data_inicio
        self.data_fim                = data_fim
        self.carga_horaria_total     = carga_horaria_total
        self.data_interrupcao        = data_interrupcao
        self.entregue_no_prazo       = entregue_no_prazo
        self.horas_homologadas       = horas_homologadas

    def __repr__ (self):
        return f"{self.id_pacto}"

# View dos pactos para API 

class VW_Atividades_Pactos(db.Model):

    __tablename__ = 'vw_produto'
    __table_args__ = {"schema": "dbo"}  

    id                          = db.Column(db.BigInteger, primary_key = True)
    id_produto                  = db.Column(db.String)
    id_pacto                    = db.Column(db.String)
    id_atividade                = db.Column(db.String)
    nome_grupo_atividade        = db.Column(db.Integer)
    nome_atividade              = db.Column(db.String)
    faixa_complexidade          = db.Column(db.String)
    parametros_complexidade     = db.Column(db.String)
    tempo_presencial_estimado   = db.Column(db.Float)
    tempo_presencial_programado = db.Column(db.Float)
    tempo_presencial_executado  = db.Column(db.Float)
    tempo_teletrabalho_estimado   = db.Column(db.Float)
    tempo_teletrabalho_programado = db.Column(db.Float)
    tempo_teletrabalho_executado  = db.Column(db.Float)
    entrega_esperada              = db.Column(db.String)
    qtde_entregas                 = db.Column(db.Integer)
    qtde_entregas_efetivas        = db.Column(db.Integer)
    avaliacao                     = db.Column(db.Float)
    data_avaliacao                = db.Column(db.Date) 
    justificativa                 = db.Column(db.String)

    def __init__(self, id, id_produto, id_pacto, id_atividade, nome_grupo_atividade, nome_atividade, faixa_complexidade, parametros_complexidade, tempo_presencial_estimado,
                       tempo_presencial_programado, tempo_presencial_executado, tempo_teletrabalho_estimado, tempo_teletrabalho_programado, tempo_teletrabalho_executado,
                       entrega_esperada, qtde_entregas, qtde_entregas_efetivas, avaliacao, data_avaliacao, justificativa):

        self.id                          = id
        self.id_produto                  = id_produto
        self.id_pacto                    = id_pacto
        self.id_atividade                = id_atividade
        self.nome_grupo_atividade        = nome_grupo_atividade
        self.nome_atividade              = nome_atividade
        self.faixa_complexidade          = faixa_complexidade
        self.parametros_complexidade     = parametros_complexidade
        self.tempo_presencial_estimado   = tempo_presencial_estimado
        self.tempo_presencial_programado = tempo_presencial_programado
        self.tempo_presencial_executado  = tempo_presencial_executado
        self.tempo_teletrabalho_estimado   = tempo_teletrabalho_estimado
        self.tempo_teletrabalho_programado = tempo_teletrabalho_programado
        self.tempo_teletrabalho_executado  = tempo_teletrabalho_executado
        self.entrega_esperada              = entrega_esperada
        self.qtde_entregas                 = qtde_entregas
        self.qtde_entregas_efetivas        = qtde_entregas_efetivas
        self.avaliacao                     = avaliacao
        self.data_avaliacao                = data_avaliacao
        self.justificativa                 = justificativa

    def __repr__ (self):
        return f"{self.id_produto}"

        
