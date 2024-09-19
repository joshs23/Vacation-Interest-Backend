from fastapi import status, HTTPException, Depends, APIRouter
import mysql.connector
from mysql.connector import errorcode
from .. import schemas, oauth2
from typing import List, Optional
from ..database import get_cursor
from . import Place

router = APIRouter(
    prefix="/features",
    tags=['Features']
)

### Functions for FEATURES_AT_PLACE table
### i.e. adding Space Needle observation deck to Space Needle
###################################################### FEATURES_AT_PLACE ######################################################
#   FEATURES_AT_PLACE uses SQL to query the db                                                                                #
#   features[0] = Feature_id                                                                                                  #
#   features[1] = Place_id                                                                                                    #
#   features[2] = Created_at                                                                                                  #
###############################################################################################################################

def addFeatureToPlace(Feature_id: int, Place_id: int, cursor):
    try:
        cursor.execute("""INSERT INTO FEATURES_AT_PLACE (Feature_id, Place_id) 
                      VALUES (%s, %s)""", (Feature_id, Place_id))
        place = Place.getPlace(id = Place_id)
        return [place.Named, place.Location_name]

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_DUP_ENTRY:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Feature already exists in Place")
        else:
            print(err)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Internal server error occurred while adding Feature to Place")

########################################################### FEATURE ###########################################################
#   FEATURE uses SQL to query the db                                                                                          #
#   Feature[0] = Feature_id                                                                                                   #
#   Feature[1] = Named                                                                                                        #
#   Feature[2] = Description                                                                                                  #
#   Feature[3] = Added_by                                                                                                     #
#   Feature[4] = Created_at                                                                                                   #
###############################################################################################################################

### Get Features
@router.get("/", response_model=List[schemas.FeatureResponse])
def getFeatures(user: int = Depends(oauth2.getCurrentUser), cursor_and_cnx=Depends(get_cursor), 
                limit:int = 10, skip:int = 0, search:Optional[str] = ""):
    cursor, _ = cursor_and_cnx
    cursor.execute("""SELECT FEATURE.Feature_id,
                             FEATURE.Named,
                             FEATURE.Description,
                             FEATURE.Created_at,
                             `USER`.Username,
                             PLACE.Named AS Place,
                             LOCATION.Named AS Location
                      FROM FEATURE
                      LEFT JOIN `USER` ON FEATURE.Added_by = `USER`.User_id
                      LEFT JOIN FEATURES_AT_PLACE ON FEATURE.Feature_id = FEATURES_AT_PLACE.Feature_id
                      LEFT JOIN PLACE ON FEATURES_AT_PLACE.Place_id = PLACE.Place_id
                      LEFT JOIN PLACES_AT_LOCATION ON PLACE.Place_id = PLACES_AT_LOCATION.Place_id
                      LEFT JOIN LOCATION ON PLACES_AT_LOCATION.Location_id = LOCATION.Location_id
                      WHERE FEATURE.Named LIKE %s
                      LIMIT %s OFFSET %s """, ('%' + search + '%', limit, skip))
    features = cursor.fetchall()
    feature_responses = []
    for feature in features:
        feature_responses.append(schemas.FeatureResponse(
        Feature_id=feature[0],
        Named=feature[1],
        Description=feature[2],
        Created_at=feature[3],
        Added_by=feature[4],
        Place=feature[5],
        Location=feature[6]
    ))
    return feature_responses

### get one feature by id
@router.get("/{id}", response_model=schemas.FeatureResponse)
def getFeature(id: int, user: int=Depends(oauth2.getCurrentUser), cursor_and_cnx=Depends(get_cursor)):
    cursor, _ = cursor_and_cnx
    cursor.execute("""SELECT FEATURE.Feature_id,
                             FEATURE.Named,
                             FEATURE.Description,
                             FEATURE.Created_at,
                             USER.Username,
                             PLACE.Named,
                             LOCATION.Named
                      FROM FEATURE
                      LEFT JOIN `USER` ON FEATURE.Added_by = `USER`.User_id
                      LEFT JOIN FEATURES_AT_PLACE ON FEATURE.Feature_id = FEATURES_AT_PLACE.Feature_id
                      LEFT JOIN PLACE ON FEATURES_AT_PLACE.Place_id = PLACE.Place_id
                      LEFT JOIN PLACES_AT_LOCATION ON PLACE.Place_id = PLACES_AT_LOCATION.Place_id
                      LEFT JOIN LOCATION ON PLACES_AT_LOCATION.Location_id = LOCATION.Location_id
                      WHERE FEATURE.Feature_id = %s""", (id,))
    feature = cursor.fetchone()
    if not feature:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Feature with id: {id} was not found")
    return schemas.FeatureResponse(
        Feature_id=feature[0],
        Named=feature[1],
        Description=feature[2],
        Created_at=feature[3],
        Added_by=feature[4],
        Place=feature[5],
        Location=feature[6]
    )

### Add a Feature
@router.post("/", status_code=status.HTTP_201_CREATED)
def addFeature(new_feature: schemas.NewFeature, current_user: int=Depends(oauth2.getCurrentUser), 
               cursor_and_cnx=Depends(get_cursor)):
    cursor, cnx = cursor_and_cnx
    try:
        cursor.execute("""INSERT INTO FEATURE (Named, Description, Added_by)
                          VALUES (%s, %s, %s)""", (new_feature.Named, new_feature.Description, current_user.User_id))
        
        # Perform a SELECT query to fetch the added feature
        cursor.execute("SELECT * FROM FEATURE WHERE Named = %s", (new_feature.Named,))
        added_feature = cursor.fetchone()
        Feature_id = added_feature[0]
        PlaceAndLocationName = addFeatureToPlace(Feature_id, new_feature.Place_id, cursor=cursor)
        cnx.commit()

    except mysql.connector.Error as err:
        cnx.rollback()
        if err.errno == errorcode.ER_DUP_ENTRY:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"{new_feature.Named} already exists")
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Internal server error occurred.")

    return schemas.FeatureResponse(
        Feature_id=added_feature[0],
        Named=added_feature[1],
        Description=added_feature[2],
        Added_by=current_user.Username,
        Created_at=added_feature[4],
        Place=PlaceAndLocationName[0],
        Location=PlaceAndLocationName[1]
    )

### TODO Update name, update description, delete feature