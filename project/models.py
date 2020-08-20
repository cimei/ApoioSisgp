"""
.. topic:: Modelos (tabelas nos bancos de dados)

    Os modelos são classes que definem a estrutura das tabelas dos bancos de dados.

    Este aplicativo utiliza dois bancos de dados. Um para os dados referentes às demandas e o outro para os dados de
    Acordos e Convênios.

    O banco de dados de demandas possui os modelos:

    * Tipos_Demanda: tipos de demanda
    * Plano_Trabalho: atividades da coordenação por usuário
    * Demanda: dados das demandas.
    * Providencia: dados das proviências tomadas para cada demanda.
    * Despacho: dados dos despachos, ou encaminhamentos, efetuados pela chefia imediata em cada demanda.
    * User: dados dos usuários registrados.

    O banco de dados de Acordos e Convênios tem os modelos:

    * RefCargaPDCTR: datas de referência das cargas de dados realizadas, conforme planilhas COSAO.
    * PagamentosPDCTR: dados brutos da planinha COSAO.
    * Bolsa: dados das bolsas utilizada no PDCTR.
    * Programa_CNPq: programas do CNPq, normalmente utilizados nos Acordos.
    * Acordo: dados dos acordos celebrados.
    * ProcessoMae: dados dos processos mãe (projetos) criados para permitir a implemtação de bolsas.
    * Programa_Interesse: programas tratados na coordenação
    * DadosSEI: dados básicos dos convênios e respectivos processos sei.
    * Chamadas: dados das chamadas homologadas pelo CNPq
    * Programa: programas importados do SICONV a partir de lista de interesse copes
    * Proposta: propostas cadastradas no SICONV a partir dos programas selecionados
    * Convenio: convênios cadastrados no SICONV a partir das propostas selecionadas
    * Pagamento: relação dos pagamento efetuados pela convenente, aqui são armazemados os dados agregados por recebedor
    * Empenho: empenhos realizados conforme o SICONV
    * Desembolso: desembolsost realizados conforme o SICONV
    * Coords: coordenações técnicas
    * RefSICONV: data da carga SICONV
    * MSG_Siconv: mensagens do siconv

    Abaixo seguem os Modelos e respectivos campos.
"""
# models.py
import locale
from project import db,login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime, date
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


    ##########################################################################################
    ##  banco acordos_conv                                                                  ##
    ##########################################################################################


## tabela que guarda as datas de referência em que as planilhas da COSAO foram geradas
class RefCargaPDCTR (db.Model):

    __tablename__ = "ref_pag_pdctr"

    id       = db.Column(db.Integer,primary_key=True)
    data_ref = db.Column(db.Date)

    def __init__ (self,data_ref):

        self.data_ref = data_ref

    def __repr__ (self):
        return f"{self.data_ref}"

## tabela com os dados brutos (colunas selecionadas da planilha enviada pela COSAO)
class PagamentosPDCTR (db.Model):

    __tablename__ = "pagamentospdctr"

    id                = db.Column(db.Integer,primary_key=True)
    processo          = db.Column(db.String)
    nome              = db.Column(db.String)
    sexo_proc_filho   = db.Column(db.String)
    cpf               = db.Column(db.String)
    situ_filho        = db.Column(db.String)
    data_situ_filho   = db.Column(db.Date)
    inic_filho        = db.Column(db.Date)
    term_filho        = db.Column(db.Date)
    proc_mae          = db.Column(db.String)
    inic_mae          = db.Column(db.Date)
    term_mae          = db.Column(db.Date)
    titu_proc_filho   = db.Column(db.String)
    nome_chamada      = db.Column(db.String)
    modalidade        = db.Column(db.String)
    nivel             = db.Column(db.String)
    cod_programa      = db.Column(db.String)
    grande_area       = db.Column(db.String)
    area_conhecimento = db.Column(db.String)
    sigla_inst        = db.Column(db.String)
    uf_inst           = db.Column(db.String)
    cidade_inst       = db.Column(db.String)
    data_pagamento    = db.Column(db.Date)
    tipo_pagamento    = db.Column(db.String)
    valor_pago        = db.Column(db.Float)

    def __init__ (self,processo, nome, sexo_proc_filho, cpf, situ_filho, data_situ_filho, inic_filho, term_filho,
                  proc_mae, inic_mae, term_mae, titu_proc_filho, nome_chamada, modalidade, nivel, cod_programa, grande_area,
                  area_conhecimento, sigla_inst, uf_inst, cidade_inst, data_pagamento, tipo_pagamento, valor_pago):

        self.processo          = processo
        self.nome              = nome
        self.sexo_proc_filho   = sexo_proc_filho
        self.cpf               = cpf
        self.situ_filho        = situ_filho
        self.data_situ_filho   = data_situ_filho
        self.inic_filho        = inic_filho
        self.term_filho        = term_filho
        self.proc_mae          = proc_mae
        self.inic_mae          = inic_mae
        self.term_mae          = term_mae
        self.titu_proc_filho   = titu_proc_filho
        self.nome_chamada      = nome_chamada
        self.modalidade        = modalidade
        self.nivel             = nivel
        self.cod_programa      = cod_programa
        self.grande_area       = grande_area
        self.area_conhecimento = area_conhecimento
        self.sigla_inst        = sigla_inst
        self.uf_inst           = uf_inst
        self.cidade_inst       = cidade_inst
        self.data_pagamento    = data_pagamento
        self.tipo_pagamento    = tipo_pagamento
        self.valor_pago        = valor_pago

    def __repr__ (self):
        return f"{self.processo};{self.nome};{self.sexo_proc_filho};{self.cpf};{self.situ_filho};{self.data_situ_filho};{self.inic_filho};\
                 {self.term_filho};{self.proc_mae};{self.inic_mae};{self.term_mae};{self.titu_proc_filho};{self.nome_chamada};\
                 {self.modalidade};{self.nivel};{self.cod_programa};{self.grande_area};{self.area_conhecimento};{self.sigla_inst};\
                 {self.uf_inst};{self.cidade_inst};{self.data_pagamento};{self.tipo_pagamento};{self.valor_pago}"


#
## tabela com as modalidades e valores de cada bolsa
class Processo_Filho (db.Model):

    __tablename__ = 'processo_filho'

    id                = db.Column(db.Integer,primary_key = True)
    cod_programa      = db.Column(db.String)
    nome_chamada      = db.Column(db.String)
    proc_mae          = db.Column(db.String)
    processo          = db.Column(db.String)
    nome              = db.Column(db.String)
    cpf               = db.Column(db.String)
    modalidade        = db.Column(db.String)
    nivel             = db.Column(db.String)
    situ_filho        = db.Column(db.String)
    inic_filho        = db.Column(db.Date)
    term_filho        = db.Column(db.Date)
    mens_pagas        = db.Column(db.Integer)
    pago_total        = db.Column(db.Float)
    valor_apagar      = db.Column(db.Float)
    mens_apagar       = db.Column(db.Integer)
    dt_ult_pag        = db.Column(db.Date)


    def __init__ (self,cod_programa,nome_chamada,proc_mae,processo, nome,cpf,modalidade, nivel, situ_filho,
                  inic_filho, term_filho,mens_pagas,pago_total,valor_apagar,mens_apagar,dt_ult_pag):
        self.cod_programa      = cod_programa
        self.nome_chamada      = nome_chamada
        self.proc_mae          = proc_mae
        self.processo          = processo
        self.nome              = nome
        self.cpf               = cpf
        self.modalidade        = modalidade
        self.nivel             = nivel
        self.situ_filho        = situ_filho
        self.inic_filho        = inic_filho
        self.term_filho        = term_filho
        self.mens_pagas        = mens_pagas
        self.pago_total        = pago_total
        self.valor_apagar      = valor_apagar
        self.mens_apagar       = mens_apagar
        self.dt_ult_pag        = dt_ult_pag

    def __repr__ (self):
        return f"{self.processo};{self.nome};{self.modalidade};{self.nivel}"
#
## tabela com as modalidades e valores de cada bolsa
class Processo_Mae (db.Model):

    __tablename__ = 'processo_mae'

    id                = db.Column(db.Integer,primary_key = True)
    cod_programa      = db.Column(db.String)
    nome_chamada      = db.Column(db.String)
    proc_mae          = db.Column(db.String)
    inic_mae          = db.Column(db.Date)
    term_mae          = db.Column(db.Date)

    def __init__ (self,cod_programa,nome_chamada,proc_mae,
                  inic_mae, term_mae):
        self.cod_programa      = cod_programa
        self.nome_chamada      = nome_chamada
        self.proc_mae          = proc_mae
        self.inic_mae          = inic_mae
        self.term_mae          = term_mae

    def __repr__ (self):
        return f"{self.proc_mae};{self.inic_mae};{self.term_mae}"

#

## tabela com as modalidades e valores de cada bolsa
class Bolsa (db.Model):

    __tablename__ = 'bolsas'

    id          = db.Column(db.Integer,primary_key = True)
    mod_niv     = db.Column(db.String,nullable=False)
    mensalidade = db.Column(db.Float)
    auxilio     = db.Column(db.Float)


    def __init__ (self,mod_niv,mensalidade,auxilio):
        self.mod_niv     = mod_niv
        self.mensalidade = mensalidade
        self.auxilio     = auxilio

    def __repr__ (self):
        return f"Bolsa {self.mod_niv} com R$ {self.mensalidade} de mensalidade e R$ {self.auxílio} de auxílios"

#
# programa do CNPq - Utilizado para Acordos

class Programa_CNPq(db.Model):

    __tablename__ = 'programa_cnpq'

    ID_PROGRAMA    = db.Column(db.Integer, primary_key = True)
    COD_PROGRAMA   = db.Column(db.String)
    NOME_PROGRAMA  = db.Column(db.String)
    SIGLA_PROGRAMA = db.Column(db.String)
    COORD          = db.Column(db.String)

    def __init__(self, COD_PROGRAMA, NOME_PROGRAMA,SIGLA_PROGRAMA,COORD):
        self.COD_PROGRAMA    = COD_PROGRAMA
        self.NOME_PROGRAMA   = NOME_PROGRAMA
        self.SIGLA_PROGRAMA  = SIGLA_PROGRAMA
        self.COORD           = COORD

    def __repr__ (self):
        return f"{self.COD_PROGRAMA};{self.NOME_PROGRAMA};{self.SIGLA_PROGRAMA};{self.COORD}"

# dados dos vários acordos
class Acordo(db.Model):

    __tablename__ = 'acordos'

    id               = db.Column(db.Integer,primary_key=True)
    nome             = db.Column(db.String)
    sei              = db.Column(db.String)
    epe              = db.Column(db.String)
    uf               = db.Column(db.String)
    data_inicio      = db.Column(db.Date)
    data_fim         = db.Column(db.Date)
    valor_cnpq       = db.Column(db.Float)
    valor_epe        = db.Column(db.Float)
    programa_cnpq    = db.Column(db.String)

    #AcordoEpeEdic = db.relationship('ProcessoMae', primaryjoin="_and(ProcessoMae.epe==Acordo.epe, ProcessoMae.acordo_nome=Acordo.nome)")

    def __init__(self,nome,sei,epe,uf,data_inicio,data_fim,valor_cnpq,valor_epe,programa_cnpq):
        self.nome             = nome
        self.sei              = sei
        self.epe              = epe
        self.uf               = uf
        self.data_inicio      = data_inicio
        self.data_fim         = data_fim
        self.valor_cnpq       = valor_cnpq
        self.valor_epe        = valor_epe
        self.programa_cnpq    = programa_cnpq

    def __repr__(self):

        return f"{self.nome};{self.sei};{self.epe};{self.uf};{self.data_inicio};{self.data_fim};{self.valor_cnpq};{self.valor_epe};{self.programa_cnpq}"


## tabela com os dados dos processos mãe e seus respectivos acordos
class Acordo_ProcMae(db.Model):

    __tablename__ = 'acordo_procmae'

    id           = db.Column(db.Integer,primary_key = True)
    acordo_id    = db.Column(db.Integer)
    proc_mae_id  = db.Column(db.Integer)

    def __init__ (self,acordo_id,proc_mae_id):
        self.acordo_id    = acordo_id
        self.proc_mae_id  = proc_mae_id

    def __repr__ (self):
        return f"{self.acordo_id};{self.proc_mae_id}"


# programas_interesse

class Programa_Interesse(db.Model):

    __tablename__ = 'programas_a_pegar'

    cod_programa  = db.Column(db.String,primary_key = True)
    desc          = db.Column(db.String)
    sigla         = db.Column(db.String)
    coord         = db.Column(db.String)

    def __init__(self, cod_programa, desc, sigla, coord):
        self.cod_programa   = cod_programa
        self.desc           = desc
        self.sigla          = sigla
        self.coord          = coord

    def __repr__ (self):
        return f"{self.cod_programa};{self.desc};{self.sigla};{self.coord}"

## tabela com os dados básicos dos convênios e respectivos processos SEI

class DadosSEI(db.Model):

    __tablename__ = 'dados_sei'

    id                = db.Column(db.Integer,primary_key = True)
    nr_convenio       = db.Column(db.Integer,nullable=False)
    ano               = db.Column(db.Integer,nullable=False)
    sei               = db.Column(db.String,nullable=False,unique=True,index=True)
    epe               = db.Column(db.String,nullable=False)
    uf                = db.Column(db.String(2),nullable=False)
    programa          = db.Column(db.String,nullable=False)

    def __init__ (self,nr_convenio,ano,sei,epe,uf,programa):
        self.nr_convenio       = nr_convenio
        self.ano               = ano
        self.sei               = sei
        self.epe               = epe
        self.uf                = uf
        self.programa          = programa

    def __repr__ (self):
        return f"{self.nr_convenio};{self.ano};{self.sei};{self.epe};{self.uf};{self.programa}"

#
## tabela com os dados de chamadas homologadas

class Chamadas(db.Model):

    __tablename__ = 'chamadas'

    id               = db.Column(db.Integer,primary_key = True)
    sei              = db.Column(db.String,nullable=False)
    chamada          = db.Column(db.String)
    qtd_projetos     = db.Column(db.Integer)
    vl_total_chamada = db.Column(db.Float)
    doc_sei          = db.Column(db.String)
    obs              = db.Column(db.String)

    def __init__ (self,sei,chamada,qtd_projetos,vl_total_chamada,doc_sei,obs):
        self.sei              = sei
        self.chamada          = chamada
        self.qtd_projetos     = qtd_projetos
        self.vl_total_chamada = vl_total_chamada
        self.doc_sei          = doc_sei
        self.obs              = obs

    def __repr__ (self):
        return f"{self.sei};{self.chamada};{self.qtd_projetos};{self.vl_total_chamada};{self.doc_sei};{self.obs}"



## tabelas do SICONV

# programa

class Programa(db.Model):

    __tablename__ = 'programa'

    ID_PROGRAMA   = db.Column(db.String, primary_key = True)
    COD_PROGRAMA  = db.Column(db.String)
    NOME_PROGRAMA = db.Column(db.String)

    def __init__(self, ID_PROGRAMA, COD_PROGRAMA, NOME_PROGRAMA):
        self.ID_PROGRAMA           = ID_PROGRAMA
        self.COD_PROGRAMA          = COD_PROGRAMA
        self.NOME_PROGRAMA         = NOME_PROGRAMA

    def __repr__ (self):
        return f"{self.ID_PROGRAMA};{self.COD_PROGRAMA};{self.NOME_PROGRAMA}"

## proposta

class Proposta(db.Model):

    __tablename__ = 'proposta'

    ID_PROGRAMA      = db.Column(db.String)
    ID_PROPOSTA      = db.Column(db.String, primary_key = True)
    UF_PROPONENTE    = db.Column(db.String)
    NM_PROPONENTE    = db.Column(db.String)
    OBJETO_PROPOSTA  = db.Column(db.String)

    def __init__(self, ID_PROGRAMA, ID_PROPOSTA, UF_PROPONENTE, NM_PROPONENTE, OBJETO_PROPOSTA):

        self.ID_PROGRAMA          = ID_PROGRAMA
        self.ID_PROPOSTA          = ID_PROPOSTA
        self.UF_PROPONENTE        = UF_PROPONENTE
        self.NM_PROPONENTE        = NM_PROPONENTE
        self.OBJETO_PROPOSTA      = OBJETO_PROPOSTA

    def __repr__ (self):
        return f"{self.ID_PROGRAMA};{self.ID_PROPOSTA};{self.UF_PROPONENTE};{self.NM_PROPONENTE};{self.OBJETO_PROPOSTA}"


## convenio

class Convenio(db.Model):

    __tablename__ = 'convenio'

    NR_CONVENIO                   = db.Column(db.String, primary_key = True)
    ID_PROPOSTA                   = db.Column(db.String)
    DIA                           = db.Column(db.String)
    MES                           = db.Column(db.String)
    ANO                           = db.Column(db.String)
    DIA_ASSIN_CONV                = db.Column(db.String)
    SIT_CONVENIO                  = db.Column(db.String)
    SUBSITUACAO_CONV              = db.Column(db.String)
    SITUACAO_PUBLICACAO           = db.Column(db.String)
    INSTRUMENTO_ATIVO             = db.Column(db.String)
    IND_OPERA_OBTV                = db.Column(db.String)
    NR_PROCESSO                   = db.Column(db.String)
    UG_EMITENTE                   = db.Column(db.String)
    DIA_PUBL_CONV                 = db.Column(db.String)
    DIA_INIC_VIGENC_CONV          = db.Column(db.String)
    DIA_FIM_VIGENC_CONV           = db.Column(db.Date)
    DIA_FIM_VIGENC_ORIGINAL_CONV  = db.Column(db.String)
    DIAS_PREST_CONTAS             = db.Column(db.String)
    DIA_LIMITE_PREST_CONTAS       = db.Column(db.String)
    SITUACAO_CONTRATACAO          = db.Column(db.String)
    IND_ASSINADO                  = db.Column(db.String)
    MOTIVO_SUSPENSAO              = db.Column(db.String)
    IND_FOTO                      = db.Column(db.String)
    QTDE_CONVENIOS                = db.Column(db.String)
    QTD_TA                        = db.Column(db.String)
    QTD_PRORROGA                  = db.Column(db.String)
    VL_GLOBAL_CONV                = db.Column(db.Float)
    VL_REPASSE_CONV               = db.Column(db.Float)
    VL_CONTRAPARTIDA_CONV         = db.Column(db.Float)
    VL_EMPENHADO_CONV             = db.Column(db.Float)
    VL_DESEMBOLSADO_CONV          = db.Column(db.Float)
    VL_SALDO_REMAN_TESOURO        = db.Column(db.Float)
    VL_SALDO_REMAN_CONVENENTE     = db.Column(db.Float)
    VL_RENDIMENTO_APLICACAO       = db.Column(db.Float)
    VL_INGRESSO_CONTRAPARTIDA     = db.Column(db.Float)
    VL_SALDO_CONTA                = db.Column(db.Float)
    VALOR_GLOBAL_ORIGINAL_CONV    = db.Column(db.Float)

    def __init__(self, NR_CONVENIO, ID_PROPOSTA, DIA, MES, ANO, DIA_ASSIN_CONV, SIT_CONVENIO,
                SUBSITUACAO_CONV, SITUACAO_PUBLICACAO, INSTRUMENTO_ATIVO, IND_OPERA_OBTV, NR_PROCESSO,
                UG_EMITENTE, DIA_PUBL_CONV, DIA_INIC_VIGENC_CONV, DIA_FIM_VIGENC_CONV, DIA_FIM_VIGENC_ORIGINAL_CONV,
                DIAS_PREST_CONTAS, DIA_LIMITE_PREST_CONTAS, SITUACAO_CONTRATACAO, IND_ASSINADO, MOTIVO_SUSPENSAO,
                IND_FOTO, QTDE_CONVENIOS, QTD_TA, QTD_PRORROGA, VL_GLOBAL_CONV, VL_REPASSE_CONV,
                VL_CONTRAPARTIDA_CONV, VL_EMPENHADO_CONV, VL_DESEMBOLSADO_CONV, VL_SALDO_REMAN_TESOURO,
                VL_SALDO_REMAN_CONVENENTE, VL_RENDIMENTO_APLICACAO, VL_INGRESSO_CONTRAPARTIDA, VL_SALDO_CONTA,
                VALOR_GLOBAL_ORIGINAL_CONV):

        self.NR_CONVENIO                   = NR_CONVENIO
        self.ID_PROPOSTA                   = ID_PROPOSTA
        self.DIA                           = DIA
        self.MES                           = MES
        self.ANO                           = ANO
        self.DIA_ASSIN_CONV                = DIA_ASSIN_CONV
        self.SIT_CONVENIO                  = SIT_CONVENIO
        self.SUBSITUACAO_CONV              = SUBSITUACAO_CONV
        self.SITUACAO_PUBLICACAO           = SITUACAO_PUBLICACAO
        self.INSTRUMENTO_ATIVO             = INSTRUMENTO_ATIVO
        self.IND_OPERA_OBTV                = IND_OPERA_OBTV
        self.NR_PROCESSO                   = NR_PROCESSO
        self.UG_EMITENTE                   = UG_EMITENTE
        self.DIA_PUBL_CONV                 = DIA_PUBL_CONV
        self.DIA_INIC_VIGENC_CONV          = DIA_INIC_VIGENC_CONV
        self.DIA_FIM_VIGENC_CONV           = DIA_FIM_VIGENC_CONV
        self.DIA_FIM_VIGENC_ORIGINAL_CONV  = DIA_FIM_VIGENC_ORIGINAL_CONV
        self.DIAS_PREST_CONTAS             = DIAS_PREST_CONTAS
        self.DIA_LIMITE_PREST_CONTAS       = DIA_LIMITE_PREST_CONTAS
        self.SITUACAO_CONTRATACAO          = SITUACAO_CONTRATACAO
        self.IND_ASSINADO                  = IND_ASSINADO
        self.MOTIVO_SUSPENSAO              = MOTIVO_SUSPENSAO
        self.IND_FOTO                      = IND_FOTO
        self.QTDE_CONVENIOS                = QTDE_CONVENIOS
        self.QTD_TA                        = QTD_TA
        self.QTD_PRORROGA                  = QTD_PRORROGA
        self.VL_GLOBAL_CONV                = VL_GLOBAL_CONV
        self.VL_REPASSE_CONV               = VL_REPASSE_CONV
        self.VL_CONTRAPARTIDA_CONV         = VL_CONTRAPARTIDA_CONV
        self.VL_EMPENHADO_CONV             = VL_EMPENHADO_CONV
        self.VL_DESEMBOLSADO_CONV          = VL_DESEMBOLSADO_CONV
        self.VL_SALDO_REMAN_TESOURO        = VL_SALDO_REMAN_TESOURO
        self.VL_SALDO_REMAN_CONVENENTE     = VL_SALDO_REMAN_CONVENENTE
        self.VL_RENDIMENTO_APLICACAO       = VL_RENDIMENTO_APLICACAO
        self.VL_INGRESSO_CONTRAPARTIDA     = VL_INGRESSO_CONTRAPARTIDA
        self.VL_SALDO_CONTA                = VL_SALDO_CONTA
        self.VALOR_GLOBAL_ORIGINAL_CONV    = VALOR_GLOBAL_ORIGINAL_CONV

    def __repr__ (self):
        return f"{self.NR_CONVENIO};{self.DIA_ASSIN_CONV};{self.SIT_CONVENIO};{self.SUBSITUACAO_CONV};{self.INSTRUMENTO_ATIVO};\
                 {self.IND_OPERA_OBTV};{self.DIA_INIC_VIGENC_CONV};{self.DIA_FIM_VIGENC_CONV};{self.QTD_TA};{self.QTD_PRORROGA};\
                 {self.VL_GLOBAL_CONV};{self.VL_REPASSE_CONV};{self.VL_CONTRAPARTIDA_CONV};\
                 {self.VL_EMPENHADO_CONV};{self.VL_DESEMBOLSADO_CONV};{self.VL_RENDIMENTO_APLICACAO};{self.VL_INGRESSO_CONTRAPARTIDA}"


## pagamento

class Pagamento(db.Model):

     __tablename__ = 'pagamento'

     id                  = db.Column(db.Integer,primary_key=True)
     NR_CONVENIO         = db.Column(db.String)
     IDENTIF_FORNECEDOR  = db.Column(db.String)
     NOME_FORNECEDOR     = db.Column(db.String)
     VL_PAGO             = db.Column(db.Float)

     def __init__(self, NR_CONVENIO, IDENTIF_FORNECEDOR, NOME_FORNECEDOR, VL_PAGO):

         self.NR_CONVENIO          = NR_CONVENIO
         self.IDENTIF_FORNECEDOR   = IDENTIF_FORNECEDOR
         self.NOME_FORNECEDOR      = NOME_FORNECEDOR
         self.VL_PAGO              = VL_PAGO

     def __repr__ (self):
         return f"{self.NR_CONVENIO};{self.IDENTIF_FORNECEDOR};{self.NOME_FORNECEDOR};{self.VL_PAGO}"


# empenho

class Empenho(db.Model):

    __tablename__ = 'empenho'

    ID_EMPENHO              = db.Column(db.String, primary_key = True)
    NR_CONVENIO             = db.Column(db.String)
    NR_EMPENHO              = db.Column(db.String)
    TIPO_NOTA               = db.Column(db.String)
    DESC_TIPO_NOTA          = db.Column(db.String)
    DATA_EMISSAO            = db.Column(db.Date)
    COD_SITUACAO_EMPENHO    = db.Column(db.String)
    DESC_SITUACAO_EMPENHO   = db.Column(db.String)
    VALOR_EMPENHO           = db.Column(db.Float)

    def __init__(self, ID_EMPENHO, NR_CONVENIO, NR_EMPENHO, TIPO_NOTA, DESC_TIPO_NOTA, DATA_EMISSAO,\
                 COD_SITUACAO_EMPENHO, DESC_SITUACAO_EMPENHO, VALOR_EMPENHO):

        self.ID_EMPENHO             = ID_EMPENHO
        self.NR_CONVENIO            = NR_CONVENIO
        self.NR_EMPENHO             = NR_EMPENHO
        self.TIPO_NOTA              = TIPO_NOTA
        self.DESC_TIPO_NOTA         = DESC_TIPO_NOTA
        self.DATA_EMISSAO           = DATA_EMISSAO
        self.COD_SITUACAO_EMPENHO   = COD_SITUACAO_EMPENHO
        self.DESC_SITUACAO_EMPENHO  = DESC_SITUACAO_EMPENHO
        self.VALOR_EMPENHO          = VALOR_EMPENHO

    def __repr__ (self):
        return f"{self.ID_EMPENHO};{self.NR_CONVENIO};{self.NOME_PROGRAMA};{self.NR_EMPENHO};{self.TIPO_NOTA};\
                 {self.DATA_EMISSAO};{self.COD_SITUACAO_EMPENHO};{self.DESC_SITUACAO_EMPENHO};{self.VALOR_EMPENHO}"

# empenho e naturezas de despesa (carga manual)

class Emp_Cap_Cus(db.Model):

    __tablename__ = 'emp_cap_cus'

    id_empenho = db.Column(db.String, primary_key = True)
    nd         = db.Column(db.String)

    def __init__(self, id_empenho, nd):

        self.id_empenho = id_empenho
        self.nd         = nd

    def __repr__ (self):
        return f"{self.id_empenho};{self.nd}"


# desembolso

class Desembolso(db.Model):

    __tablename__ = 'desembolso'

    ID_DESEMBOLSO           = db.Column(db.String, primary_key = True)
    NR_CONVENIO             = db.Column(db.String)
    DT_ULT_DESEMBOLSO       = db.Column(db.Date)
    QTD_DIAS_SEM_DESEMBOLSO = db.Column(db.String)
    DATA_DESEMBOLSO         = db.Column(db.Date)
    ANO_DESEMBOLSO          = db.Column(db.String)
    MES_DESEMBOLSO          = db.Column(db.String)
    NR_SIAFI                = db.Column(db.String)
    VL_DESEMBOLSADO         = db.Column(db.Float)
    ID_EMPENHO              = db.Column(db.String)

    def __init__(self, ID_DESEMBOLSO, NR_CONVENIO, DT_ULT_DESEMBOLSO, QTD_DIAS_SEM_DESEMBOLSO, DATA_DESEMBOLSO,
                 ANO_DESEMBOLSO, MES_DESEMBOLSO, NR_SIAFI, VL_DESEMBOLSADO, ID_EMPENHO):

        self.ID_DESEMBOLSO              = ID_DESEMBOLSO
        self.NR_CONVENIO                = NR_CONVENIO
        self.DT_ULT_DESEMBOLSO          = DT_ULT_DESEMBOLSO
        self.QTD_DIAS_SEM_DESEMBOLSO    = QTD_DIAS_SEM_DESEMBOLSO
        self.DATA_DESEMBOLSO            = DATA_DESEMBOLSO
        self.ANO_DESEMBOLSO             = ANO_DESEMBOLSO
        self.MES_DESEMBOLSO             = MES_DESEMBOLSO
        self.NR_SIAFI                   = NR_SIAFI
        self.VL_DESEMBOLSADO            = VL_DESEMBOLSADO
        self.ID_EMPENHO                 = ID_EMPENHO

    def __repr__ (self):
        return f"{self.ID_DESEMBOLSO};{self.NR_CONVENIO};{self.DT_ULT_DESEMBOLSO};{self.QTD_DIAS_SEM_DESEMBOLSO};\
                 {self.DATA_DESEMBOLSO};{self.ANO_DESEMBOLSO};{self.MES_DESEMBOLSO};{self.NR_SIAFI};\
                 {self.VL_DESEMBOLSADO};{self.ID_EMPENHO}"


    ##############################################################################################
    ##  banco demandas                                                                          ##
    ##############################################################################################

#
## tabela das coordenações técnicas
class Coords (db.Model):

    __bind_key__ = 'demandas_banco'
    __tablename__ = "coords"

    id   = db.Column(db.Integer,primary_key=True)
    sigla = db.Column(db.String)

    def __init__ (self,sigla):

        self.sigla = sigla

    def __repr__ (self):
        return f"{self.sigla}"


class Tipos_Demanda(db.Model):

    __bind_key__ = 'demandas_banco'
    __tablename__ = 'tipos_demanda'

    id                  = db.Column(db.Integer, primary_key=True)
    tipo                = db.Column(db.String,nullable=False)
    relevancia          = db.Column(db.Integer,nullable=False)

    def __init__(self, tipo, relevancia):

        self.tipo       = tipo
        self.relevancia = relevancia

    def __repr__(self):

        return f"{self.tipo}"


class Plano_Trabalho(db.Model):

    __bind_key__ = 'demandas_banco'
    __tablename__ = 'plano_trabalho'

    id              = db.Column(db.Integer, primary_key=True)
    atividade_sigla = db.Column(db.String,nullable=False)
    atividade_desc  = db.Column(db.String,nullable=False)
    natureza        = db.Column(db.String,nullable=False)
    meta            = db.Column(db.Float,nullable=False)
    respon_1        = db.Column(db.Integer,nullable=False)
    respon_2        = db.Column(db.Integer,nullable=False)

    def __init__(self, atividade_sigla, atividade_desc, natureza, meta, respon_1, respon_2):

        self.atividade_sigla = atividade_sigla
        self.atividade_desc  = atividade_desc
        self.natureza        = natureza
        self.meta            = meta
        self.respon_1        = respon_1
        self.respon_2        = respon_2

    def __repr__(self):

        return f"{self.atividade_sigla};{self.atividade_desc};{self.natureza};{self.meta};{self.respon_1};{self.respon_2}"


class Demanda(db.Model):

    __bind_key__ = 'demandas_banco'
    __tablename__ = 'demandas'

    id                     = db.Column(db.Integer, primary_key=True)
    programa               = db.Column(db.String, nullable=False)
    sei                    = db.Column(db.String, nullable=False)
    convênio               = db.Column(db.String(6))
    ano_convênio           = db.Column(db.String(4))
    tipo                   = db.Column(db.String,nullable=False)
    data                   = db.Column(db.DateTime,nullable=False,default=datetime.now())
    user_id                = db.Column(db.Integer, db.ForeignKey('users.id'),nullable=False)
    titulo                 = db.Column(db.String(140),nullable=False)
    desc                   = db.Column(db.Text,nullable=False)
    necessita_despacho     = db.Column(db.Boolean)
    conclu                 = db.Column(db.Boolean)
    data_conclu            = db.Column(db.DateTime)
    necessita_despacho_cg  = db.Column(db.Boolean)
    urgencia               = db.Column(db.Integer,default=3)
    data_env_despacho      = db.Column(db.DateTime)
    nota                   = db.Column(db.Integer)

    providencias        = db.relationship('Providencia',backref='demanda',cascade="delete, delete-orphan")
    despachos           = db.relationship('Despacho',backref='demanda',cascade="delete, delete-orphan")


    def __init__(self, programa, sei, convênio, ano_convênio, tipo, data, user_id, titulo, desc, necessita_despacho,\
                 conclu, data_conclu,necessita_despacho_cg,urgencia,data_env_despacho,nota):
        self.programa              = programa
        self.sei                   = sei
        self.convênio              = convênio
        self.ano_convênio          = ano_convênio
        self.tipo                  = tipo
        self.data                  = data
        self.user_id               = user_id
        self.titulo                = titulo
        self.desc                  = desc
        self.necessita_despacho    = necessita_despacho
        self.conclu                = conclu
        self.data_conclu           = data_conclu
        self.necessita_despacho_cg = necessita_despacho_cg
        self.urgencia              = urgencia
        self.data_env_despacho     = data_env_despacho
        self.nota                  = nota

    def __repr__(self):

        if self.necessita_despacho == '1':
            flag1 = 'Necessida despacho'
        else:
            flag1 = ''
        if self.conclu == '1':
            flag2 = 'Concluído'
        else:
            flag2 = ''
        if self.necessita_despacho_cg == '1':
            flag3 = 'Necessida despacho CG'
        else:
            flag3 = ''

        return f"{self.programa};{self.sei};{self.convênio};{self.ano_convênio};{self.tipo};{self.data};\
                 {self.user_id};{self.titulo};{flag1};{flag2};{flag3};{self.data_conclu}"

class Despacho(db.Model):

    __bind_key__ = 'demandas_banco'
    __tablename__ = 'despachos'

    id                  = db.Column(db.Integer, primary_key=True)
    data                = db.Column(db.DateTime,nullable=False,default=datetime.now())
    user_id             = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"),nullable=False)
    demanda_id          = db.Column(db.Integer, db.ForeignKey('demandas.id', ondelete="CASCADE"),nullable=False)
    texto               = db.Column(db.Text,nullable=False)

    def __init__(self, data, user_id, demanda_id, texto):

        self.data       = data
        self.user_id    = user_id
        self.demanda_id = demanda_id
        self.texto      = texto


    def __repr__(self):

        return f"{self.data};{self.user_id};{self.demanda_id};{self.texto}"

class Providencia(db.Model):

    __bind_key__ = 'demandas_banco'
    __tablename__ = 'providencias'

    id                  = db.Column(db.Integer, primary_key=True)
    data                = db.Column(db.DateTime,nullable=False,default=datetime.now())
    demanda_id          = db.Column(db.Integer, db.ForeignKey('demandas.id', ondelete="CASCADE"),nullable=False)
    texto               = db.Column(db.Text,nullable=False)
    user_id             = db.Column(db.Integer, nullable=False)
    duracao             = db.Column(db.Integer)
    programada          = db.Column(db.Boolean)

    def __init__(self, data, demanda_id, texto, user_id, duracao, programada):

        self.data       = data
        self.demanda_id = demanda_id
        self.texto      = texto
        self.user_id    = user_id
        self.duracao    = duracao
        self.programada = programada

    def __repr__(self):

        return f"{self.data};{self.demanda_id};{self.texto}"

class User(db.Model, UserMixin):

    __bind_key__ = 'demandas_banco'
    __tablename__ = 'users'

    id                         = db.Column(db.Integer,primary_key=True)
    profile_image              = db.Column(db.String(64),nullable=False,default='default_profile.png')
    email                      = db.Column(db.String(64),unique=True,index=True)
    username                   = db.Column(db.String(64),unique=True,index=True)
    password_hash              = db.Column(db.String(128))
    despacha                   = db.Column(db.Boolean)
    email_confirmation_sent_on = db.Column(db.DateTime, nullable=True)
    email_confirmed            = db.Column(db.Boolean, nullable=True, default=False)
    email_confirmed_on         = db.Column(db.DateTime, nullable=True)
    registered_on              = db.Column(db.DateTime, nullable=True)
    last_logged_in             = db.Column(db.DateTime, nullable=True)
    current_logged_in          = db.Column(db.DateTime, nullable=True)
    role                       = db.Column(db.String, default='user')
    coord                      = db.Column(db.String)
    despacha2                  = db.Column(db.Boolean)
    ativo                      = db.Column(db.Boolean)
    sversion                   = db.Column(db.String)
    cargo_func                 = db.Column(db.String)


    posts = db.relationship ('Demanda',backref='author',lazy=True)
    desp  = db.relationship ('Despacho',backref='author',lazy=True)

    def __init__(self,email,username,plaintext_password,despacha,coord,despacha2,ativo,sversion,cargo_func,email_confirmation_sent_on=None,role='user'):

        self.email                      = email
        self.username                   = username
        self.password_hash              = generate_password_hash(plaintext_password)
        #self.password = plaintext_password
        self.despacha                   = despacha
        self.email_confirmation_sent_on = email_confirmation_sent_on
        self.email_confirmed            = False
        self.email_confirmed_on         = None
        self.registered_on              = datetime.now()
        self.last_logged_in             = None
        self.current_logged_in          = datetime.now()
        self.role                       = role
        self.coord                      = coord
        self.despacha2                  = despacha2
        self.ativo                      = ativo
        self.sversion                   = sversion
        self.cargo_func                 = cargo_func

    def check_password (self,plaintext_password):

        return check_password_hash(self.password_hash,plaintext_password)

    def __repr__(self):

        return f"{self.username};{self.despacha};{self.despacha2};{self.cargo_func}"
#
## tabela de registro dos principais commits
class Log_Auto(db.Model):

    __bind_key__ = 'demandas_banco'
    __tablename__ = 'log_auto'

    id             = db.Column(db.Integer, primary_key=True)
    data_hora      = db.Column(db.DateTime,nullable=False,default=datetime.now())
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'),nullable=False)
    demanda_id     = db.Column(db.Integer, db.ForeignKey('demandas.id'))
    tipo_registro  = db.Column(db.Text,nullable=False)

    def __init__(self, data_hora, user_id, demanda_id, tipo_registro):

        self.data_hora     = data_hora
        self.user_id       = user_id
        self.demanda_id    = demanda_id
        self.tipo_registro = tipo_registro


    def __repr__(self):

        return f"{self.data_hora};{self.user_id};{self.demanda_id};{self.tipo_registro}"
#
#
## tabela com a descrição dos principais commits
class Log_Desc(db.Model):

    __bind_key__ = 'demandas_banco'
    __tablename__ = 'log_desc'

    id             = db.Column(db.Integer, primary_key=True)
    tipo_registro  = db.Column(db.String,nullable=False)
    desc_registro  = db.Column(db.Text,nullable=False)

    def __init__(self, tipo_registro, desc_registro):

        self.data_hora     = data_hora
        self.tipo_registro = tipo_registro
        self.desc_registro = desc_registro


    def __repr__(self):

        return f"{self.tipo_registro};{self.desc_registro}"

#
## tabela que guarda as datas de referência em que as planilhas da COSAO foram geradas
class RefSICONV (db.Model):

    __tablename__ = "ref_siconv"

    id       = db.Column(db.Integer,primary_key=True)
    data_ref = db.Column(db.Date)

    def __init__ (self,data_ref):

        self.data_ref = data_ref

    def __repr__ (self):
        return f"{self.data_ref}"

#
## tabela com as mensagens siconv carregadas em procedimento específico
class MSG_Siconv (db.Model):

    __tablename__ = "msg_siconv"

    id          = db.Column(db.Integer,primary_key=True)
    nr_convenio = db.Column(db.String(6))
    desc        = db.Column(db.String)
    data_ref    = db.Column(db.Date)
    sit         = db.Column(db.String)

    def __init__ (self,nr_convenio,desc,data_ref,sit):

        self.nr_convenio = nr_convenio
        self.desc        = desc
        self.data_ref    = data_ref
        self.sit         = sit

    def __repr__ (self):
        return f"{self.nr_convenio};{self.desc};{self.data_ref};{self.sit}"
