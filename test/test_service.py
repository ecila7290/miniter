import jwt
import bcrypt
import pytest
import config

from model import UserDao, TweetDao
from service import UserService, TweetService
from sqlalchemy import create_engine, text

database=create_engine(config.test_config['DB_URL'], encoding='utf-8', max_overflow=0)

@pytest.fixture
def user_service():
    return UserService(UserDao(database),config.test_config)

@pytest.fixture
def tweet_service():
    return TweetService(TweetDao(database))

def setup_function():
    hashed_password=bcrypt.hashpw(b'password',bcrypt.gensalt())
    new_users=[{
        'id':1,
        'email':'test1@mail.com',
        'hashed_password':hashed_password,
        'name':'test1',
        'profile':'test1 profile'
    },
    {
        'id':2,
        'email':'test2@mail.com',
        'hashed_password':hashed_password,
        'name':'test2',
        'profile':'test2 profile'
    }
    ]
    database.execute(text("""
        INSERT INTO users (
            id,
            name,
            email,
            profile,
            hashed_password
        ) VALUES (
            :id,
            :name,
            :email,
            :profile,
            :hashed_password
        )
    """), new_users)

    database.execute(text("""
        INSERT INTO tweets (
            user_id,
            tweet
        ) VALUES (
            2,
            'test2 tweet'
        )
    """))

def teardown_function():
    database.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    database.execute(text("TRUNCATE users"))
    database.execute(text("TRUNCATE tweets"))
    database.execute(text("TRUNCATE users_follow_list"))
    database.execute(text("SET FOREIGN_KEY_CHECKS=1"))

def get_user(user_id):
    user=database.execute(text("""
        SELECT
            id,
            name,
            email,
            profile
        FROM users
        WHERE id=:user_id
    """),{
        'user_id':user_id
    }).fetchone()

    return {
        'id':user['id'],
        'name':user['name'],
        'email':user['email'],
        'profile':user['profile']
    } if user else None

def get_follow_list(user_id):
    rows=database.execute(text("""
        SELECT follow_user_id as id
        FROM users_follow_list
        WHERE user_id=:user_id
    """),{'user_id':user_id}).fetchall()

    return [int(row['id']) for row in rows]

def test_create_new_user(user_service):
    new_user={
        'name':'new',
        'email':'new@mail.com',
        'profile':'new profile',
        'password':'password'
    }
    new_user_id=user_service.create_new_user(new_user)
    created_user=get_user(new_user_id)
    assert created_user=={
        'id':new_user_id,
        'name':new_user['name'],
        'email':new_user['email'],
        'profile':new_user['profile']
    }

def test_login(user_service):
    assert user_service.login({'email':'test1@mail.com','password':'password'})

    assert not user_service.login({'email':'test1@mail.com','password':'password123'})

def test_generate_access_token(user_service):
    token=user_service.generate_access_token(1)
    payload=jwt.decode(token, config.JWT_SECRET_KEY, config.ALGORITHM)

    assert payload['user_id']==1

def test_follow(user_service):
    user_service.follow(1,2)
    follow_list=get_follow_list(1)

    assert follow_list==[2]

def test_unfollow(user_service):
    user_service.follow(1,2)
    user_service.unfollow(1,2)
    follow_list=get_follow_list(1)

    assert follow_list==[]

def test_tweet(tweet_service):
    tweet_service.tweet(1,'tweet test')
    timeline=tweet_service.get_timeline(1)

    assert timeline==[{
        'user_id':1,
        'tweet':'tweet test'
    }]

def test_get_timeline(user_service,tweet_service):
    tweet_service.tweet(1,'tweet test')
    user_service.follow(1,2)

    timeline=tweet_service.get_timeline(1)

    assert timeline==[
        {
            'user_id':2,
            'tweet':'test2 tweet'
        },
        {
            'user_id':1,
            'tweet':'tweet test'
        }
    ]