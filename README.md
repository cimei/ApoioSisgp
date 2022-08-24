# ApoioSisgp
Aplicativo de apoio à gestão do SISGP. Permite visualizar e atualizar dados das tabelas Unidade e Pessoa, de tabelas auxiliares (SituacaoPessoa, TipoFuncao, TipoVinculo e Feriado), além de outras funcionalidades.

A partir da versão 2.5.0, o aplicativo está preparado para a instalação via contêiner Docker, usando o gunicorn como WSGI.

Imagem disponível em https://hub.docker.com/r/cimei/apoiosisgp.

Como o código é reaproveitado de um projeto anterior, pode ocorrer de ter mais pacotes instalados do que o realmente necessário, mas isto não é um impedimento.

Na pasta Instance, há o arquivo flask.cfg onde podem ser verificadas as varíaveis de ambiente necessárias quando da execução do contêiner. Atente para a chave SECRECT_KEY do sistema, é recomendável usar uma chave aletória.

Como este sistema faz controle de acesso e registra o log dos commits realizados, é necessário criar duas tabelas no DBSISGP, conforme instruções SQL:

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
            [userAtivo] [bit] NULL,
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
            [msg] [varchar](150) NOT NULL,
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



