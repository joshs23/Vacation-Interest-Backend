from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import time
import mysql.connector
from .config import settings

def create_db_connection():
    while True:

        try:
            cnx = mysql.connector.connect(user=settings.DB_USERNAME, 
                                        host=settings.DB_HOST, 
                                        password=settings.DB_PASSWORD, 
                                        database=settings.DB_NAME)
            print(("DATABASE: Connection success"))
            return cnx
            break
        except Exception as error: 
            print("connection failure")
            print("Error: ", error)
            time.sleep(5)

SQLALCHEMY_DATABASE_URL = ("mysql+mysqlconnector://%s:%s@%s/%s" % (settings.DB_USERNAME, 
                                                                   settings.DB_PASSWORD, 
                                                                   settings.DB_HOST, 
                                                                   settings.DB_NAME))

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_cursor():
    cnx = create_db_connection()
    cursor = cnx.cursor(buffered=True)
    try:
        yield cursor, cnx
    finally:
        cursor.close()
        cnx.close()