from fastapi import Response, status, HTTPException, Depends, APIRouter
import mysql.connector
from mysql.connector import errorcode
from .. import schemas, oauth2
from typing import List, Optional
from ..database import cursor, cnx

router = APIRouter(
    prefix="/features",
    tags=['Features']
)

########################################################### FEATURE ###########################################################
#   FEATURE uses SQL to query the db                                                                                          #
#   Feature[0] = Feature_id                                                                                                   #
#   Feature[1] = Named                                                                                                        #
#   Feature[2] = Description                                                                                                  #
#   Feature[3] = Added_by                                                                                                     #
#   Feature[4] = Created_at                                                                                                   #
###############################################################################################################################

### Get Features
@router.get("/", response_model=schemas.FeatureResponse)
def getFeatures(user: int = Depends(oauth2.getCurrentUser), limit:int = 10, skip:int = 0, search:Optional[str] = ""):
    cursor.execute("""SELECT FEATURE.Feature_id,
                             FEATURE.Named,
                             FEATURE.Description,
                             USER.Named,
                             PLACE.Named,
                             LOCATION.Named
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
        feature_responses.append(schemas.PlaceResponse(
        Feature_id=feature[0],
        Named=feature[1],
        Description=feature[2],
        Added_by=feature[3],
        Place=feature[4],
        Location=feature[5]
    ))
    return feature_responses

### get one feature by id
@router.get("/{id}", response_model=schemas.FeatureResponse)
def getFeatures(id: int, user: int=Depends(oauth2.getCurrentUser)):
    cursor.execute("""SELECT FEATURE.Feature_id,
                             FEATURE.Named,
                             FEATURE.Description,
                             USER.Named,
                             PLACE.Named,
                             LOCATION.Named
                      FROM FEATURE
                      LEFT JOIN `USER` ON FEATURE.Added_by = `USER`.User_id
                      LEFT JOIN FEATURES_AT_PLACE ON FEATURE.Feature_id = FEATURES_AT_PLACE.Feature_id
                      LEFT JOIN PLACE ON FEATURES_AT_PLACE.Place_id = PLACE.Place_id
                      LEFT JOIN PLACES_AT_LOCATION ON PLACE.Place_id = PLACES_AT_LOCATION.Place_id
                      LEFT JOIN LOCATION ON PLACES_AT_LOCATION.Location_id = LOCATION.Location_id
                      WHERE Feature_id = %s""", (id,))
    feature = cursor.fetchone()
    if not feature:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Feature with id: {id} was not found")
    return schemas.PlaceResponse(
        Feature_id=feature[0],
        Named=feature[1],
        Description=feature[2],
        Added_by=feature[3],
        Place=feature[4],
        Location=feature[5]
    )

