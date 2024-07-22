from fastapi import Response, status, HTTPException, Depends, APIRouter
from .. import models, schemas, oauth2
from sqlalchemy.orm import Session
from ..database import engine, get_db
from typing import List, Optional

router = APIRouter(
    prefix="/locations",
    tags=['Locations']
)

################################################################ LOCATION #####################################################
#   LOCATION uses ORM SQLAlchemy from tutorial I was following, while the rest use SQL code for more complex queries          #
###############################################################################################################################

### Get all Locations
@router.get("/", response_model=List[schemas.LocationResponse])
def getLocations(db: Session = Depends(get_db), user: int=Depends(oauth2.getCurrentUser), 
                 limit:int = 10, skip:int = 0, search: Optional[str] = ""):
    locations = db.query(models.Location).filter(models.Location.Named.contains(search)).limit(limit).offset(skip).all()
    return locations

### Get a Location by id
@router.get("/{id}", response_model=schemas.LocationResponse)
def getLocation(id: int, db: Session = Depends(get_db), user: int=Depends(oauth2.getCurrentUser)):
    location = db.query(models.Location).filter(models.Location.Location_id == id).first()
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Location with id {id} was not found")
    return location

### Add a Location
    # Takes Named column input in body
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.LocationResponse)
def addLocation(new_location: schemas.Location, db: Session = Depends(get_db), user: int=Depends(oauth2.getCurrentUser)):
    # try to add a location, catch if the name of the location is not unique, 
    # or if there is a server error
    try: 
        added_location = models.Location(**new_location.dict())
        db.add(added_location)
        db.commit()
        db.refresh(added_location)
    except Exception as e:
        db.rollback()
        error_message = str(e)
        if 'Duplicate entry' in error_message:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"{new_location.Named} already exists")
        else:
            print(e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Internal server error occurred.")
    return added_location

### Update a location name
    # Takes updated Named column input in body
@router.put("/{id}")
def changeLocationName(id: int, updated_location: schemas.Location, db: Session = Depends(get_db), user: int=Depends(oauth2.getCurrentUser)):
    try:
        location_query = db.query(models.Location).filter(models.Location.Location_id == id)
        location = location_query.first()
        if location is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Location with id: {id} was not found")
        location_query.update(updated_location.dict(), synchronize_session = False)
        db.commit()
    except Exception as e:
        db.rollback()
        error_message = str(e)
        if 'Duplicate entry' in error_message:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"{updated_location.Named} already exists")
        else:
            print(e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Internal server error occurred.")
    return {"Updated": True}

### Delete a location by id
@router.delete("/{id}", status_code= status.HTTP_204_NO_CONTENT)
def removeLocation(id: int, db: Session = Depends(get_db), user: int=Depends(oauth2.getCurrentUser)):
    location = db.query(models.Location).filter(models.Location.Location_id == id).first()

    if location is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Location with id: {id} was not found")
    db.delete(location)
    db.commit()

    return Response(status_code= status.HTTP_204_NO_CONTENT)
