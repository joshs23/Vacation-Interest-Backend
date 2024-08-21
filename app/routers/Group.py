from fastapi import status, HTTPException, Depends, APIRouter
import mysql.connector
from mysql.connector import errorcode
from .. import schemas, oauth2
from typing import List, Optional
from ..database import get_cursor

### Functions for users in group table
####################################################### USERS_IN_GROUP ########################################################
#   USERS_IN_GROUP uses SQL to query the db                                                                                   #
#   Users[0] = User_id                                                                                                        #
#   Users[1] = Group_id                                                                                                       #                                                                                                #
#   Users[2] = Created_at                                                                                                     #                                                          #
###############################################################################################################################
def addUserToGroup(User_id: int, Group_id: int, cursor):
    try:
        cursor.execute("""INSERT INTO USERS_IN_GROUP (User_id, Group_id) 
                        VALUES (%s, %s)""", (User_id, Group_id))
    except mysql.connector.Error as err:

        if err.errno == errorcode.ER_DUP_ENTRY:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="User already in group")
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Internal server error occurred while adding user to group")

router = APIRouter(
    prefix="/group",
    tags=['Group']
)

######################################################### USER_GROUP ##########################################################
#   USER_GROUP uses SQL to query the db                                                                                       #
#   group[0] = Group_id                                                                                                       #
#   group[1] = Group_name                                                                                                     #
#   group[2] = Owner_id                                                                                                       #
#   group[3] = Public_group                                                                                                   #
#   group[4] = Created_at                                                                                                     #
###############################################################################################################################

### get all user groups
@router.get("/", response_model=List[schemas.GroupResponse])
def getGroups(current_user: int=Depends(oauth2.getCurrentUser), cursor_and_cnx=Depends(get_cursor), 
              limit:int = 10, skip:int = 0, search:Optional[str] = ""):
    cursor, _ = cursor_and_cnx
    cursor.execute("""SELECT USER_GROUP.*,
                             USER.Username,
                             USER.Email,
                             USER.Created_at AS Owner_created_at
                      FROM USER_GROUP
                      LEFT JOIN `USER` ON USER_GROUP.Owner_id = `USER`.User_id
                      WHERE Group_name LIKE %s
                      AND Public_group = true
                      LIMIT %s OFFSET %s""", ('%' + search + '%', limit, skip))
    groups = cursor.fetchall()
    group_responses = []
    for group in groups:
        group_responses.append(schemas.GroupResponse(
            Group_id = group[0],
            Group_name = group[1],
            Owner_id = group[2],
            Public_group = group[3],
            Created_at = group[4], 
            Owner = schemas.GroupOwnerUser(
                Username = group[5],
                Email = group[6],
                Owner_created_at = group[7]
            )
        ))
    return group_responses

### Get a specific user group by group id
@router.get("/{id}", response_model=schemas.GroupResponse)
def getGroup(id: int, current_user: int=Depends(oauth2.getCurrentUser), cursor_and_cnx=Depends(get_cursor)):
    cursor, _ = cursor_and_cnx
    cursor.execute("""SELECT USER_GROUP.*,
                             USER.Username,
                             USER.Email,
                             USER.Created_at AS Owner_created_at
                      FROM USER_GROUP
                      LEFT JOIN `USER` ON USER_GROUP.Owner_id = `USER`.User_id
                      WHERE Group_id = %s""", (id,))
    group = cursor.fetchone()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Group with id: {id} was not found")
    Group_id, Group_name, Owner_id, Public_group, Created_at, Username, Email, Owner_created_at  = group
    return schemas.GroupResponse(
        Group_id = Group_id,
        Group_name = Group_name,
        Owner_id = Owner_id,
        Public_group = Public_group,
        Created_at = Created_at,
        Owner = schemas.GroupOwnerUser(
            Username = Username,
            Email = Email,
            Owner_created_at = Owner_created_at
        )
    )

### Create a user group
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.GroupResponse)
def createGroup(new_group: schemas.NewGroup, current_user: int=Depends(oauth2.getCurrentUser), 
                cursor_and_cnx=Depends(get_cursor)):
    cursor, cnx = cursor_and_cnx
    try:
        cursor.execute("""INSERT INTO USER_GROUP (Group_name, Owner_id, Public_group)
                       values (%s, %s, %s)""", (new_group.Group_name, current_user.User_id, new_group.Public_group))

        # Check to see if the group was added
        cursor.execute("""SELECT USER_GROUP.*,
                                 USER.Username,
                                 USER.Email,
                                 USER.Created_at AS Owner_created_at
                          FROM USER_GROUP 
                          LEFT JOIN `USER` ON USER_GROUP.Owner_id = `USER`.User_id
                          WHERE Group_name = %s""", (new_group.Group_name, ))
        added_group = cursor.fetchone()
        Group_id=added_group[0]
        addUserToGroup(current_user.User_id, Group_id, cursor=cursor)
        cnx.commit()
    except mysql.connector.Error as err:
        cnx.rollback()
        if err.errno == errorcode.ER_DUP_ENTRY:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"{new_group.Group_name} already exists")
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Internal server error occurred.")
        
    return schemas.GroupResponse(
        Group_id=added_group[0],
        Group_name=added_group[1],
        Owner_id=added_group[2],
        Public_group=added_group[3],
        Created_at=added_group[4],
        Owner = schemas.GroupOwnerUser(
            Username = added_group[5],
            Email = added_group[6],
            Owner_created_at = added_group[7]
        )
    )

### Update Group Owner
@router.put("/{id}")
def UpdateOwner(id: int, new_owner_id: schemas.UpdateGroupOwner, Current_user: int = Depends(oauth2.getCurrentUser), 
                cursor_and_cnx=Depends(get_cursor)):
    cursor, cnx = cursor_and_cnx
    try:
        cursor.execute("""UPDATE USER_GROUP SET Owner_id = %s WHERE Group_id = %s""", (new_owner_id.Owner_id, id))
        cnx.commit
    except mysql.connector.Error as err:
        cnx.rollback
        print(err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Internal server error occurred.")
    if cursor.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Group with id: {id} was not found")

    return {"Updated": True}

### Delete group

### Join Group