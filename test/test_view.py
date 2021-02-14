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

def test_ping(api):
    resp=api.get('/ping')
    assert b'pong' in resp.data

def test_login(api):
    resp=api.post('/login', data=json.dumps({'email':'test1@mail.com','password':'password'}), content_type='application/json')
    assert b'access_token' in resp.data

def test_unauthorized(api):
    resp=api.post('/tweet', data=json.dumps({'tweet':'test tweet'}), content_type='application/json')
    assert resp.status_code==401

    resp=api.post('/follow', data=json.dumps({'follow':2}), content_type='application/json')
    assert resp.status_code==401

    resp=api.post('/unfollow', data=json.dumps({'follow':2}), content_type='application/json')
    assert resp.status_code==401

def test_tweet(api):
    # login & access token
    resp=api.post('/login', data=json.dumps({'email':'test1@mail.com', 'password':'password'}), content_type='application/json')
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

def test_follow(api):
    # login & access token
    resp=api.post('/login', data=json.dumps({'email':'test1@mail.com', 'password':'password'}), content_type='application/json')
    resp_json=json.loads(resp.data.decode('utf-8'))
    access_token=resp_json['access_token']

    # test before follow
    resp=api.get('/timeline/1')
    tweets=json.loads(resp.data.decode('utf-8'))
    assert resp.status_code==200
    assert tweets=={
        'user_id':1,
        'timeline':[]
    }

    # follow
    resp=api.post('/follow', data=json.dumps({'follow':2}), content_type='application/json', headers={'Authorization':access_token})
    assert resp.status_code==200

    # check test1 followed test2
    resp=api.get('/timeline/1')
    tweets=json.loads(resp.data.decode('utf-8'))
    assert resp.status_code==200
    assert tweets=={
        'user_id':1,
        'timeline':[{
            'user_id':2,
            'tweet':'test2 tweet'
        }]
    }

def test_unfollow(api):
    # login & access token
    resp=api.post('/login', data=json.dumps({'email':'test1@mail.com', 'password':'password'}), content_type='application/json')
    resp_json=json.loads(resp.data.decode('utf-8'))
    access_token=resp_json['access_token']

    # follow test2
    resp=api.post('/follow', data=json.dumps({'follow':2}), content_type='application/json', headers={'Authorization':access_token})
    assert resp.status_code==200

    # test before unfollow
    resp=api.get('/timeline/1')
    tweets=json.loads(resp.data.decode('utf-8'))
    assert resp.status_code==200
    assert tweets=={
        'user_id':1,
        'timeline':[{
            'user_id':2,
            'tweet':'test2 tweet'
        }]
    }

    # unfollow test2
    resp=api.post('/unfollow', data=json.dumps({'unfollow':2}), content_type='application/json', headers={'Authorization':access_token})
    assert resp.status_code==200

    # check test1 unfollowed test2
    resp=api.get('timeline/1')
    tweets=json.loads(resp.data.decode('utf-8'))
    assert resp.status_code==200
    assert tweets=={
        'user_id':1,
        'timeline':[]
    }