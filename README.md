# ApoioSisgp
Aplicativo de apoio à gestão do SISGP. Permite visualizar e atualizar dados das tabelas Unidade e Pessoa, de tabelas auxiliares (SituacaoPessoa, TipoFuncao, TipoVinculo e Feriado), além de outras funcionalidades.

Considerando que você tem o Python instalado em sua máquina, baixe os arquivos deste repositório. 
Lembre-se de criar um ambiente para o sistema. Os arquivos requirements.txt ou environment.yml podem ser úteis nisto, mas deverão ser ajustados para o seu caso.
Como o código é reaproveitado de um projeto anterior, pode ocorrer de ter mais pacotes instalados do que o realmente necessário, mas isto não é um impedimento.
Certifique-se que o pacote pyodbc está instalado: pip install pyodbc

Na pasta Instance, há o arquivo flask exemplo.cfg. Este deve ser ajustado para o seu caso e renomeado para flask.cfg.

Como este sistema faz controle de acesso e registra o log dos commits realizados, é necessário criar duas tabelas no 
DBSISGP. Abaixo seguem as instruções SQL para tal:

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

Outra forma de disponibilizar este aplicativo para os que não tem o Python instalado e por meio do Pyinstaller. Ele agrega o projeto e todas as suas dependências
em um único arquivo executável. Com o pyinstaller instalado, crie este .exe com o comando pyinstaller --onefile app.spec.

O app.spec neste repositório contém as configurações necessárias para a geração do .exe com sucesso, mas precisa ajustar o pathex para o teu caso.
Se tudo funcionar, será gerado o arquvo app.exe, na pasta dist. Renomeie ele com o nome que quiser e passe para os demais que irão gerenciar o sistema. 
Eles deverão ter a mesma versão do driver ODBC que você usou para gerar o executável.
