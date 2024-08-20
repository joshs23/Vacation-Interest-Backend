from fastapi import Response, status, HTTPException, Depends, APIRouter
import mysql.connector
from mysql.connector import errorcode
from .. import schemas, oauth2
from typing import List, Optional
from ..database import cursor, cnx
from .Location import getLocation
from sqlalchemy.orm import Session
from ..database import get_db

router = APIRouter(
    prefix="/places",
    tags=['Places']
)

### Functions for Places at location table
### i.e. adding Space Needle to Seattle
##################################################### PLACES_AT_LOCATION ######################################################
#   PLACES_AT_LOCATION uses SQL to query the db                                                                               #
#   places[0] = Place_id                                                                                                      #
#   places[1] = Location_id                                                                                                   #
#   place[2] = Created_at                                                                                                     #
###############################################################################################################################

def addPlaceToLocation(Place_id: int, Location_id: int, user: int, db: Session):
    try:
        cursor.execute("""INSERT INTO PLACES_AT_LOCATION (Place_id, Location_id) 
                      VALUES (%s, %s)""", (Place_id, Location_id))
        location = getLocation(id = Location_id,db=db, user=user)
        return location.Named

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_DUP_ENTRY:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Place already exists in Location")
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Internal server error occurred while adding Place to Location")
    
        

############################################################ PLACE ############################################################
#   PLACE uses SQL to query the db                                                                                            #
#   place[0] = Place_id                                                                                                       #
#   place[1] = Named                                                                                                          #
#   place[2] = Created_at                                                                                                     #
###############################################################################################################################

### Get Places
@router.get("/", response_model=List[schemas.PlaceResponse])
def getPlaces(user: int=Depends(oauth2.getCurrentUser), limit:int = 10, skip:int = 0, search:Optional[str] = ""):
    cursor.execute("""SELECT PLACE.Place_id,
                             PLACE.Named,
                             PLACE.Created_at,
                             LOCATION.Named
                      FROM PLACE
                      LEFT JOIN PLACES_AT_LOCATION ON PLACE.Place_id = PLACES_AT_LOCATION.Place_id
                      LEFT JOIN LOCATION ON PLACES_AT_LOCATION.Location_id = LOCATION.Location_id
                      WHERE PLACE.Named LIKE %s
                      LIMIT %s OFFSET %s """, ('%' + search + '%', limit, skip))
    places = cursor.fetchall()
    place_responses = []
    for place in places:
        place_responses.append(schemas.PlaceResponse(
        Place_id=place[0],
        Named=place[1],
        Created_at=place[2],
        Location_name=place[3]
    ))
    return place_responses

@router.get("/{id}", response_model=schemas.PlaceResponse)
def getPlace(id: int, user: int=Depends(oauth2.getCurrentUser)):
    cursor.execute("""SELECT PLACE.*,
                             LOCATION.Named
                      FROM PLACE
                      LEFT JOIN PLACES_AT_LOCATION ON PLACE.Place_id = PLACES_AT_LOCATION.Place_id
                      LEFT JOIN LOCATION ON PLACES_AT_LOCATION.Location_id = LOCATION.Location_id
                      WHERE PLACE.Place_id = %s""", (id,))
    place = cursor.fetchone()
    if not place:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Place with id: {id} was not found")
    return schemas.PlaceResponse(
        Place_id=place[0],
        Named=place[1],
        Created_at=place[2],
        Location_name=place[3]
    )

### Add a Place
@router.post("/", status_code=status.HTTP_201_CREATED)                          ### vv This part becasue of ORM vv
def addPlace(new_place: schemas.NewPlace, user: int=Depends(oauth2.getCurrentUser), db: Session = Depends(get_db)):
    try:
        cursor.execute("""INSERT INTO PLACE (Named)
                          VALUES (%s)""", (new_place.Named,))
        
        # Perform a SELECT query to fetch the added place
        cursor.execute("SELECT * FROM PLACE WHERE Named = %s", (new_place.Named,))
        added_place = cursor.fetchone()
        Place_id = added_place[0]
        Location_name = addPlaceToLocation(Place_id, new_place.Location_id, user=user, db=db)
        cnx.commit()

    except mysql.connector.Error as err:
        cnx.rollback()
        if err.errno == errorcode.ER_DUP_ENTRY:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"{new_place.Named} already exists")
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Internal server error occurred.")

    return schemas.PlaceResponse(
        Place_id=added_place[0],
        Named=added_place[1],
        Created_at=added_place[2],
        Location_name = Location_name
    )

### Delete a Place TODO: delete from PLACES_AT_LOCATION and FEATURES_AT_PLACE first
@router.delete("/{id}")
def removePlace(id: int, user: int=Depends(oauth2.getCurrentUser)):
    # Fetch the place details before deleting it to ensure it exists
    cursor.execute("""SELECT * FROM PLACE WHERE Place_id = %s""", (id,))
    deleted_place = cursor.fetchone()

    if deleted_place is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Place with id: {id} was not found")
    cursor.execute("""DELETE FROM PLACE WHERE Place_id = %s""", (id,))
    cnx.commit()

    return Response(status_code= status.HTTP_204_NO_CONTENT)

### Update a Place
@router.put("/{id}")
def changePlaceName(id: int, place: schemas.UpdatePlaceName, user: int=Depends(oauth2.getCurrentUser)):
    try:
        cursor.execute("""UPDATE PLACE SET Named = %s WHERE Place_id = %s""", (place.Named, id))
        cnx.commit()

    except mysql.connector.Error as err:
        cnx.rollback()
        if err.errno == errorcode.ER_DUP_ENTRY:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"{place.Named} already exists")

    # Check if any rows were affected by the update operation
    if cursor.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Place with id: {id} was not found")

    return {"Updated": True}
