# Flask SQLAlchemy Simple App

It is an example of simple web-backend app which is connected to the PostgreSQL DB via Flask_SQLAlchemy library. The app was created as a test assignment for DevOps Engineer position.
It is bundled with docker-compose file for local deployment and a Helm chart for k8s one.

## Prerequisites 

- Docker and docker-compose
- Git
- Minikube
- Helm 3

## Deployment preparation

Clone this repository to your server:
```
git clone https://github.com/dpilin/flask_sqlalchemy_simple_app.git
```

Build a simple-ban-app Docker image:
```
docker-compose build simple-ban-app
```

## Local deployment via docker-compose

First of all, you have to export the next environment variables or put them to the .env file next to the docker-compose.yml (feel free to set your own values):
```
SIMPLE_APP_DB_HOST="localhost"
SIMPLE_APP_DB_PORT=5432
SIMPLE_APP_DB_NAME="simpledb"
SIMPLE_APP_DB_USER="simpleuser"
SIMPLE_APP_DB_PASSWORD="simplepassword"
SIMPLE_APP_SMTP_SERVER="localhost"
SIMPLE_APP_DB_REPLICATION_USER="simplereplicauser"
SIMPLE_APP_DB_REPLICATION_PASSWORD="simplereplicapassword"
```

Deploy the application, database, its replica and smtp server:
```
docker-compose up -d
```

As it is a local deployment for testing purposes, both master and replica DBs can be accessed using the psql client (localhost:5432 for master and localhost:5433 for replica). The app is listening on the http://localhost:5000 

## Kubernetes deployment via Helm

The application's chart includes subcharts for DB, its replica and a SMTP server. All required environment variables are parametrized and put to the chart's and subcharts' values.yaml file (the full list of variables can be seen in the previous paragraph). 

For basic deployment you should just install the chart:

```
helm install simple_ban_app_chart
```

If the installation succeded, you will see the next deployments in the cluster:
```
$ kubectl get deployments
NAME                   READY   UP-TO-DATE   AVAILABLE   AGE
bytemark-smtp-server   1/1     1            1           4m52s
postgres-master        1/1     1            1           4m52s
postgres-replica       1/1     1            1           4m52s
simple-ban-app         1/1     1            1           4m52s
```

The only exposed service here is the application itself. For simplicity, the NodePort was used. You can obtain the application URL using the next command in the shell:
```
$ echo http://$(minikube node list | awk -F ' ' '{print $2}'):$(kubectl get service "simple-ban-app" --output='jsonpath="{.spec.ports[0].nodePort}"' | sed 's/"//g')
http://192.168.49.2:31329
```
You can also export the output to an environment variable for convenience.

## Endpoints description 

The web-app has two endpoint for different purposes:
| Endpoint | Purpose |
| ------ | ------ |
| /?n=x | Return the square of the x |
| /blackilisted | Ban the requestor's IP and write it to the DB. Then send an email to test@domain.com|

## Usage example (based on local deployment)

Obtain the list of the running containers:
```
$ docker ps
CONTAINER ID   IMAGE                    COMMAND                  CREATED         STATUS                           PORTS                                                                                                                                  NAMES
9698a37d4885   simplebanapp:1           "/bin/sh -c '/usr/lo…"   3 seconds ago   Up 1 second (health: starting)   0.0.0.0:5000->5000/tcp                                                                                                                 flask_sqlalchemy_simple_app_simple-ban-app_1
000af83f57de   bitnami/postgresql:14    "/opt/bitnami/script…"   3 seconds ago   Up 2 seconds                     0.0.0.0:5433->5432/tcp                                                                                                                 flask_sqlalchemy_simple_app_postgresql-replica_1
31bcab57bb15   bytemark/smtp            "docker-entrypoint.s…"   4 seconds ago   Up 3 seconds                     25/tcp                                                                                                                                 flask_sqlalchemy_simple_app_bytemark-smtp-server_1
e020ecab90b7   bitnami/postgresql:14    "/opt/bitnami/script…"   4 seconds ago   Up 2 seconds                     0.0.0.0:5432->5432/tcp                                                                                                                 flask_sqlalchemy_simple_app_postgresql-master_1
```

Check that a number's square is calculated correctly:
```
$ curl http://localhost:5000/?n=10
{"result": 100}
```

Check that your IP is banned in the DB after request to /blacklisted endpoint:
```
$ curl http://localhost:5000/blacklisted
{"result": "From now on your IP address (192.168.96.1) is banned"}
$ curl http://localhost:5000/blacklisted
{"result": "Access from your IP address (192.168.96.1) is forbidden"}
```

Check that the email was sent using the application container's logs: 
```
[2022-03-25 17:43:45 +0000] [8] [DEBUG] GET /blacklisted
[2022-03-25 17:43:45 +0000] [8] [INFO] Received an incoming request to /blacklisted
[2022-03-25 17:43:45 +0000] [8] [DEBUG] The visitor's ip is 192.168.96.1
[2022-03-25 17:43:45 +0000] [8] [DEBUG] The next record will be added to the blocklist table: <BlockList (transient 139744419598192)>
[2022-03-25 17:43:45 +0000] [8] [DEBUG] The record was successfully saved in the database
[2022-03-25 17:43:45 +0000] [8] [DEBUG] Preparing an email with banned IP
[2022-03-25 17:43:45 +0000] [8] [DEBUG] Email was formed, here is its content:

Content-Type: text/plain; charset="us-ascii"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Subject: New IP was banned
From: simple_ban_app@python
To: test@domain.com

The next IP address was banned at 2022-03-25 17:43:45.953977: 192.168.96.1
```

Check that the appropriate record was created in the master DB:
```
# psql -h localhost -p 5432 -d simpledb -U simpleuser
Password for user simpleuser:
...
simpledb=> SELECT * FROM blocklist;
 id |     path     |    ip     |         timestamp          
----+--------------+-----------+----------------------------
  1 | /blacklisted | 192.168.96.1 | 2022-03-25 17:43:45.953977
(1 row)
```
Check that the replica DB has cloned the record:
```
# psql -h localhost -p 5433 -d simpledb -U simpleuser
Password for user simpleuser:
...
simpledb=> SELECT * FROM blocklist;
 id |     path     |    ip     |         timestamp          
----+--------------+-----------+----------------------------
  1 | /blacklisted | 192.168.96.1 | 2022-03-25 17:43:45.953977
(1 row)
```
