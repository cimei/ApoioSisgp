use DBSISGP14
go


/*** Limpeza das tabelas que receberão dados de teste ***/

DELETE FROM [dbo].[Pessoa]
DELETE FROM [dbo].[Unidade]
DELETE FROM [dbo].[TipoFuncao]
GO

/*** EXEMPLO DE REGISTRO DE TIPOS DE FUNÇÃO ***/
   
INSERT INTO [dbo].[TipoFuncao] ([tipoFuncaoId],[tfnDescricao],[tfnCodigoFuncao],[tfnIndicadorChefia]) 
   VALUES (2, 'Diretor', '101.5', 1)
INSERT INTO [dbo].[TipoFuncao] ([tipoFuncaoId],[tfnDescricao],[tfnCodigoFuncao],[tfnIndicadorChefia]) 
   VALUES (3, 'Coordenador-Geral', '101.4', 1)
INSERT INTO [dbo].[TipoFuncao] ([tipoFuncaoId],[tfnDescricao],[tfnCodigoFuncao],[tfnIndicadorChefia]) 
   VALUES (4, 'Coordenador', '101.3', 1)
GO
   
/*** EXEMPLO DE REGISTRO DE UNIDADES ***/
/*** Os IDs das unidades serão utilizados para o registro de pessoas na sequência ***/
   
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
   VALUES ('SUSEP', 'Superintendência de Seguros Privados', NULL, 13, 1, 'RJ', 1, NULL, 'susep.rj@susep.gov.br', '')
SET @SUSEP = @@IDENTITY

INSERT INTO [dbo].[Unidade] ([undSigla],[undDescricao],[unidadeIdPai],[tipoUnidadeId],[situacaoUnidadeId],[ufId],[undNivel],[tipoFuncaoUnidadeId],[Email],[undCodigoSIORG])
   VALUES ('DEAFI', 'Departamento de Administração e Finanças', @SUSEP, 2, 1, 'RJ', 2, NULL, 'susep.rj@susep.gov.br', '')
SET @DEAFI = @@IDENTITY

INSERT INTO [dbo].[Unidade] ([undSigla],[undDescricao],[unidadeIdPai],[tipoUnidadeId],[situacaoUnidadeId],[ufId],[undNivel],[tipoFuncaoUnidadeId],[Email],[undCodigoSIORG])
   VALUES ('DETIC', 'Departamento de tecnologia da informação', @SUSEP, 2, 1, 'RJ', 2, NULL, 'susep.rj@susep.gov.br', '')
SET @DETIC = @@IDENTITY

INSERT INTO [dbo].[Unidade] ([undSigla],[undDescricao],[unidadeIdPai],[tipoUnidadeId],[situacaoUnidadeId],[ufId],[undNivel],[tipoFuncaoUnidadeId],[Email],[undCodigoSIORG])
   VALUES ('COGEP', 'Coordenação de Gestão e Desenvolvimento de Pessoal', @DEAFI, 4, 1, 'RJ', 3, 1, 'susep.rj@susep.gov.br', '')
SET @COGEP = @@IDENTITY

INSERT INTO [dbo].[Unidade] ([undSigla],[undDescricao],[unidadeIdPai],[tipoUnidadeId],[situacaoUnidadeId],[ufId],[undNivel],[tipoFuncaoUnidadeId],[Email],[undCodigoSIORG])
   VALUES ('COGET', 'Coordenação de Apoio à Gestão Estratégica', @DEAFI, 4, 1, 'RJ', 3, 5, 'susep.rj@susep.gov.br', '')
SET @COGET = @@IDENTITY

INSERT INTO [dbo].[Unidade] ([undSigla],[undDescricao],[unidadeIdPai],[tipoUnidadeId],[situacaoUnidadeId],[ufId],[undNivel],[tipoFuncaoUnidadeId],[Email],[undCodigoSIORG])
   VALUES ('ASDEN', 'Assessoria de Desenvolvimento de Sistemas', @DETIC, 3, 1, 'RJ', 3, NULL, 'susep.rj@susep.gov.br', '')
SET @ASDEN = @@IDENTITY

INSERT INTO [dbo].[Unidade] ([undSigla],[undDescricao],[unidadeIdPai],[tipoUnidadeId],[situacaoUnidadeId],[ufId],[undNivel],[tipoFuncaoUnidadeId],[Email],[undCodigoSIORG])
   VALUES ('COPROJ', 'Coordenação de Projetos de Tecnologia', @ASDEN, 4, 1, 'RJ', 4, NULL, 'susep.rj@susep.gov.br', '')
SET @COPROJ = @@IDENTITY

INSERT INTO [dbo].[Unidade] ([undSigla],[undDescricao],[unidadeIdPai],[tipoUnidadeId],[situacaoUnidadeId],[ufId],[undNivel],[tipoFuncaoUnidadeId],[Email],[undCodigoSIORG]) 
   VALUES ('COARQ', 'Departamento de tecnologia da informação', @ASDEN, 4, 1, 'RJ', 4, NULL, 'susep.rj@susep.gov.br', '')
SET @COARQ = @@IDENTITY

/*** EXEMPLO DE REGISTRO DE PESSOAS ***/
    
/*** Esta pessoa será designada como usuário gestor na tabela CatalogoDominio ***/
INSERT INTO [dbo].[Pessoa] ([pesNome],[pesCPF],[pesDataNascimento],[pesMatriculaSiape],[pesEmail],[unidadeId],[tipoFuncaoId],[cargaHoraria]) 
   VALUES ('Usuário Gestor', '08056275029', getdate(), '111', 'EMAILPESSOA@ORGAO.GOV.BR', @COPROJ, NULL, 8)
SET @USUARIOGESTOR = @@IDENTITY
DELETE FROM [dbo].[CatalogoDominio] WHERE classificacao = 'GestorSistema'
INSERT INTO [dbo].[CatalogoDominio] VALUES(10001, 'GestorSistema', @USUARIOGESTOR, 1)

/*** Pessoas sem função associada ***/
INSERT INTO [dbo].[Pessoa] ([pesNome],[pesCPF],[pesDataNascimento],[pesMatriculaSiape],[pesEmail],[unidadeId],[tipoFuncaoId],[cargaHoraria])
   VALUES ('Usuário Servidor', '08152972541', getdate(), '111', 'EMAILPESSOA@ORGAO.GOV.BR', @COPROJ, NULL, 8)
INSERT INTO [dbo].[Pessoa] ([pesNome],[pesCPF],[pesDataNascimento],[pesMatriculaSiape],[pesEmail],[unidadeId],[tipoFuncaoId],[cargaHoraria]) 
   VALUES ('Usuário Servidor 1', '59516301002', getdate(),  '111', 'EMAILPESSOA@ORGAO.GOV.BR', @COARQ, NULL, 8)
INSERT INTO [dbo].[Pessoa] ([pesNome],[pesCPF],[pesDataNascimento],[pesMatriculaSiape],[pesEmail],[unidadeId],[tipoFuncaoId],[cargaHoraria]) 
   VALUES ('Usuário Servidor 2', '18761704091',  getdate(), '111', 'EMAILPESSOA@ORGAO.GOV.BR', @COARQ, NULL, 8)
INSERT INTO [dbo].[Pessoa] ([pesNome],[pesCPF],[pesDataNascimento],[pesMatriculaSiape],[pesEmail],[unidadeId],[tipoFuncaoId],[cargaHoraria]) 
   VALUES ('Usuário Servidor 3', '07721701007', getdate(),  '111', 'EMAILPESSOA@ORGAO.GOV.BR', @COPROJ, NULL, 8)
INSERT INTO [dbo].[Pessoa] ([pesNome],[pesCPF],[pesDataNascimento],[pesMatriculaSiape],[pesEmail],[unidadeId],[tipoFuncaoId],[cargaHoraria])
   VALUES ('Usuário Servidor 4', '51884275087', getdate(),  '111', 'EMAILPESSOA@ORGAO.GOV.BR', @COPROJ, NULL, 8)
INSERT INTO [dbo].[Pessoa] ([pesNome],[pesCPF],[pesDataNascimento],[pesMatriculaSiape],[pesEmail],[unidadeId],[tipoFuncaoId],[cargaHoraria]) 
   VALUES ('Usuário COGET', '43321040565', getdate(),  '111', 'EMAILPESSOA@ORGAO.GOV.BR', @COGET, 4, 8)
   
/*** Pessoas com função associada e respectiva atualização na tabela de Unidades ***/
INSERT INTO [dbo].[Pessoa] ([pesNome],[pesCPF],[pesDataNascimento],[pesMatriculaSiape],[pesEmail],[unidadeId],[tipoFuncaoId],[cargaHoraria])
   VALUES ('Usuário Coordenador', '25715446597', getdate(),  '111', 'EMAILPESSOA@ORGAO.GOV.BR', @COPROJ, 2, 8)


INSERT INTO [dbo].[Pessoa] ([pesNome],[pesCPF],[pesDataNascimento],[pesMatriculaSiape],[pesEmail],[unidadeId],[tipoFuncaoId],[cargaHoraria]) 
   VALUES ('Usuário CG', '95387502500', getdate(),  '111', 'EMAILPESSOA@ORGAO.GOV.BR', @ASDEN, 3, 8)


INSERT INTO [dbo].[Pessoa] ([pesNome],[pesCPF],[pesDataNascimento],[pesMatriculaSiape],[pesEmail],[unidadeId],[tipoFuncaoId],[cargaHoraria]) 
   VALUES ('Usuário Diretor', '39178470510', getdate(),  '111', 'EMAILPESSOA@ORGAO.GOV.BR', @DETIC, NULL, 8)


GO
    
