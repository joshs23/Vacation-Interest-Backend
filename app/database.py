from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from mysql.connector import pooling
from .config import settings

# Set up the connection pool
pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    user=settings.DB_USERNAME,
    host=settings.DB_HOST,
    password=settings.DB_PASSWORD,
    database=settings.DB_NAME
)

# SQLAlchemy setup
SQLALCHEMY_DATABASE_URL = (
    "mysql+mysqlconnector://%s:%s@%s/%s" % 
    (settings.DB_USERNAME, settings.DB_PASSWORD, settings.DB_HOST, settings.DB_NAME)
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_cursor():
    cnx = pool.get_connection()
    cursor = cnx.cursor(buffered=True)
    try:
        yield cursor, cnx
    finally:
        cursor.close()
        cnx.close()
