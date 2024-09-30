from passlib.context import CryptContext
from fastapi import status, HTTPException
import mysql.connector
from mysql.connector import errorcode

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash(password: str):
    return pwd_context.hash(password)

def verify(plain_pwd: str, hashed_pwd: str):
    return pwd_context.verify(plain_pwd, hashed_pwd)

### Helper function to check group owner for updates and deletes
def checkOwner(group_id, current_user_id, cursor, table, owner_column):
    isOwner = False
    try:
        query = f"""SELECT Owner_id
                          FROM {table}
                          WHERE {owner_column} = %s"""
        cursor.execute(query, (group_id, ))
        owner = cursor.fetchone()
        if owner is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")
        if(owner[0] == current_user_id):
            isOwner = True

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_DUP_ENTRY:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Group not found.")
        else:
            print(err)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Internal server error occurred.")
    return isOwner