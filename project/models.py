"""
.. topic:: Modelos (tabelas nos bancos de dados)

    Os modelos são classes que definem a estrutura das tabelas dos bancos de dados.

    Os modelos de interesse do banco DBSISGP são os seguintes:

    * users: tabela dos usuários que podem executar o ApoioSisgp
    * log_auto: tabela de log dos principais commits
    * Unidades: as caixas que compóe a instituição.
    * Pessoas: pessoa da instituição
    * Situ_Pessoa: situção das pessoas na instituição
    * Tipo_Func_Pessoa: tipo de função exercida pela pessoa
    * Tipo_Vinculo_Pessoa: tipo de vínculo da pessoa
    * Feriados: tabela de feriados
    * Planos_de_Trabalho: tabela dos programas de gestão de cada unidade
    * catalogo_dominio: tabela do catálogo de domínios
    * unidade_ativ: tabela que relaciona unidade a atividades

    Abaixo seguem os Modelos e respectivos campos.
"""
# models.py
import locale
from project import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime, date


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

    def __init__(self,userNome,userEmail,plaintext_password,userAtivo,\
                 email_confirmation_sent_on=None):

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

    __tablename__ = 'unidade'
    __table_args__ = {"schema": "dbo"}

    unidadeId                = db.Column(db.BigInteger, primary_key = True)
    undSigla                 = db.Column(db.String)
    undDescricao             = db.Column(db.String)
    unidadeIdPai             = db.Column(db.BigInteger)
    tipoUnidadeId            = db.Column(db.BigInteger)
    situacaoUnidadeId        = db.Column(db.BigInteger)
    ufId                     = db.Column(db.String)
    undNivel                 = db.Column(db.Integer)
    tipoFuncaoUnidadeId      = db.Column(db.BigInteger)
    Email                    = db.Column(db.String)
    undCodigoSIORG           = db.Column(db.Integer)
    pessoaIdChefe           = db.Column(db.BigInteger)
    pessoaIdChefeSubstituto = db.Column(db.BigInteger)

    def __init__(self, undSigla, undDescricao, unidadeIdPai, tipoUnidadeId,
                 situacaoUnidadeId, ufId, undNivel, tipoFuncaoUnidadeId, Email, undCodigoSIORG,
                 pessoaIdChefe, pessoaIdChefeSubstituto):

        self.undSigla                  = undSigla
        self.undDescricao              = undDescricao
        self.unidadeIdPai              = unidadeIdPai
        self.tipoUnidadeId             = tipoUnidadeId
        self.situacaoUnidadeId         = situacaoUnidadeId
        self.ufId                      = ufId
        self.undNivel                  = undNivel
        self.tipoFuncaoUnidadeId       = tipoFuncaoUnidadeId
        self.Email                     = Email
        self.undCodigoSIORG            = undCodigoSIORG
        self.pessoaIdChefe            = pessoaIdChefe
        self.pessoaIdChefeSubstituto  = pessoaIdChefeSubstituto

    def __repr__ (self):
        return f"{self.undSigla};{self.undDescricao};{self.unidadeIdPai};\
                 {self.tipoUnidadeId};{self.situacaoUnidadeId};{self.ufId};{self.undNivel};\
                 {self.tipoFuncaoUnidadeId};{self.Email};{self.undCodigoSIORG};\
                 {self.pessoaIdChefe};{self.pessoaIdChefeSubstituto};"

# pessoas

class Pessoas(db.Model):

    __tablename__ = 'pessoa'
    __table_args__ = {"schema": "dbo"}

    pessoaId          = db.Column(db.BigInteger, primary_key = True)
    pesNome           = db.Column(db.String)
    pesCPF            = db.Column(db.String)
    pesDataNascimento = db.Column(db.Date)
    pesMatriculaSiape = db.Column(db.String)
    pesEmail          = db.Column(db.String)
    unidadeId         = db.Column(db.BigInteger)
    tipoFuncaoId      = db.Column(db.BigInteger)
    cargaHoraria      = db.Column(db.Integer)
    situacaoPessoaId  = db.Column(db.BigInteger)
    tipoVinculoId     = db.Column(db.BigInteger)

    def __init__(self, pesNome, pesCPF, pesDataNascimento, pesMatriculaSiape, pesEmail, unidadeId,
                 tipoFuncaoId, cargaHoraria, situacaoPessoaId, tipoVinculoId):

        self.pesNome           = pesNome
        self.pesCPF            = pesCPF
        self.pesDataNascimento = pesDataNascimento
        self.pesMatriculaSiape = pesMatriculaSiape
        self.pesEmail          = pesEmail
        self.unidadeId         = unidadeId
        self.tipoFuncaoId      = tipoFuncaoId
        self.cargaHoraria      = cargaHoraria
        self.situacaoPessoaId  = situacaoPessoaId
        self.tipoVinculoId     = tipoVinculoId

    def __repr__ (self):
        return f"{self.pesNome};{self.pesCPF};{self.pesDataNascimento};\
                 {self.pesMatriculaSiape};{self.pesEmail};{self.unidadeId};\
                 {self.tipoFuncaoId};{self.cargaHoraria};{self.situacaoPessoaId};{self.tipoVinculoId};"

# situação pessoa

class Situ_Pessoa(db.Model):

    __tablename__ = 'SituacaoPessoa'
    __table_args__ = {"schema": "dbo"}

    situacaoPessoaId = db.Column(db.BigInteger, primary_key = True, autoincrement=False)
    spsDescricao     = db.Column(db.String)

    def __init__(self, situacaoPessoaId, spsDescricao):

        self.situacaoPessoaId = situacaoPessoaId
        self.spsDescricao     = spsDescricao

    def __repr__ (self):
        return f"{self.spsDescricao};"

# tipo função pessoa

class Tipo_Func_Pessoa(db.Model):

    __tablename__ = 'TipoFuncao'
    __table_args__ = {"schema": "dbo"}

    tipoFuncaoId        = db.Column(db.BigInteger, primary_key = True, autoincrement=False)
    tfnDescricao       = db.Column(db.String)
    tfnCodigoFuncao    = db.Column(db.String)
    tfnIndicadorChefia = db.Column(db.Boolean)

    def __init__(self, tipoFuncaoId, tfnDescricao, tfnCodigoFuncao, tfnIndicadorChefia):

        self.tipoFuncaoId = tipoFuncaoId
        self.tfnDescricao = tfnDescricao
        self.tfnCodigoFuncao = tfnCodigoFuncao
        self.tfnIndicadorChefia = tfnIndicadorChefia

    def __repr__ (self):
        return f"{self.tfnDescricao};{self.tfnCodigoFuncao};{self.tfnIndicadorChefia};"

# tipo vínculo pessoa

class Tipo_Vinculo_Pessoa(db.Model):

    __tablename__ = 'TipoVinculo'
    __table_args__ = {"schema": "dbo"}

    tipoVinculoId = db.Column(db.BigInteger, primary_key = True, autoincrement=False)
    tvnDescricao  = db.Column(db.String)

    def __init__(self, tipoVinculoId, tvnDescricao):

        self.tipoVinculoId = tipoVinculoId
        self.tvnDescricao = tvnDescricao

    def __repr__ (self):
        return f"{self.tvnDescricao};"            

# feriados

class Feriados(db.Model):

    __tablename__ = 'Feriado'
    __table_args__ = {"schema": "dbo"}

    feriadoId    = db.Column(db.BigInteger, primary_key = True)
    ferData      = db.Column(db.Date)
    ferFixo      = db.Column(db.Boolean)
    ferDescricao = db.Column(db.String)
    ufId         = db.Column(db.String)

    def __init__(self, ferData, ferFixo, ferDescricao, ufId):

        self.ferData      = ferData
        self.ferFixo      = ferFixo
        self.ferDescricao = ferDescricao
        self.ufId         = ufId

    def __repr__ (self):
        return f"{self.ferData};{self.ferFixo};{self.ferDescricao};{self.ufId};"

# Planos de Trabalho

class Planos_de_Trabalho(db.Model):

    __tablename__ = 'PlanoTrabalho'
    __table_args__ = {"schema": "ProgramaGestao"}

    planoTrabalhoId      = db.Column(db.String, primary_key = True)
    unidadeId            = db.Column(db.BigInteger)
    dataInicio           = db.Column(db.Date)
    dataFim              = db.Column(db.Date)
    situacaoId           = db.Column(db.Integer)
    avaliacaoId          = db.Column(db.String)
    tempoComparecimento  = db.Column(db.Integer)
    totalServidoresSetor = db.Column(db.Integer)
    tempoFaseHabilitacao = db.Column(db.Integer)
    termoAceite          = db.Column(db.String)

    def __init__(self, unidadeId, dataInicio, dataFim, situacaoId, avaliacaoId, tempoComparecimento,
                 totalServidoresSetor, tempoFaseHabilitacao, termoAceite):

        self.unidadeId            = unidadeId
        self.dataInicio           = dataInicio
        self.dataFim              = dataFim
        self.situacaoId           = situacaoId
        self.avaliacaoId          = avaliacaoId
        self.tempoComparecimento  = tempoComparecimento
        self.totalServidoresSetor = totalServidoresSetor
        self.tempoFaseHabilitacao = tempoFaseHabilitacao
        self.termoAceite          = termoAceite

    def __repr__ (self):
        return f"{self.unidadeId};{self.dataInicio};{self.dataFim};\
                 {self.situacaoId};{self.avaliacaoId};{self.tempoComparecimento};\
                 {self.totalServidoresSetor};{self.tempoFaseHabilitacao};{self.termoAceite};"

# Pactos de Trabalho

class Pactos_de_Trabalho(db.Model):

    __tablename__ = 'PactoTrabalho'
    __table_args__ = {"schema": "ProgramaGestao"}

    pactoTrabalhoId          = db.Column(db.String, primary_key = True)
    planoTrabalhoId          = db.Column(db.String)
    unidadeId                = db.Column(db.BigInteger)
    pessoaId                 = db.Column(db.BigInteger)
    dataInicio               = db.Column(db.Date)
    dataFim                  = db.Column(db.Date)
    formaExecucaoId          = db.Column(db.Integer)
    situacaoId               = db.Column(db.Integer)
    tempoComparecimento      = db.Column(db.Integer)
    cargaHorariaDiaria       = db.Column(db.Integer)
    percentualExecucao       = db.Column(db.Float)
    relacaoPrevistoRealizado = db.Column(db.Float)
    avaliacaoId              = db.Column(db.String)
    tempoTotalDisponivel     = db.Column(db.Integer)
    termoAceite              = db.Column(db.String)

    def __init__(self, planoTrabalhoId,unidadeId,pessoaId,dataInicio,dataFim,formaExecucaoId,
                 situacaoId,tempoComparecimento,cargaHorariaDiaria,percentualExecucao,relacaoPrevistoRealizado,
                 avaliacaoId,tempoTotalDisponivel,termoAceite):

        self.planoTrabalhoId      = planoTrabalhoId
        self.unidadeId            = unidadeId
        self.pessoaId             = pessoaId
        self.dataInicio           = dataInicio
        self.dataFim              = dataFim
        self.formaExecucaoId      = formaExecucaoId
        self.situacaoId           = situacaoId
        self.tempoComparecimento  = tempoComparecimento
        self.cargaHorariaDiaria   = cargaHorariaDiaria
        self.percentualExecucao   = percentualExecucao
        self.relacaoPrevistoRealizado = relacaoPrevistoRealizado
        self.avaliacaoId          = avaliacaoId
        self.tempoComparecimento  = tempoComparecimento
        self.tempoTotalDisponivel = tempoTotalDisponivel
        self.termoAceite          = termoAceite

    def __repr__ (self):
        return f"{self.planoTrabalhoId};{self.unidadeId};{self.pessoaId};{self.dataInicio};{self.dataFim};\
                 {self.formaExecucaoId};{self.situacaoId};\
                 {self.tempoComparecimento};{self.cargaHorariaDiaria};\
                 {self.percentualExecucao};{self.relacaoPrevistoRealizado};{self.avaliacaoId};\
                 {self.tempoComparecimento};{self.tempoTotalDisponivel};{self.termoAceite};"

# catálogo de domínios

class catdom(db.Model):

    __tablename__ = 'CatalogoDominio'
    __table_args__ = {"schema": "dbo"}

    catalogoDominioId   = db.Column(db.Integer, primary_key = True)
    classificacao       = db.Column(db.String)
    descricao           = db.Column(db.String)
    ativo               = db.Column(db.Boolean)

    def __init__(self, catalogoDominioId, classificacao, descricao, ativo):

        self.catalogoDominioId = catalogoDominioId
        self.classificacao     = classificacao
        self.descricao         = descricao
        self.ativo             = ativo

    def __repr__ (self):
        return f"{self.catalogoDominioId};{self.classificacao};{self.descricao};{self.ativo};"

# catálogo (relaciona atividades às unidades)

class unidade_ativ(db.Model):

    __tablename__ = 'Catalogo'
    __table_args__ = {"schema": "ProgramaGestao"}

    catalogoId = db.Column(db.String, primary_key = True)
    unidadeId  = db.Column(db.Integer)

    def __init__(self, catalogoId, unidadeId):

        self.catalogoId = catalogoId
        self.unidadeId  = unidadeId

    def __repr__ (self):
        return f"{self.catalogoId};{self.unidadeId};"
