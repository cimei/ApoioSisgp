use DBSISGP14
go


/*** Limpeza das tabelas que receber�o dados de teste ***/

DELETE FROM [dbo].[Pessoa]
DELETE FROM [dbo].[Unidade]
DELETE FROM [dbo].[TipoFuncao]
GO

/*** EXEMPLO DE REGISTRO DE TIPOS DE FUN��O ***/
   
INSERT INTO [dbo].[TipoFuncao] ([tipoFuncaoId],[tfnDescricao],[tfnCodigoFuncao],[tfnIndicadorChefia]) 
   VALUES (2, 'Diretor', '101.5', 1)
INSERT INTO [dbo].[TipoFuncao] ([tipoFuncaoId],[tfnDescricao],[tfnCodigoFuncao],[tfnIndicadorChefia]) 
   VALUES (3, 'Coordenador-Geral', '101.4', 1)
INSERT INTO [dbo].[TipoFuncao] ([tipoFuncaoId],[tfnDescricao],[tfnCodigoFuncao],[tfnIndicadorChefia]) 
   VALUES (4, 'Coordenador', '101.3', 1)
GO
   
/*** EXEMPLO DE REGISTRO DE UNIDADES ***/
/*** Os IDs das unidades ser�o utilizados para o registro de pessoas na sequ�ncia ***/
   
DECLARE @SUSEP INT
DECLARE @DEAFI INT
DECLARE @DETIC INT
DECLARE @COGEP INT
DECLARE @COGET INT
DECLARE @ASDEN INT
DECLARE @COPROJ INT
DECLARE @COARQ INT
DECLARE @USUARIOGESTOR INT

INSERT INTO [dbo].[Unidade] ([undSigla],[undDescricao],[unidadeIdPai],[tipoUnidadeId],[situacaoUnidadeId],[ufId],[undNivel],[tipoFuncaoUnidadeId],[Email],[undCodigoSIORG])
   VALUES ('SUSEP', 'Superintend�ncia de Seguros Privados', NULL, 13, 1, 'RJ', 1, NULL, 'susep.rj@susep.gov.br', '')
SET @SUSEP = @@IDENTITY

INSERT INTO [dbo].[Unidade] ([undSigla],[undDescricao],[unidadeIdPai],[tipoUnidadeId],[situacaoUnidadeId],[ufId],[undNivel],[tipoFuncaoUnidadeId],[Email],[undCodigoSIORG])
   VALUES ('DEAFI', 'Departamento de Administra��o e Finan�as', @SUSEP, 2, 1, 'RJ', 2, NULL, 'susep.rj@susep.gov.br', '')
SET @DEAFI = @@IDENTITY

INSERT INTO [dbo].[Unidade] ([undSigla],[undDescricao],[unidadeIdPai],[tipoUnidadeId],[situacaoUnidadeId],[ufId],[undNivel],[tipoFuncaoUnidadeId],[Email],[undCodigoSIORG])
   VALUES ('DETIC', 'Departamento de tecnologia da informa��o', @SUSEP, 2, 1, 'RJ', 2, NULL, 'susep.rj@susep.gov.br', '')
SET @DETIC = @@IDENTITY

INSERT INTO [dbo].[Unidade] ([undSigla],[undDescricao],[unidadeIdPai],[tipoUnidadeId],[situacaoUnidadeId],[ufId],[undNivel],[tipoFuncaoUnidadeId],[Email],[undCodigoSIORG])
   VALUES ('COGEP', 'Coordena��o de Gest�o e Desenvolvimento de Pessoal', @DEAFI, 4, 1, 'RJ', 3, 1, 'susep.rj@susep.gov.br', '')
SET @COGEP = @@IDENTITY

INSERT INTO [dbo].[Unidade] ([undSigla],[undDescricao],[unidadeIdPai],[tipoUnidadeId],[situacaoUnidadeId],[ufId],[undNivel],[tipoFuncaoUnidadeId],[Email],[undCodigoSIORG])
   VALUES ('COGET', 'Coordena��o de Apoio � Gest�o Estrat�gica', @DEAFI, 4, 1, 'RJ', 3, 5, 'susep.rj@susep.gov.br', '')
SET @COGET = @@IDENTITY

INSERT INTO [dbo].[Unidade] ([undSigla],[undDescricao],[unidadeIdPai],[tipoUnidadeId],[situacaoUnidadeId],[ufId],[undNivel],[tipoFuncaoUnidadeId],[Email],[undCodigoSIORG])
   VALUES ('ASDEN', 'Assessoria de Desenvolvimento de Sistemas', @DETIC, 3, 1, 'RJ', 3, NULL, 'susep.rj@susep.gov.br', '')
SET @ASDEN = @@IDENTITY

INSERT INTO [dbo].[Unidade] ([undSigla],[undDescricao],[unidadeIdPai],[tipoUnidadeId],[situacaoUnidadeId],[ufId],[undNivel],[tipoFuncaoUnidadeId],[Email],[undCodigoSIORG])
   VALUES ('COPROJ', 'Coordena��o de Projetos de Tecnologia', @ASDEN, 4, 1, 'RJ', 4, NULL, 'susep.rj@susep.gov.br', '')
SET @COPROJ = @@IDENTITY

INSERT INTO [dbo].[Unidade] ([undSigla],[undDescricao],[unidadeIdPai],[tipoUnidadeId],[situacaoUnidadeId],[ufId],[undNivel],[tipoFuncaoUnidadeId],[Email],[undCodigoSIORG]) 
   VALUES ('COARQ', 'Departamento de tecnologia da informa��o', @ASDEN, 4, 1, 'RJ', 4, NULL, 'susep.rj@susep.gov.br', '')
SET @COARQ = @@IDENTITY

/*** EXEMPLO DE REGISTRO DE PESSOAS ***/
    
/*** Esta pessoa ser� designada como usu�rio gestor na tabela CatalogoDominio ***/
INSERT INTO [dbo].[Pessoa] ([pesNome],[pesCPF],[pesDataNascimento],[pesMatriculaSiape],[pesEmail],[unidadeId],[tipoFuncaoId],[cargaHoraria]) 
   VALUES ('Usu�rio Gestor', '08056275029', getdate(), '111', 'EMAILPESSOA@ORGAO.GOV.BR', @COPROJ, NULL, 8)
SET @USUARIOGESTOR = @@IDENTITY
DELETE FROM [dbo].[CatalogoDominio] WHERE classificacao = 'GestorSistema'
INSERT INTO [dbo].[CatalogoDominio] VALUES(10001, 'GestorSistema', @USUARIOGESTOR, 1)

/*** Pessoas sem fun��o associada ***/
INSERT INTO [dbo].[Pessoa] ([pesNome],[pesCPF],[pesDataNascimento],[pesMatriculaSiape],[pesEmail],[unidadeId],[tipoFuncaoId],[cargaHoraria])
   VALUES ('Usu�rio Servidor', '08152972541', getdate(), '111', 'EMAILPESSOA@ORGAO.GOV.BR', @COPROJ, NULL, 8)
INSERT INTO [dbo].[Pessoa] ([pesNome],[pesCPF],[pesDataNascimento],[pesMatriculaSiape],[pesEmail],[unidadeId],[tipoFuncaoId],[cargaHoraria]) 
   VALUES ('Usu�rio Servidor 1', '59516301002', getdate(),  '111', 'EMAILPESSOA@ORGAO.GOV.BR', @COARQ, NULL, 8)
INSERT INTO [dbo].[Pessoa] ([pesNome],[pesCPF],[pesDataNascimento],[pesMatriculaSiape],[pesEmail],[unidadeId],[tipoFuncaoId],[cargaHoraria]) 
   VALUES ('Usu�rio Servidor 2', '18761704091',  getdate(), '111', 'EMAILPESSOA@ORGAO.GOV.BR', @COARQ, NULL, 8)
INSERT INTO [dbo].[Pessoa] ([pesNome],[pesCPF],[pesDataNascimento],[pesMatriculaSiape],[pesEmail],[unidadeId],[tipoFuncaoId],[cargaHoraria]) 
   VALUES ('Usu�rio Servidor 3', '07721701007', getdate(),  '111', 'EMAILPESSOA@ORGAO.GOV.BR', @COPROJ, NULL, 8)
INSERT INTO [dbo].[Pessoa] ([pesNome],[pesCPF],[pesDataNascimento],[pesMatriculaSiape],[pesEmail],[unidadeId],[tipoFuncaoId],[cargaHoraria])
   VALUES ('Usu�rio Servidor 4', '51884275087', getdate(),  '111', 'EMAILPESSOA@ORGAO.GOV.BR', @COPROJ, NULL, 8)
INSERT INTO [dbo].[Pessoa] ([pesNome],[pesCPF],[pesDataNascimento],[pesMatriculaSiape],[pesEmail],[unidadeId],[tipoFuncaoId],[cargaHoraria]) 
   VALUES ('Usu�rio COGET', '43321040565', getdate(),  '111', 'EMAILPESSOA@ORGAO.GOV.BR', @COGET, 4, 8)
   
/*** Pessoas com fun��o associada e respectiva atualiza��o na tabela de Unidades ***/
INSERT INTO [dbo].[Pessoa] ([pesNome],[pesCPF],[pesDataNascimento],[pesMatriculaSiape],[pesEmail],[unidadeId],[tipoFuncaoId],[cargaHoraria])
   VALUES ('Usu�rio Coordenador', '25715446597', getdate(),  '111', 'EMAILPESSOA@ORGAO.GOV.BR', @COPROJ, 2, 8)


INSERT INTO [dbo].[Pessoa] ([pesNome],[pesCPF],[pesDataNascimento],[pesMatriculaSiape],[pesEmail],[unidadeId],[tipoFuncaoId],[cargaHoraria]) 
   VALUES ('Usu�rio CG', '95387502500', getdate(),  '111', 'EMAILPESSOA@ORGAO.GOV.BR', @ASDEN, 3, 8)


INSERT INTO [dbo].[Pessoa] ([pesNome],[pesCPF],[pesDataNascimento],[pesMatriculaSiape],[pesEmail],[unidadeId],[tipoFuncaoId],[cargaHoraria]) 
   VALUES ('Usu�rio Diretor', '39178470510', getdate(),  '111', 'EMAILPESSOA@ORGAO.GOV.BR', @DETIC, NULL, 8)


GO
    
