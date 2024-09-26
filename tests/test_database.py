from fastapi.testclient import TestClient
from app.main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from mysql.connector import pooling
from app.config import settings
from app.database import get_db, get_cursor
import mysql.connector


db_name = f"{settings.DB_NAME}_test"

pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    user=settings.DB_USERNAME,
    host=settings.DB_HOST,
    password=settings.DB_PASSWORD,
    database=db_name
)

# SQLAlchemy setup
SQLALCHEMY_DATABASE_URL = (
    "mysql+mysqlconnector://%s:%s@%s/%s_test" % 
    (settings.DB_USERNAME, settings.DB_PASSWORD, settings.DB_HOST, settings.DB_NAME)
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_cursor():
    cnx = pool.get_connection()
    cursor = cnx.cursor(buffered=True)
    try:
        yield cursor, cnx
    finally:
        cursor.close()
        cnx.close()

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_cursor] = override_get_cursor

client = TestClient(app)

def drop_all():
    try:
        cnx = mysql.connector.connect(user=settings.DB_USERNAME, 
                                      host=settings.DB_HOST, 
                                      password=settings.DB_PASSWORD, 
                                      database=db_name)
        cursor = cnx.cursor(buffered=True)
    except Exception as error: 
        print("connection failure")
        print(error)
    try:
        cursor.execute("SET foreign_key_checks = 0;")
    
        # Get all table names
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()

        # Drop each table
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS `{table[0]}`;")

        # Re-enable foreign key checks
        cursor.execute("SET foreign_key_checks = 1;")
        cnx.commit()
    except Exception as e:
        print(f"Error during drop_all: {e}")
        raise

def create_all():
    try:
        cnx = mysql.connector.connect(user=settings.DB_USERNAME, 
                                      host=settings.DB_HOST, 
                                      password=settings.DB_PASSWORD, 
                                      database=db_name)
        cursor = cnx.cursor(buffered=True)
    except Exception as error: 
        print("connection failure")
        print(error)
    try:
        create_statements = [
            """
            CREATE TABLE USER (
                User_id INT UNSIGNED AUTO_INCREMENT NOT NULL,
                Username VARCHAR(50) NOT NULL UNIQUE,
                Password_hash VARCHAR(60) NOT NULL,
                Email VARCHAR(100) NOT NULL UNIQUE,
                Created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (User_id)
            );
            """,
            """
            CREATE TABLE USER_GROUP (
                Group_id INT UNSIGNED AUTO_INCREMENT NOT NULL,
                Group_name VARCHAR(50) NOT NULL UNIQUE,
                Owner_id INT UNSIGNED NOT NULL,
                Public_group TINYINT NOT NULL,
                Created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (Group_id),
                FOREIGN KEY (Owner_id) REFERENCES USER(User_id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE USERS_IN_GROUP (
                User_id INT UNSIGNED NOT NULL,
                Group_id INT UNSIGNED NOT NULL,
                Created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (User_id, Group_id),
                FOREIGN KEY (User_id) REFERENCES USER(User_id) ON DELETE CASCADE,
                FOREIGN KEY (Group_id) REFERENCES USER_GROUP(Group_id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE LOCATION (
                Location_id INT UNSIGNED AUTO_INCREMENT NOT NULL,
                Named VARCHAR(50) NOT NULL UNIQUE,
                Created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (Location_id)
            );
            """,
            """
            CREATE TABLE PLACE (
                Place_id INT UNSIGNED AUTO_INCREMENT NOT NULL,
                Named VARCHAR(50) UNIQUE,
                Created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (Place_id)
            );
            """,
            """
            CREATE TABLE PLACES_AT_LOCATION (
                Place_id INT UNSIGNED NOT NULL,
                Location_id INT UNSIGNED NOT NULL,
                Created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (Place_id),
                FOREIGN KEY (Place_id) REFERENCES PLACE(Place_id) ON DELETE CASCADE,
                FOREIGN KEY (Location_id) REFERENCES LOCATION(Location_id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE FEATURE (
                Feature_id INT UNSIGNED AUTO_INCREMENT NOT NULL,
                Named VARCHAR(50) NOT NULL UNIQUE,
                Description TEXT NOT NULL,
                Added_by INT UNSIGNED NOT NULL,
                Created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (Feature_id),
                FOREIGN KEY (Added_by) REFERENCES USER(User_id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE FEATURES_AT_PLACE (
                Feature_id INT UNSIGNED NOT NULL,
                Place_id INT UNSIGNED NOT NULL,
                Created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (Feature_id),
                FOREIGN KEY (Feature_id) REFERENCES FEATURE(Feature_id) ON DELETE CASCADE,
                FOREIGN KEY (Place_id) REFERENCES PLACE(Place_id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE REVIEW (
                Review_id INT UNSIGNED AUTO_INCREMENT NOT NULL,
                Review_score INT NOT NULL,
                User_comment TEXT,
                Created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (Review_id)
            );
            """,
            """
            CREATE TABLE REVIEWS_OF_FEATURE (
                Review_id INT UNSIGNED NOT NULL,
                Feature_id INT UNSIGNED NOT NULL,
                User_id INT UNSIGNED NOT NULL,
                Created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (Feature_id, User_id),
                FOREIGN KEY (Review_id) REFERENCES REVIEW(Review_id) ON DELETE CASCADE,
                FOREIGN KEY (Feature_id) REFERENCES FEATURE(Feature_id) ON DELETE CASCADE,
                FOREIGN KEY (User_id) REFERENCES USER(User_id) ON DELETE CASCADE
            );
            """
        ]

        for statement in create_statements:
            cursor.execute(statement)
        cnx.commit()
    except Exception as e:
        print(f"Error during create_all: {e}")
        raise