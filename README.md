# MEAG
Aplicativo de apoio à gestão do SISGP. Possibilita o envio de dados ao órgão central do SIPEC via API correspondente e permite visualizar e atualizar dados das tabelas Unidade e Pessoa, de tabelas auxiliares (SituacaoPessoa, TipoFuncao, TipoVinculo e Feriado), além de outras funcionalidades.

O sistema está configurado para a instalação via contêiner Docker, usando o gunicorn como WSGI.

Imagem disponível em https://hub.docker.com/r/cimei/apoiosisgp. Atenção para a tag que se deseja utilizar, bem como para as respectivas variáveis de ambiente que devem ser informadas no momento da execução (run) do contêiner.

Para verificar o que foi incorporado/corrigido em cada versão, veja o arquivo de histórico de atualizações, disponível em atualizações.txt.

Como o código é reaproveitado de um projeto anterior, pode ocorrer de ter mais pacotes instalados do que o realmente necessário, mas isto não é um impedimento.

Na pasta Instance, o arquivo flask.cfg contem as configurações básicas, atente para a chave SECRECT_KEY do sistema, é recomendável usar uma chave aletória.

A pasta build/html tem a documentação do aplicativo gerada via Sphinx.

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
            [avaliadorId] [bigint] NULL,
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

[Apoio].[User] é para o controle de usuários e [Apoio],[log_auto] para o diário do sistema.

Outro detalhe sobre o banco de dados: Como o sistema conta com a funcionalidade de envio de dados, ele utiliza as views da API de Envio de Planos de Trabalho do Programa de Gestão (CADE/ME). O script de geração destas views está disponível no github do SISGP (https://github.com/spbgovbr/Sistema_Programa_de_Gestao_Susep).

