import bcrypt
import pytest
import config

from model import UserDao, TweetDao
from sqlalchemy import create_engine, text

database=create_engine(config.test_config['DB_URL'], encoding='utf-8', max_overflow=0)

@pytest.fixture
def user_dao():
    return UserDao(database)

@pytest.fixture 
def tweet_dao():
    return TweetDao(database)

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

def test_insert_user(user_dao):
    new_user={
        'name':'new',
        'email':'new@mail.com',
        'profile':'new profile',
        'password':'password'
    }

    new_user_id=user_dao.insert_user(new_user)
    user=get_user(new_user_id)

    assert user=={
        'id':new_user_id,
        'name':new_user['name'],
        'email':new_user['email'],
        'profile':new_user['profile']
    }

def test_get_user_id_and_password(user_dao):
    user_credential=user_dao.get_user_id_and_password(email='test1@mail.com')

    assert user_credential['id']==1

    assert bcrypt.checkpw('password'.encode('utf-8'), user_credential['hashed_password'].encode('utf-8'))

def test_insert_follow(user_dao):
    user_dao.insert_follow(user_id=1,follow_id=2)
    follow_list=get_follow_list(1)

    assert follow_list==[2]

def test_insert_unfollow(user_dao):
    user_dao.insert_follow(user_id=1,follow_id=2)
    user_dao.insert_unfollow(user_id=1,unfollow_id=2)
    follow_list=get_follow_list(1)

    assert follow_list==[]

def test_insert_tweet(tweet_dao):
    tweet_dao.insert_tweet(1,'tweet test')
    timeline=tweet_dao.get_timeline(1)

    assert timeline==[{
        'user_id':1,
        'tweet':'tweet test'
    }]

def test_get_timeline(user_dao,tweet_dao):
    tweet_dao.insert_tweet(1,'tweet test')
    user_dao.insert_follow(1,2)

    timeline=tweet_dao.get_timeline(1)

    assert timeline==[
        {
            'user_id':1,
            'tweet':'tweet test'
        },
        {
            'user_id':2,
            'tweet':'test2 tweet'
        }
    ]