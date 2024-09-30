from fastapi import Response, status, HTTPException, Depends, APIRouter
import mysql.connector
from mysql.connector import errorcode
from .. import schemas, oauth2, utils
from typing import List, Optional
from ..database import get_cursor

router = APIRouter(
    prefix="/reviews",
    tags=['Reviews']
)

### Functions for REVIEWS_OF_FEATURE table
### i.e. maps review to each feature
###################################################### REVIEWS_OF_FEATURE ######################################################
#   REVIEWS_OF_FEATURE uses SQL to query the db                                                                                #
#   reviews[0] = Review_id                                                                                                    #
#   reviews[1] = Feature_id                                                                                                   #
#   reviews[2] = Created_at                                                                                                   #
###############################################################################################################################

def addReviewToFeature(Review_id: int, Feature_id: int, User_id: int, cursor):
    try:
        cursor.execute("""INSERT INTO REVIEWS_OF_FEATURE (Review_id, Feature_id, User_id) 
                      VALUES (%s, %s, %s)""", (Review_id, Feature_id, User_id))
        return

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_DUP_ENTRY:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Review of Feature by user already exists")
        else:
            print(err)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Internal server error occurred while adding Review to Feature")

########################################################### REVIEW ############################################################
#   REVIEW uses SQL to query the db                                                                                           #
#   Review[0] = Review_id                                                                                                     #
#   Review[1] = Review_score                                                                                                  #
#   Review[2] = User_comment                                                                                                  #
#   Review[3] = User_id                                                                                                       #
#   Review[4] = Created_at                                                                                                    #
###############################################################################################################################

### Get Reviews
@router.get("/", response_model=List[schemas.ReviewResponse])
def getReviews(user: int = Depends(oauth2.getCurrentUser), cursor_and_cnx=Depends(get_cursor), 
                limit:int = 10, skip:int = 0, search:Optional[str] = ""):
    cursor, _ = cursor_and_cnx
    cursor.execute("""SELECT REVIEW.Review_id,
                             REVIEW.Review_score,
                             REVIEW.User_comment,
                             REVIEW.Created_at,
                             FEATURE.Named AS Feature,
                             `USER`.Username AS Username,
                             PLACE.Named AS Place,
                             LOCATION.Named AS Location
                      FROM REVIEW
                      LEFT JOIN REVIEWS_OF_FEATURE ON REVIEW.Review_id = REVIEWS_OF_FEATURE.Review_id
                      LEFT JOIN FEATURE ON REVIEWS_OF_FEATURE.Feature_id = FEATURE.Feature_id
                      LEFT JOIN `USER` ON REVIEWS_OF_FEATURE.User_id = `USER`.User_id
                      LEFT JOIN FEATURES_AT_PLACE ON FEATURE.Feature_id = FEATURES_AT_PLACE.Feature_id
                      LEFT JOIN PLACE ON FEATURES_AT_PLACE.Place_id = PLACE.Place_id
                      LEFT JOIN PLACES_AT_LOCATION ON PLACE.Place_id = PLACES_AT_LOCATION.Place_id
                      LEFT JOIN LOCATION ON PLACES_AT_LOCATION.Location_id = LOCATION.Location_id
                      WHERE FEATURE.Named LIKE %s
                      LIMIT %s OFFSET %s """, ('%' + search + '%', limit, skip))
    reviews = cursor.fetchall()
    review_responses = []
    for review in reviews:
        review_responses.append(schemas.ReviewResponse(
        Review_id=review[0],
        Review_score=review[1],
        User_comment=review[2],
        Created_at=review[3],
        Feature_name=review[4],
        Username=review[5],
        Place_name=review[6],
        Location_name=review[7]
    ))
    return review_responses

### get one review by id
@router.get("/{id}", response_model=schemas.ReviewResponse)
def getReview(id: int, user: int=Depends(oauth2.getCurrentUser), cursor_and_cnx=Depends(get_cursor)):
    cursor, _ = cursor_and_cnx
    cursor.execute("""SELECT REVIEW.Review_id,
                             REVIEW.Review_score,
                             REVIEW.User_comment,
                             REVIEW.Created_at,
                             FEATURE.Named AS Feature,
                             `USER`.Username AS Username,
                             PLACE.Named AS Place,
                             LOCATION.Named AS Location
                      FROM REVIEW
                      LEFT JOIN REVIEWS_OF_FEATURE ON REVIEW.Review_id = REVIEWS_OF_FEATURE.Review_id
                      LEFT JOIN FEATURE ON REVIEWS_OF_FEATURE.Feature_id = FEATURE.Feature_id
                      LEFT JOIN `USER` ON REVIEWS_OF_FEATURE.User_id = `USER`.User_id
                      LEFT JOIN FEATURES_AT_PLACE ON FEATURE.Feature_id = FEATURES_AT_PLACE.Feature_id
                      LEFT JOIN PLACE ON FEATURES_AT_PLACE.Place_id = PLACE.Place_id
                      LEFT JOIN PLACES_AT_LOCATION ON PLACE.Place_id = PLACES_AT_LOCATION.Place_id
                      LEFT JOIN LOCATION ON PLACES_AT_LOCATION.Location_id = LOCATION.Location_id
                      WHERE REVIEW.Review_id = %s""", (id,))
    review = cursor.fetchone()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Feature with id: {id} was not found")
    return schemas.FeatureResponse(
        Review_id=review[0],
        Review_score=review[1],
        User_comment=review[2],
        Created_at=review[3],
        Feature_name=review[4],
        Username=review[5],
        Place_name=review[6],
        Location_name=review[7]
    )

### Add a Review
@router.post("/", status_code=status.HTTP_201_CREATED)
def addReview(new_review: schemas.NewReview, current_user: int=Depends(oauth2.getCurrentUser), 
               cursor_and_cnx=Depends(get_cursor)):
    cursor, cnx = cursor_and_cnx
    try:
        cursor.execute("""INSERT INTO REVIEW (Review_score, User_comment)
                          VALUES (%s, %s)""", (new_review.Review_score, new_review.User_comment))
        # Perform a SELECT query to fetch the added review
        cursor.execute("SELECT * FROM REVIEW WHERE Review_id = LAST_INSERT_ID()")
        added_review = cursor.fetchone()
        if ((added_review[1] != new_review.Review_score) or 
            (added_review[2] != new_review.User_comment)):
            cnx.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Internal server error occurred.1")
        Review_id = added_review[0]
        addReviewToFeature(Review_id, new_review.Feature_id, current_user.User_id, cursor=cursor)
        cnx.commit()

    except mysql.connector.Error as err:
        print(err)
        cnx.rollback()
        if err.errno == errorcode.ER_DUP_ENTRY:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"ERROR: review already exists")
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Internal server error occurred.")
    cursor.execute("""SELECT REVIEW.Review_id,
                             REVIEW.Review_score,
                             REVIEW.User_comment,
                             REVIEW.Created_at,
                             FEATURE.Named AS Feature,
                             `USER`.Username AS Username,
                             PLACE.Named AS Place,
                             LOCATION.Named AS Location
                      FROM REVIEW
                      LEFT JOIN REVIEWS_OF_FEATURE ON REVIEW.Review_id = REVIEWS_OF_FEATURE.Review_id
                      LEFT JOIN FEATURE ON REVIEWS_OF_FEATURE.Feature_id = FEATURE.Feature_id
                      LEFT JOIN `USER` ON REVIEWS_OF_FEATURE.User_id = `USER`.User_id
                      LEFT JOIN FEATURES_AT_PLACE ON FEATURE.Feature_id = FEATURES_AT_PLACE.Feature_id
                      LEFT JOIN PLACE ON FEATURES_AT_PLACE.Place_id = PLACE.Place_id
                      LEFT JOIN PLACES_AT_LOCATION ON PLACE.Place_id = PLACES_AT_LOCATION.Place_id
                      LEFT JOIN LOCATION ON PLACES_AT_LOCATION.Location_id = LOCATION.Location_id
                      WHERE REVIEW.Review_id = %s""", (Review_id,))
    review = cursor.fetchone()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Feature with id: {id} was not found")
    return schemas.ReviewResponse(
        Review_id=review[0],
        Review_score=review[1],
        User_comment=review[2],
        Created_at=review[3],
        Feature_name=review[4],
        Username=review[5],
        Place_name=review[6],
        Location_name=review[7]
    )

### Update Review score or body - must be owner
@router.put("/{id}")
def updateReview(id: int, update: schemas.UpdateReview, current_user: int = Depends(oauth2.getCurrentUser), 
                cursor_and_cnx=Depends(get_cursor)):
    cursor, cnx = cursor_and_cnx
    if(not utils.checkOwner(id, current_user.User_id, cursor, table="REVIEW", owner_column="Review_id")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Unauthorized action.")
    try:
        if(update.Review_score):
            cursor.execute("""UPDATE REVIEW SET Review_score = %s WHERE Review_id = %s""", (update.Review_score, id))
            cnx.commit()
        if(update.User_comment):
            cursor.execute("""UPDATE REVIEW SET User_comment = %s WHERE Review_id = %s""", (update.User_comment, id))
            cnx.commit()
    except mysql.connector.Error as err:
        cnx.rollback
        print(err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Internal server error occurred.")
    if cursor.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Review with id: {id} was not found")

    return {"Updated": True}

### Delete Review
@router.delete("/{id}")
def removeReview(id: int, current_user: int = Depends(oauth2.getCurrentUser),cursor_and_cnx=Depends(get_cursor)):
    cursor, cnx = cursor_and_cnx
    if(not utils.checkOwner(id, current_user.User_id, cursor, table="REVIEW", owner_column="Review_id")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Unauthorized action.")
    cursor.execute("""SELECT * FROM REVIEW WHERE Review_id = %s""", (id,))
    deleted_review = cursor.fetchone()

    if deleted_review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Review with id: {id} was not found")
    cursor.execute("""DELETE FROM REVIEW WHERE Review_id = %s""", (id,))
    cnx.commit()

    return Response(status_code= status.HTTP_204_NO_CONTENT)