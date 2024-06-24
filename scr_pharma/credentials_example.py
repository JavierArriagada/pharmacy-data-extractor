USER = "user"
PASSWORD = "password"
IP = "localhost"
BD_NAME = "analitica"

SQLALCHEMY_DATABASE_URI ='mysql+pymysql://{}:{}@localhost:3306/{}'.format(USER,PASSWORD,BD_NAME)

