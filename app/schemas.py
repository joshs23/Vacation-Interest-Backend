from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional

####################################### TOKEN #############################################
class Token(BaseModel):
    Access_token: str
    Token_type: str

class TokenData(BaseModel):
    id: int

######################################### LOCATION #########################################
# Location_id  INT UNSIGNED AUTO_INCREMENT NOT NULL,
# Named	       VARCHAR(50) NOT NULL UNIQUE,
# Created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
# PRIMARY KEY  (Location_id)

class LocationBase(BaseModel):
    Named: str

class Location(LocationBase):
    pass

class LocationResponse(LocationBase):
    Location_id: int
    Created_at: datetime
    class Config:
        from_attributes = True

########################################### PLACE ##########################################
# Place_id     INT UNSIGNED AUTO_INCREMENT NOT NULL,
# Named        VARCHAR(50) UNIQUE,
# Created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
# PRIMARY KEY  (Place_id)

class PlaceBase(BaseModel):
    Named: str

class Place(PlaceBase):
    pass

class PlaceResponse(PlaceBase):
    Place_id: int
    Created_at: datetime
    Location_name: str


########################################### USER ###########################################
# User_id        INT UNSIGNED AUTO_INCREMENT NOT NULL,
# Username       VARCHAR(50) NOT NULL UNIQUE,
# Password_hash  VARCHAR(50) NOT NULL,
# Email          VARCHAR(100) NOT NULL UNIQUE,
# Created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
# PRIMARY KEY    (User_id)

class CreateUser(BaseModel):
    Username: str
    Email: EmailStr
    Password_hash: str

class UserBase(BaseModel):
    Username: str
    Email: EmailStr

class Username(BaseModel):
    Username: str

class UserEmail(BaseModel):
    Email: EmailStr

class UserResponse(UserBase):
    User_id: int
    Created_at: datetime

class CurrentUser(UserBase):
    User_id: int

class GroupOwnerUser(UserBase):
    Owner_created_at: datetime

######################################## USER_GROUP ########################################
# Group_id           INT UNSIGNED AUTO_INCREMENT NOT NULL,
# Group_name         VARCHAR(50) NOT NULL UNIQUE,
# Owner_id           INT UNSIGNED NOT NULL,
# Public_group       TINYINT NOT NULL,
# Created_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
# PRIMARY KEY (Group_id)

class User_groupBase(BaseModel):
    Group_id: int
    Group_name: str
    Owner_id: int
    Public_group: bool
    Created_at: datetime

class GroupResponse(User_groupBase):
    pass
    Owner: GroupOwnerUser

class NewGroup(BaseModel):
    Group_name: str
    Public_group: bool

class  UpdateGroupOwner(BaseModel):
    Owner_id: int
    
class UpdateGroupName(BaseModel):
    Group_name: str

# CREATE TABLE USERS_IN_GROUP (
# 	User_id INT UNSIGNED NOT NULL,
# 	Group_id INT UNSIGNED NOT NULL,
#   Created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
# 	PRIMARY KEY (User_id, Group_id),
# 	FOREIGN KEY (User_id) REFERENCES USERS(User_id),
# 	FOREIGN KEY (Group_id) REFERENCES USER_GROUP(Group_id)
# );

class Users_In_GroupBase(BaseModel):
    User_id: int
    Group_id: int
    Created_at: datetime

# CREATE TABLE PLACES_AT_LOCATION (
# 	Place_id INT UNSIGNED NOT NULL,
# 	Location_id INT UNSIGNED NOT NULL,
#   Created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
# 	PRIMARY KEY (Place_id),
# 	FOREIGN KEY (Place_id) REFERENCES PLACE(Place_id),
# 	FOREIGN KEY (Location_id) REFERENCES LOCATION(Location_id)
# );

# CREATE TABLE FEATURE (
# 	Feature_id INT UNSIGNED AUTO_INCREMENT NOT NULL,
# 	Named VARCHAR(50) NOT NULL UNIQUE,
# 	Description TEXT NOT NULL,
# 	Added_by INT UNSIGNED NOT NULL,
#   Created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
# 	PRIMARY KEY (Feature_id),
# 	FOREIGN KEY (Added_by) REFERENCES USERS(User_id)
# );

class FeatureBase(BaseModel):
    Feature_id: int
    Named: str
    Description: str
    Added_by: int

class FeatureCreate(FeatureBase):
    pass
    
class FeatureResponse(FeatureBase):
    pass
    Created_at: datetime

# CREATE TABLE FEATURES_AT_PLACE(
# 	Feature_id INT UNSIGNED NOT NULL,
# 	Place_id INT UNSIGNED NOT NULL, 
#   Created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
# 	PRIMARY KEY (Feature_id),
# 	FOREIGN KEY (Feature_id) REFERENCES FEATURE(Feature_id),
# 	FOREIGN KEY (Place_id) REFERENCES PLACE(Place_id)
# );

# CREATE TABLE REVIEW (
# 	Review_id INT UNSIGNED AUTO_INCREMENT NOT NULL,
# 	Review INT NOT NULL,
# 	User_comment TEXT,
#   Created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
# 	PRIMARY KEY (Review_id)
# );

# CREATE TABLE REVIEWS_OF_FEATURE (
# 	Review_id INT UNSIGNED NOT NULL,
# 	Feature_id INT UNSIGNED NOT NULL, 
# 	User_id INT UNSIGNED NOT NULL,
#   Created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
# 	PRIMARY KEY (Review_id),
# 	FOREIGN KEY (Review_id) REFERENCES REVIEW(Review_id),
# 	FOREIGN KEY (Feature_id) REFERENCES FEATURE(Feature_id),
# 	FOREIGN KEY (User_id) REFERENCES USERS(User_id)