# syntax=docker/dockerfile:1

FROM python:3.9-bullseye

LABEL vendor="ApoioSisgp" maintainer="Cimei" description="Aplicativo Python-Flask de apoio à gestão do SISGP" version="3.0.2"

WORKDIR /app

ENV PYTHONIOENCODING=utf-8

ENV TZ="America/Sao_Paulo"

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update

# estabelece padrão brasileiro no locale
RUN apt-get install -y locales locales-all --no-install-recommends apt-utils
ENV LC_ALL pt_BR.UTF-8
ENV LANG pt_BR.UTF-8
ENV LANGUAGE pt_BR.UTF-8

# install FreeTDS and dependencies
# RUN apt-get install unixodbc -y \
#  && apt-get install unixodbc-dev -y \
#  && apt-get install freetds-dev -y \
#  && apt-get install freetds-bin -y \
#  && apt-get install tdsodbc -y \
#  && apt-get install --reinstall build-essential -y

# populate "ocbcinst.ini" as this is where ODBC driver config sits
# RUN echo "[FreeTDS]\n\
# Description = FreeTDS Driver\n\
# Driver = /usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so\n\
# Setup = /usr/lib/x86_64-linux-gnu/odbc/libtdsS.so" >> /etc/odbcinst.ini

# RUN echo "[postgresql]\n\
# Description = General ODBC for PostgreSQL\n\
# Driver      = /usr/lib64/libodbcpsql.so\n\
# Setup       = /usr/lib64/libodbcpsqlS.so\n\
# FileUsage   = 1\n\
# Threading   = 2" >> /etc/odbcinst.ini

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip

#Pip command without proxy setting
RUN pip install -r requirements.txt

COPY . .

RUN chmod +x ./entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["sh", "entrypoint.sh"]
