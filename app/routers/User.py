from fastapi import Response, status, HTTPException, Depends, APIRouter
import mysql.connector
from mysql.connector import errorcode
from .. import schemas, utils, oauth2
from typing import List, Optional
from ..database import cursor, cnx

router = APIRouter(
    prefix="/users",
    tags=['Users']
)

############################################################ USER #############################################################
#   USER uses SQL to query the db                                                                                             #
#   user[0]0 = User_id                                                                                                        #
#   user[1] = Username                                                                                                        #
#   user[3] = Email                                                                                                           #
#   user[4] = Created_at                                                                                                      #                                                          #
###############################################################################################################################

### Get Users
@router.get("/", response_model=List[schemas.UserResponse])
def getUsers(current_user: int=Depends(oauth2.getCurrentUser), search:Optional[str] = "", limit:int = 10, skip:int = 0):
    cursor.execute("""SELECT * FROM `USER` 
                      WHERE Named LIKE %s
                      LIMIT %s OFFSET %s """, ('%' + search + '%', limit, skip))
    users = cursor.fetchall()
    user_responses = []
    for user in users:
        user_responses.append(schemas.UserResponse(
            User_id=user[0],
            Username=user[1],
            Email=user[3],
            Created_at=user[4]
        ))
    return user_responses

@router.get("/{id}", response_model=schemas.UserResponse)
def getUser(id: int, current_user: int=Depends(oauth2.getCurrentUser)):
    cursor.execute("""SELECT * FROM `USER` WHERE User_id = %s""", (id,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {id} was not found")
    User_id, Username, _, Email, Created_at = user
    return schemas.UserResponse(
        User_id=User_id,
        Username=Username,
        Email=Email,
        Created_at=Created_at
    )

### Add a User
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.UserResponse)
def addUser(new_user: schemas.CreateUser):
    # Hash the password
    Hashed_password = utils.hash(new_user.Password_hash)
    new_user.Password_hash = Hashed_password

    try:
        cursor.execute("""INSERT INTO `USER` (Username, Email, Password_hash)
                    VALUES (%s, %s, %s)""", (new_user.Username, new_user.Email, new_user.Password_hash))
        # Commit the transaction to ensure the INSERT operation is persisted
        cnx.commit()
        
        # Perform a SELECT query to fetch the added place
        cursor.execute("SELECT * FROM `USER` WHERE Email = %s", (new_user.Email,))
        added_user = cursor.fetchone()
        User_id, Username, _, Email, Created_at = added_user
    except mysql.connector.Error as err:
        cnx.rollback()
        if err.errno == errorcode.ER_DUP_ENTRY:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"{new_user.Email} or {new_user.Username} already exists")
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Internal server error occurred.")

    return schemas.UserResponse(
        User_id=User_id,
        Username=Username,
        Email=Email,
        Created_at=Created_at
    )

### Update a Username
@router.put("/username")
def changeUserName(user: schemas.Username, current_user: int=Depends(oauth2.getCurrentUser)):
    try:
        cursor.execute("""UPDATE `USER` SET Username = %s WHERE User_id = %s""", (user.Username, current_user.User_id))
        cnx.commit()

    except mysql.connector.Error as err:
        cnx.rollback()
        if err.errno == errorcode.ER_DUP_ENTRY:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"{user.Username} already exists")

    # Check if any rows were affected by the update operation
    if cursor.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Username change unsuccessful.")

    return {"Updated": True}

### Update a Email
@router.put("/email")
def changeEmail(user: schemas.UserEmail, current_user: int=Depends(oauth2.getCurrentUser)):
    try:
        cursor.execute("""UPDATE `USER` SET Email = %s WHERE User_id = %s""", (user.Email, current_user.User_id))
        cnx.commit()
    except mysql.connector.Error as err:
        cnx.rollback()
        if err.errno == errorcode.ER_DUP_ENTRY:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"{user.Email} already exists")

    # Check if any rows were affected by the update operation
    if cursor.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Email change unsuccessful.")

    return {"Updated": True}

### Delete own account
@router.delete("/", response_model=schemas.UserResponse)
def removeUser(current_user: int=Depends(oauth2.getCurrentUser)):
    # Fetch the User details before deleting it to ensure it exists
    cursor.execute("""SELECT * FROM `USER` WHERE User_id = %s""", (current_user.User_id,))
    deleted_user = cursor.fetchone()

    if deleted_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Account deletion unsuccessful.")
    
    cursor.execute("""DELETE FROM `USER` WHERE User_id = %s""", (current_user.User_id,))
    cnx.commit()

    return Response(status_code= status.HTTP_204_NO_CONTENT)

