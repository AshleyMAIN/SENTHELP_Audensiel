import os
from typing import Optional, List
from decouple import config
from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ConfigDict, BaseModel, Field, EmailStr
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated
from bson import ObjectId
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import date  # ou datetime, selon votre besoin
from datetime import datetime

app = FastAPI(
    title="Tweets API",
    summary="A FastAPI application to manage tweets and requests in MongoDB.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],  # autorise React à accéder à l'API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration de la connexion à MongoDB et aux collections de tweets et de requêtes
client = AsyncIOMotorClient(config('MONGODB_URL'))
db = client.Recolte
tweets_collection = db.get_collection("tweets")
requetes_collection = db.get_collection("requests")

PyObjectId = Annotated[str, BeforeValidator(str)]

class Tweet(BaseModel):
    """Model representing a tweet document in MongoDB."""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    text_tweet: Optional[str] = Field(default=None)
    cleaned_text_tweet: Optional[str] = Field(default=None)
    nombre_likes: Optional[int] = Field(default=None)
    nombre_reposts: Optional[int] = Field(default=None)
    nombre_replies: Optional[int] = Field(default=None)
    nombre_views: Optional[int] = Field(default=None)
    date_tweet: Optional[str] = Field(default=None)
    identifiant: Optional[int] = Field(default=None)
    req_id: Optional[int] = Field(default=None)
    mot_cle: Optional[str] = Field(default=None)
    bool_analyse: Optional[bool] = Field(default=None)
    emotion: Optional[str] = Field(default=None)
    timestamp: Optional[int] = Field(default=None)
    date_tweet_cleaned: Optional[datetime] = Field(default=None)
    year: Optional[int] = Field(default=None)
    month: Optional[int] = Field(default=None)
    day: Optional[int] = Field(default=None)
    hour: Optional[int] = Field(default=None)
    minute: Optional[int] = Field(default=None)
    second: Optional[int] = Field(default=None)
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        populate_by_name=True  # utile si vous utilisez alias (_id)
    )

class TweetCollection(BaseModel):
    """
    A container holding a list of `TweetModel` instances.
    This exists because providing a top-level array in a JSON response can be a [vulnerability](https://haacked.com/archive/2009/06/25/json-hijacking.aspx/)
    """
    tweets: List[Tweet]




class Requete(BaseModel):
    """Model representing a request document in MongoDB."""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    req_id : Optional[int] = Field(default=None)
    corpus : Optional[dict] = Field(default=None)
    timestamp_debut : Optional[int] = Field(default=None)
    timestamp_fin : Optional[int] = Field(default=None)
    nb_tweets : Optional[int] = Field(default=None)
    nb_scrolls : Optional[int] = Field(default=None)
    fin_recolte : Optional[bool] = Field(default=None)
    bool_group_analysis : Optional[bool] = Field(default=None)
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        populate_by_name=True  # utile si vous utilisez alias (_id)
    )
class ReqCollection(BaseModel):
    """
    A container holding a list of `Requete` instances.
    This exists because providing a top-level array in a JSON response can be a [vulnerability](https://haacked.com/archive/2009/06/25/json-hijacking.aspx/)
    """
    requetes : List[Requete]

@app.get(
    "/tweets/",
    response_description="List all tweets",
    response_model=TweetCollection,
    response_model_by_alias=False,
)
async def list_tweets():
    """
    List all of the tweet data in the database.
    """
    return TweetCollection(tweets=await tweets_collection.find().to_list()) 


@app.get(
    "/req/",
    response_description="List all req",
    response_model=ReqCollection,
    response_model_by_alias=False,
)
async def list_requetes():
    """
    List all of the request data in the database.
    """
    return ReqCollection(requetes = await requetes_collection.find().to_list()) 