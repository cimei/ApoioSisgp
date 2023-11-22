**Histórico recente:**

Tag v3.3.0: 
A instituição do usuário deve ser informada no momento do seu registro. Isto permitirá a segregação por instituição na parte de envio de dados.
Ao usar esta imagem, deve-se alterar a tabela Apoio.User em função da inclusão de campos novos.
As variáveis de ambiente APIPGDME_AUTH_USER e APIPGDME_AUTH_PASSWORD serão informadas no momento da liberação do usuário para o envio de dados.

Tag v3.2.8: 
Correção/ajuste na carga de Unidades e Pessoas.  

Tag v3.2.7: 
Procura evitar que uma Unidade seja registrada como "pai" dela mesma, o que pode causar erro de acesso no SISGP. Passa a permitir carga em lote (Unidades e Pessoas) com a possibilidade de manutenção de valores originais em campos dos registros por meio do uso de caractere coringa (ver manual).

**Instruções para instalação:**

O sistema foi desenvolvido em Python-Flask, usa o gunicorn como WSGI.

Antes de rodar o contêiner pela primeira vez, é necessário criar, ou alterar, as seguintes tabelas no banco de dados do SISGP:

      use [<nome do banco do SISGP>]
      GO

      CREATE SCHEMA [Apoio]
      GO
      
      /****** Object:  Table [Apoio].[User]  e [Apoio].[log_auto]  ******/
      SET ANSI_NULLS ON
      GO
      
      SET QUOTED_IDENTIFIER ON
      GO
      
      CREATE TABLE [Apoio].[User](
            [id] [bigint] IDENTITY(1,1) NOT NULL,
            [userNome] [varchar](150) NOT NULL,
            [userEmail] [varchar](150) NOT NULL,
            [password_hash] [varchar](128) NOT NULL,
            [email_confirmation_sent_on] [datetime] NULL,
            [email_confirmed] [bit] NULL,
            [email_confirmed_on] [datetime] NULL,
            [registered_on] [datetime] NULL,
            [last_logged_in] [datetime] NULL,
            [current_logged_in] [datetime] NULL,
            [userEnvia] [bit] NULL,
            [userAtivo] [bit] NULL,
            [avaliadorId] [bigint] NULL,
            [instituicaoId] [bigint] NULL,
	      [user_api] [varchar](150) NULL,
	      [senha_api] [varchar](150) NULL,
       CONSTRAINT [PK_User] PRIMARY KEY CLUSTERED 
      (
      	[id] ASC
      )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON)       ON [PRIMARY]
      ) ON [PRIMARY]
      GO
      
      CREATE TABLE [Apoio].[log_auto](
            [id] [bigint] IDENTITY(1,1) NOT NULL,
            [data_hora] [datetime] NOT NULL,
            [user_id] [bigint] NOT NULL,
            [msg] [varchar](300) NOT NULL,
       CONSTRAINT [PK_log_auto] PRIMARY KEY CLUSTERED 
      (
      	[id] ASC
      )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON)     ON [PRIMARY]
      ) ON [PRIMARY]
      GO

      ALTER TABLE [Apoio].[log_auto]  WITH CHECK ADD  CONSTRAINT [FK_log_auto_user_id] FOREIGN KEY([user_id])
      REFERENCES [Apoio].[User] ([id])
      GO
      
      ALTER TABLE [Apoio].[log_auto] CHECK CONSTRAINT [FK_log_auto_user_id]
      GO

[Apoio].[User] é para o controle de usuários, [Apoio].[log_auto] para o diário do sistema .

Outro detalhe sobre o banco de dados: Como o sistema conta com a funcionalidade de envio de dados, ele utiliza as views da API de Envio de Planos de Trabalho do Programa de Gestão (CADE/ME). O script de geração destas views está disponível no github do SISGP (https://github.com/spbgovbr/Sistema_Programa_de_Gestao_Susep).

Ao executar o contêiner, atente para os parâmetros de acesso ao banco de dados do SISGP e de e-mail:

    docker run -dp 5000:5000 -e DB_SERVER="servidor do banco sqlserver do sisgp" -e DB_PORT="1433" -e DB_DATABASE="DBSISGP" -e DB_USER="usuário de acesso ao banco" -e DB_PWD="senha de acesso ao banco" -e MAIL_SERVER="servidor de e-mail" -e MAIL_PORT="587" -e MAIL_USE_TLS="True" -e MAIL_USER="email que o APP irá utilizar" -e MAIL_PWD="senha do e-mail"  -e APIPGDME_URL="http://hom.api.programadegestao.economia.gov.br -> este é a url de testes" -e APIPGDME_AUTH_USER="user da credencial" -e APIPGDME_AUTH_PASSWORD="senha da credencial"  -e CONSULTA_API="N"  meag:[TAG]

**Variáveis de ambiente:**

*Banco de dados:*

 - DB_SERVER - servidor onde o bando de dados do SISGP foi instalado
 - DB_PORT - porta de acesso ao banco de dados do SISGP, no SQLSever costuma ser a 1433
 - DB_DATABASE - o nome do banco de dados do SISGP, costuma ser DBSISGP
 - DB_USER - o usuário que terá acesso ao bando de dados do SISGP
 - DB_PWD - a senha do usuário de acesso ao banco de dados do SISGP, é importante que esta senha não expire

*E-mail:*

 - MAIL_SERVER - servidor de e-mail
 - MAIL_PORT -  porta
 - MAIL_USE_TLS - se usa TLS (True ou False)
 - MAIL_USER - conta de e-mail que será utilizada pelo aplicativo MEAG
 - MAIL_PWD - senha desta conta

*API de envio de dados:*

- APIPGDME_URL -  Url de conexão com a API PGD ME

Caso não as possua, as credenciais podem ser informadas em branco ("").