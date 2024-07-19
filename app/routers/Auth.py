from fastapi import APIRouter, Depends, status, HTTPException, Response
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
import mysql.connector
from mysql.connector import errorcode
from ..database import cursor, cnx
from .. import schemas, utils, oauth2


router = APIRouter(
    tags=['Authentication']
)

@router.post('/login', response_model=schemas.Token)
def Login(user_credentials: OAuth2PasswordRequestForm = Depends()):
    cursor.execute("""SELECT * FROM USER WHERE Username = %s""", (user_credentials.username,))
    user = cursor.fetchone()
    if not user: 
        cursor.execute("""SELECT * FROM USER WHERE Email = %s""", (user_credentials.username,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                                detail=f"Login Unsuccessful.")
    if not utils.verify(user_credentials.password, user[2]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                                detail=f"Login Unsuccessful.")
    
    # Create Token
    accesToken = oauth2.createAccessToken(data={"user_id": user[0]})
    #return token

    return {"Access_token": accesToken, "Token_type": "bearer"}