from app import create_app
from sqlalchemy import create_engine, text

import config
import pytest
import json
import bcrypt

database=create_engine(config.test_config['DB_URL'], encoding='utf-8', max_overflow=0)

@pytest.fixture
def api():
    app=create_app(config.test_config)
    app.config['TEST']=True
    api=app.test_client()

    return api

def setup_function():
    hashed_password=bcrypt.hashpw(b'password',bcrypt.gensalt())
    new_user={
        'id':1,
        'email':'test@mail.com',
        'hashed_password':hashed_password,
        'name':'test',
        'profile':'test profile'
    }
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
    """), new_user)

def teardown_function():
    database.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    database.execute(text("TRUNCATE users"))
    database.execute(text("TRUNCATE tweets"))
    database.execute(text("TRUNCATE users_follow_list"))
    database.execute(text("SET FOREIGN_KEY_CHECKS=1"))

def test_ping(api):
    resp=api.get('/ping')
    assert b'pong' in resp.data

def test_tweet(api):
    # login & access token
    resp=api.post('/login', data=json.dumps({'email':'test@mail.com', 'password':'password'}), content_type='application/json')
    resp_json=json.loads(resp.data.decode('utf-8'))
    access_token=resp_json['access_token']

    # tweet
    resp=api.post('/tweet', data=json.dumps({'tweet':'test tweet'}), content_type='application/json', headers={'Authorization':access_token})
    assert resp.status_code==200

    # check tweet
    resp=api.get(f"/timeline/1")
    tweets=json.loads(resp.data.decode('utf-8'))

    assert resp.status_code==200
    assert tweets=={
        'user_id':1,
        'timeline':[
            {
                'user_id':1,
                'tweet':'test tweet'
            }
        ]
    }

