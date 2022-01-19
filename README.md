# ApoioSisgp
Aplicativo de apoio à gestão do SISGP. Permite visualizar e atualizar dados de Unidades e Pessoas, bem como de tabelas auxiliares.

Considerando que você tem o Python instalado em sua máquina, baixe os arquivos deste repositório. 
Lembre-se de criar um ambiente para o sistema. Os arquivos requirements.txt ou environment.yml podem ser úteis nisto, mas deverão ser ajustados para o seu caso.
Como o código é reaproveitado de um projeto anteior, pode ocorrer de ter mais pacotes instalados do que o realmente necessário, mas isto não é um impedimento.
Certifique-se que o pacore pyodbc está instalado: pip install pyodbc

Será necessário criar sob na pasta ApoioSisgp a pasta Instance. Nesta pasta crie o arquivo flask.cfg.

É neste arquivo que você deverá informar a string de acesso ao seu banco DBSISGP. Veja abaixo o conteúdo mínimo deste arquivo. Altere params para o seu caso:

      # flask.cfg

      import urllib

      # Used a random number generator

      SECRET_KEY = '\x8b\xe5\xdb\x17\xe8\x93h\\\xae\xe8\x13e.\xb0\xabU\xdc\xf8q\xf4\xef>~\xce'

      ####################
      ## SQL DATABASE   ##
      ####################

      params = urllib.parse.quote_plus("DRIVER={<driver>};\
                                        SERVER=<servidor>;\
                                        DATABASE=<database>;\
                                        UID=<uid>;PWD=<pwd>")

      SQLALCHEMY_DATABASE_URI = "mssql+pyodbc:///?odbc_connect=%s" % params

      SQLALCHEMY_TRACK_MODIFICATIONS = False

      DEBUG = False
      #DEBUG = True

Em params:

<driver> 
      deverá corresponder à versão que está instalada em sua máquina. Exemplo: ODBC Driver 17 for SQL Server.
<servidor> 
        é o local onde o DBSISGP foi instalado
<database> 
        é o nome do banco de dados. Se não foi alterado será DBSISGP
<uid> 
        é o usuário que acessa o banco de dados
<pwd> 
        é a senha deste usuário.
  
Outra forma de disponibilizar este aplicativo para os que não tem o Python instaldo e por meio do Pyinstaller. Ele agrega o projeot e todas as suas dependências
em um único arquivo .exe. Com o pyinstaller instalado, crie este .exe com o comando pyinstaller --onefile app.spec.
O app.spec neste repositório contém as configurações necessárias para a geração do .exe com sucesso, mas precisa ajustar o pathex para o teu caso.
Se tudo funcionar, será gerado o arquvo app.exe, na pasta dist. Renomeie ele com o nome que quiser e passe para os demais que irão gerenciar o sistema. 
Eles deverão ter a mesma versão do driver ODBC que você usou para gera o executável.
