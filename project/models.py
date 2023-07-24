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
    * Pactos_de_Trabalho:
    * catalogo_dominio: tabela do catálogo de domínios
    * unidade_ativ: tabela que relaciona unidade a atividades
    * cat_item_cat:
    * Atividades:
    * Pactos_de_Trabalho_Atividades:

    Abaixo seguem os Modelos e respectivos campos.
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

class jobs(db.Model):

    __tablename__ = 'apscheduler_jobs'
    __table_args__ = {"schema": "dbo"}

    id             = db.Column(db.String,primary_key=True)
    next_run_time  = db.Column(db.Float)
    job_state      = db.Column(db.String)
    
    def __init__(self, id,next_run_time, job_state):

        self.id            = id
        self.next_run_time = next_run_time
        self.mjob_statesg  = job_state

    def __repr__(self):

        return f"{self.id};{self.next_run_time}" 

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

    def __init__(self,userNome,userEmail,plaintext_password,userAtivo,userEnvia,email_confirmation_sent_on=None):

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

# view que monta a sigla completa das unidades

class VW_Unidades(db.Model):

    __tablename__ = 'VW_UnidadeSiglaCompleta'
    __table_args__ = {"schema": "dbo"}

    unidadeId           = db.Column(db.BigInteger, primary_key = True)
    undSigla            = db.Column(db.String)
    unidadeIdPai        = db.Column(db.String)
    tipoUnidadeId       = db.Column(db.BigInteger)
    situacaoUnidadeId   = db.Column(db.BigInteger)
    ufId                = db.Column(db.String)
    undNivel            = db.Column(db.Integer)
    tipoFuncaoUnidadeId = db.Column(db.BigInteger)
    undSiglaCompleta    = db.Column(db.String)
    Email               = db.Column(db.String)
    undCodigoSIORG      = db.Column(db.Integer)

    def __init__(self, unidadeId,undSigla,undDescricao,unidadeIdPai,tipoUnidadeId,situacaoUnidadeId,ufId,
                       undNivel,tipoFuncaoUnidadeId,undSiglaCompleta,Email,undCodigoSIORG):

        self.unidadeId           = unidadeId
        self.undSigla            = undSigla
        self.undDescricao        = undDescricao
        self.unidadeIdPai        = unidadeIdPai
        self.tipoUnidadeId       = tipoUnidadeId
        self.situacaoUnidadeId   = situacaoUnidadeId
        self.ufId                = ufId
        self.undNivel            = undNivel
        self.tipoFuncaoUnidadeId = tipoFuncaoUnidadeId
        self.undSiglaCompleta    = undSiglaCompleta
        self.Email               = Email
        self.undCodigoSIORG      = undCodigoSIORG


    def __repr__ (self):
        return f"{self.undSiglaCompleta}"



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

# Atividades de Planos de Trabalho

class Planos_de_Trabalho_Ativs(db.Model):

    __tablename__ = 'PlanoTrabalhoAtividade'
    __table_args__ = {"schema": "ProgramaGestao"}

    planoTrabalhoAtividadeId = db.Column(db.String, primary_key = True)
    planoTrabalhoId          = db.Column(db.String)
    modalidadeExecucaoId     = db.Column(db.Integer)
    quantidadeColaboradores  = db.Column(db.Integer)
    descricao                = db.Column(db.String)   

    def __init__(self, planoTrabalhoAtividadeId, planoTrabalhoId, modalidadeExecucaoId,
                 quantidadeColaboradores, descricao):

        self.planoTrabalhoAtividadeId = planoTrabalhoAtividadeId
        self.planoTrabalhoId          = planoTrabalhoId
        self.modalidadeExecucaoId     = modalidadeExecucaoId
        self.quantidadeColaboradores  = quantidadeColaboradores
        self.descricao                = descricao   

    def __repr__ (self):
        return f"{self.planoTrabalhoAtividadeId};{self.planoTrabalhoId};{self.modalidadeExecucaoId};\
                 {self.quantidadeColaboradores};{self.descricao}"

# Items de Atividades de Planos de Trabalho

class Planos_de_Trabalho_Ativs_Items(db.Model):

    __tablename__ = 'PlanoTrabalhoAtividadeItem'
    __table_args__ = {"schema": "ProgramaGestao"}

    planoTrabalhoAtividadeItemId = db.Column(db.String, primary_key = True)
    planoTrabalhoAtividadeId     = db.Column(db.String)
    itemCatalogoId               = db.Column(db.String)

    def __init__(self, planoTrabalhoAtividadeId, itemCatalogoId):

        self.planoTrabalhoAtividadeId = planoTrabalhoAtividadeId
        self.itemCatalogoId           = itemCatalogoId

    def __repr__ (self):
        return f"{self.planoTrabalhoAtividadeId};{self.itemCatalogoId}"   


# HIstórico de Planos de Trabalho

class Planos_de_Trabalho_Hist(db.Model):

    __tablename__ = 'PlanoTrabalhoHistorico'
    __table_args__ = {"schema": "ProgramaGestao"}

    planoTrabalhoHistoricoId = db.Column(db.String, primary_key = True)
    planoTrabalhoId          = db.Column(db.String)
    situacaoId               = db.Column(db.Integer)
    observacoes              = db.Column(db.String)
    responsavelOperacao      = db.Column(db.String)   
    DataOperacao             = db.Column(db.Date)

    def __init__(self, planoTrabalhoId, situacaoId, observacoes,
                 responsavelOperacao, DataOperacao):

        self.planoTrabalhoId     = planoTrabalhoId
        self.situacaoId          = situacaoId
        self.observacoes         = observacoes
        self.responsavelOperacao = responsavelOperacao
        self.DataOperacao        = DataOperacao   

    def __repr__ (self):
        return f"{self.planoTrabalhoId};{self.situacaoId};{self.observacoes};\
                 {self.responsavelOperacao};{self.DataOperacao}"
                 

# PG (planotrabalho) atividade candidato

class Atividade_Candidato(db.Model):

    __tablename__ = 'PlanoTrabalhoAtividadeCandidato'
    __table_args__ = {"schema": "ProgramaGestao"}   

    planoTrabalhoAtividadeCandidatoId = db.Column(db.String, primary_key = True)
    planoTrabalhoAtividadeId          = db.Column(db.String)
    pessoaId                          = db.Column(db.Integer)
    situacaoId                        = db.Column(db.Integer)
    termoAceite                       = db.Column(db.String)

    def __init__(self,planoTrabalhoAtividadeCandidatoId,planoTrabalhoAtividadeId,pessoaId,situacaoId,termoAceite):
        
        self.planoTrabalhoAtividadeCandidatoId = planoTrabalhoAtividadeCandidatoId
        self.planoTrabalhoAtividadeId = planoTrabalhoAtividadeId
        self.pessoaId                 = pessoaId
        self.situacaoId               = situacaoId
        self.termoAceite              = termoAceite

    def __repr__ (self):
        return f"{self.planoTrabalhoAtividadeCandidatoId};{self.planoTrabalhoAtividadeId};{self.pessoaId};{self.situacaoId};{self.termoAceite}"              


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

    catalogoDominioId   = db.Column(db.Integer, primary_key = True, autoincrement=False)
    classificacao       = db.Column(db.String)
    descricao           = db.Column(db.String)
    ativo               = db.Column(db.Boolean)

    def __init__(self, catalogoDominioId, classificacao, descricao, ativo):

        self.catalogoDominioId = catalogoDominioId
        self.classificacao     = classificacao
        self.descricao         = descricao
        self.ativo             = ativo

    def __repr__ (self):
        return f"{self.classificacao};{self.descricao};{self.ativo};"

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

# catálogo item catálogo (intermediárna no relacionamento atividades - unidades)

class cat_item_cat(db.Model):

    __tablename__ = 'CatalogoItemCatalogo'
    __table_args__ = {"schema": "ProgramaGestao"}

    catalogoItemCatalogoId = db.Column(db.String, primary_key = True)
    catalogoId             = db.Column(db.String)
    itemCatalogoId         = db.Column(db.String)

    def __init__(self, catalogoItemCatalogoId, catalogoId, itemCatalogoId):

        self.catalogoItemCatalogoId = catalogoItemCatalogoId
        self.catalogoId             = catalogoId
        self.itemCatalogoId         = itemCatalogoId

    def __repr__ (self):
        return f"{self.catalogoItemCatalogoId};{self.catalogoId};{self.itemCatalogoId};"

# atividades 

class Atividades(db.Model):

    __tablename__ = 'ItemCatalogo'
    __table_args__ = {"schema": "ProgramaGestao"}

    itemCatalogoId        = db.Column(db.String, primary_key = True)
    titulo                = db.Column(db.String)
    calculoTempoId        = db.Column(db.Integer)
    permiteRemoto         = db.Column(db.Boolean)
    tempoPresencial       = db.Column(db.Numeric(4,1))
    tempoRemoto           = db.Column(db.Numeric(4,1))
    descricao             = db.Column(db.String)
    complexidade          = db.Column(db.String)
    definicaoComplexidade = db.Column(db.String)
    entregasEsperadas     = db.Column(db.String)

    def __init__(self, itemCatalogoId, titulo, calculoTempoId, permiteRemoto, tempoPresencial, tempoRemoto, 
                descricao, complexidade, definicaoComplexidade, entregasEsperadas):

        self.itemCatalogoId        = itemCatalogoId
        self.titulo                = titulo
        self.calculoTempoId        = calculoTempoId
        self.permiteRemoto         = permiteRemoto
        self.tempoPresencial       = tempoPresencial
        self.tempoRemoto           = tempoRemoto
        self.descricao             = descricao
        self.complexidade          = complexidade
        self.definicaoComplexidade = definicaoComplexidade
        self.entregasEsperadas     = entregasEsperadas

    def __repr__ (self):
        return f"{self.itemCatalogoId};{self.titulo};{self.calculoTempoId};{self.permiteRemoto};{self.tempoPresencial};\
                {self.tempoRemoto};{self.descricao};{self.complexidade};{self.definicaoComplexidade};\
                {self.entregasEsperadas};"

# Atividades de Pactos de Trabalho 

class Pactos_de_Trabalho_Atividades(db.Model):

    __tablename__ = 'PactoTrabalhoAtividade'
    __table_args__ = {"schema": "ProgramaGestao"}

    pactoTrabalhoAtividadeId = db.Column(db.String, primary_key = True)
    pactoTrabalhoId          = db.Column(db.String)
    itemCatalogoId           = db.Column(db.String)
    quantidade               = db.Column(db.Integer)
    tempoPrevistoPorItem     = db.Column(db.Numeric(4,1))
    tempoPrevistoTotal       = db.Column(db.Numeric(4,1))
    dataInicio               = db.Column(db.Date)
    dataFim                  = db.Column(db.Date)
    tempoRealizado           = db.Column(db.Numeric(4,1))
    situacaoId               = db.Column(db.Integer)
    descricao                = db.Column(db.String)
    tempoHomologado          = db.Column(db.Numeric(4,1))
    nota                     = db.Column(db.Numeric(4,2))
    justificativa            = db.Column(db.String)
    consideracoesConclusao   = db.Column(db.String)
    modalidadeExecucaoId     = db.Column(db.Integer)

    def __init__(self,pactoTrabalhoId,itemCatalogoId,quantidade,tempoPrevistoPorItem,tempoPrevistoTotal,
                dataInicio,dataFim,tempoRealizado,situacaoId,descricao,tempoHomologado,nota,justificativa,
                consideracoesConclusao,modalidadeExecucaoId):

        self.pactoTrabalhoId        = pactoTrabalhoId
        self.itemCatalogoId         = itemCatalogoId
        self.quantidade             = quantidade
        self.tempoPrevistoPorItem   = tempoPrevistoPorItem
        self.tempoPrevistoTotal     = tempoPrevistoTotal
        self.dataInicio             = dataInicio
        self.dataFim                = dataFim
        self.tempoRealizado         = tempoRealizado
        self.situacaoId             = situacaoId
        self.descricao              = descricao
        self.tempoHomologado        = tempoHomologado 
        self.nota                   = nota
        self.justificativa          = justificativa
        self.consideracoesConclusao = consideracoesConclusao
        self.modalidadeExecucaoId   = modalidadeExecucaoId

    def __repr__ (self):
        return f"{self.pactoTrabalhoId};{self.itemCatalogoId};{self.quantidade};{self.tempoPrevistoPorItem};\
                 {self.tempoPrevistoTotal};{self.dataInicio};{self.dataFim};{self.tempoRealizado};\
                 {self.situacaoId};{self.descricao};{self.tempoHomologado};\
                 {self.nota};{self.justificativa};{self.consideracoesConclusao};{self.modalidadeExecucaoId}"

# Solicitações nos Pactos de Trabalho 

class Pactos_de_Trabalho_Solic(db.Model):

    __tablename__ = 'PactoTrabalhoSolicitacao'
    __table_args__ = {"schema": "ProgramaGestao"}

    pactoTrabalhoSolicitacaoId = db.Column(db.String, primary_key = True)
    pactoTrabalhoId            = db.Column(db.String)
    tipoSolicitacaoId          = db.Column(db.Integer)
    dataSolicitacao            = db.Column(db.Date)
    solicitante                = db.Column(db.String)
    dadosSolicitacao           = db.Column(db.String)
    observacoesSolicitante     = db.Column(db.String)
    analisado                  = db.Column(db.Boolean)
    dataAnalise                = db.Column(db.Date)
    analista                   = db.Column(db.String)
    aprovado                   = db.Column(db.Boolean)
    observacoesAnalista        = db.Column(db.String)

    def __init__(self,pactoTrabalhoSolicitacaoId,pactoTrabalhoId,tipoSolicitacaoId,dataSolicitacao,solicitante,dadosSolicitacao,
                observacoesSolicitante,analisado,dataAnalise,analista,aprovado,observacoesAnalista):

        self.pactoTrabalhoSolicitacaoId = pactoTrabalhoSolicitacaoId
        self.pactoTrabalhoId            = pactoTrabalhoId
        self.tipoSolicitacaoId          = tipoSolicitacaoId
        self.dataSolicitacao            = dataSolicitacao
        self.solicitante                = solicitante
        self.dadosSolicitacao           = dadosSolicitacao
        self.observacoesSolicitante     = observacoesSolicitante
        self.analisado                  = analisado
        self.dataAnalise                = dataAnalise
        self.analista                   = analista
        self.aprovado                   = aprovado
        self.observacoesAnalista        = observacoesAnalista 

    def __repr__ (self):
        return f"{self.pactoTrabalhoSolicitacaoId};{self.pactoTrabalhoId};{self.tipoSolicitacaoId};{self.dataSolicitacao};{self.solicitante};\
                 {self.dadosSolicitacao};{self.observacoesSolicitante};{self.analisado};{self.dataAnalise};\
                 {self.analista};{self.aprovado};{self.observacoesAnalista}" 


# View dos pactos para API 

class VW_Pactos(db.Model):

    __tablename__ = 'VW_PACTO'
    __table_args__ = {"schema": "dbo"}

    id_pacto                = db.Column(db.String, primary_key = True)
    situacao                = db.Column(db.String)
    matricula_siape         = db.Column(db.String)
    cpf                     = db.Column(db.String)
    nome_participante       = db.Column(db.String)
    cod_unidade_exercicio   = db.Column(db.Integer)
    nome_unidade_exercicio  = db.Column(db.String)
    sigla_unidade_exercicio = db.Column(db.String)
    desc_situacao_pacto     = db.Column(db.String)
    modalidade_execucao     = db.Column(db.Integer)
    carga_horaria_semanal   = db.Column(db.Integer)
    data_inicio             = db.Column(db.Date)
    data_fim                = db.Column(db.Date)
    carga_horaria_total     = db.Column(db.Integer)
    data_interrupcao        = db.Column(db.Date)
    entregue_no_prazo       = db.Column(db.Integer)
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

    __tablename__ = 'VW_PRODUTO'
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

        
