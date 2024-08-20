from jose  import JWTError, jwt
from datetime import datetime, timedelta, timezone
from . import schemas
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from .database import cursor
from .config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

def createAccessToken(data: dict):
    toEncode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_MINUTES)
    toEncode.update({"exp": expire})

    token = jwt.encode(toEncode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token

def verifyAccessToken(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, settings.ALGORITHM)
        id: str = payload.get("user_id")

        if id is None:
            raise credentials_exception
        token_data = schemas.TokenData(id=id)
    except JWTError:
        raise credentials_exception
    
    return token_data
    
#   user[0]0 = User_id                                                                                                        #
#   user[1] = Username                                                                                                        #
#   user[3] = Email                                                                                                           #

def getCurrentUser(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                          detail='Could not validate credentials',
                                          headers={"WWW-Authenticate": "bearer"})
    
    token_data = verifyAccessToken(token, credentials_exception)
    cursor.execute("""SELECT * FROM USER WHERE User_id = %s""", (token_data.id,))
    user = cursor.fetchone()
    return schemas.CurrentUser(
        User_id=user[0],
        Username=user[1],
        Email=user[3]
    )

