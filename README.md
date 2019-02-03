# Threaded TCP/IP Game Server (Python3)

### Run server

Prepare virtualenv and install requirements:

    $ mkvirtualenv -p /usr/bin/python3.5 server
    $ workon server
    $ pip install -r requirements.txt

Configure PostgreSQL DB and set necessary environment variables:

    $ export DB_USER=user DB_PASSWORD=password DB_HOST=127.0.0.1 DB_NAME=server_db

Initialize DB and generate game map:

    $ cd server
    $ invoke db-init
    $ invoke generate-map

Run server:

    $ invoke run-server -l DEBUG

### Run server with docker

Install docker-compose:

    $ pip install docker-compose

Create files with environment variables for DB ('pg.env') and server ('server.env'):

    $ cat > pg.env
    POSTGRES_DB=server_db
    POSTGRES_USER=user
    POSTGRES_PASSWORD=password
    
    $ cat > server.env
    SERVER_ADDR=0.0.0.0
    DB_HOST=pg
    DB_NAME=server_db
    DB_USER=user
    DB_PASSWORD=password

Run server:

    $ docker-compose up -d
