import config

from flask import Flask
from sqlalchemy import create_engine
from flask_cors import CORS

from model import UserDao, TweetDao
from service import UserService, TweetService
from view import create_endpoints

class Service:
    pass

##################################################
# Create App
##################################################

def create_app(test_config=None):
    app=Flask(__name__)
    CORS(app)

    if test_config is None:
        app.config.from_pyfile('config.py')
    else:
        app.config.update(test_config) 
    
    database=create_engine(app.config['DB_URL'], encoding='utf-8', max_overflow=0)

    # persistence layer
    user_dao=UserDao(database)
    tweet_dao=TweetDao(database)

    # business layer
    services=Service
    services.user_service=UserService(user_dao,app.config)
    services.tweet_service=TweetService(tweet_dao)

    # create endpoint
    create_endpoints(app,services)

    return app
