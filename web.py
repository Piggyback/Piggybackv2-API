import os
import simplejson
import datetime
from flask import Flask, render_template, redirect, url_for, request, Response, jsonify
from flaskext.sqlalchemy import SQLAlchemy
from apns import APNs, Payload
from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

if not os.environ.get('PROD'):
    app.config['SQLALCHEMY_ECHO'] = True
    app.debug = True

db = SQLAlchemy(app)

apns = APNs(use_sandbox=True, cert_file='cert.pem', key_file='key.pem')

class PbUser(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(64))
    lastName = db.Column(db.String(64))
    fbId = db.Column(db.BigInteger, unique=True)
    email = db.Column(db.String(64))
    spotifyUsername = db.Column(db.String(32))
    foursquareId = db.Column(db.BigInteger)
    youtubeUsername = db.Column(db.String(32))
    isPiggybackUser = db.Column(db.SmallInteger)
    dateAdded = db.Column(db.DateTime)
    dateBecamePbUser = db.Column(db.DateTime)
    ambassadors = db.relationship('PbAmbassador', backref='follower', lazy='dynamic')
    musicActivity = db.relationship('PbMusicActivity', backref='user', lazy='dynamic')
    musicTodos = db.relationship('PbMusicTodo', backref='follower', lazy='dynamic')

    def __init__(self, firstName, lastName, fbId, email, spotifyUsername, foursquareId, youtubeUsername, isPiggybackUser, dateAdded, dateBecamePbUser):
        self.firstName = firstName
        self.lastName = lastName
        self.fbId = fbId
        self.email = email
        self.spotifyUsername = spotifyUsername
        if foursquareId == 0:
            self.foursquareId = None
        else:
            self.foursquareId = foursquareId
        self.youtubeUsername = youtubeUsername
        self.isPiggybackUser = isPiggybackUser
        self.dateAdded = dateAdded
        self.dateBecamePbUser = dateBecamePbUser

class PbAmbassador(db.Model):
    followerUid = db.Column(db.Integer, db.ForeignKey("pb_user.uid"), primary_key=True)
    ambassadorUid = db.Column(db.Integer, primary_key=True)
    ambassadorType = db.Column(db.String(16), primary_key=True)
    dateAdded = db.Column(db.DateTime)
    deleted = db.Column(db.SmallInteger, default=0)

    def __init__(self, followerUid, ambassadorUid, ambassadorType, dateAdded, deleted):
        self.ambassadorUid = ambassadorUid
        self.ambassadorType = ambassadorType
        self.followerUid = followerUid
        self.dateAdded = dateAdded
        self.deleted = deleted

class PbIphonePushToken(db.Model):
    uid = db.Column(db.Integer, db.ForeignKey("pb_user.uid"), primary_key=True)
    iphonePushToken = db.Column(db.String(64), primary_key=True)
    dateAdded = db.Column(db.DateTime)

    def __init__(self, uid, iphonePushToken, dateAdded):
        self.uid = uid
        self.iphonePushToken = iphonePushToken
        self.dateAdded = dateAdded

class PbMusicActivity(db.Model):
    musicActivityId = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer, db.ForeignKey("pb_user.uid"))
    musicItemId = db.Column(db.Integer, db.ForeignKey("pb_music_item.musicItemId"))
    dateAdded = db.Column(db.DateTime)
    todos = db.relationship('PbMusicTodo', backref='musicActivity', lazy='select')

    def __init__(self, uid, musicItemId, dateAdded):
        self.uid = uid
        self.musicItemId = musicItemId
        self.dateAdded = dateAdded

class PbMusicItem(db.Model):
    musicItemId = db.Column(db.Integer, primary_key=True)
    artistName = db.Column(db.String(64))
    songTitle = db.Column(db.String(64))
    albumTitle = db.Column(db.String(64))
    albumYear = db.Column(db.Integer)
    spotifyUrl = db.Column(db.String(64), unique=True)
    songDuration = db.Column(db.Float)
    inMusicAcitivity = db.relationship('PbMusicActivity', backref='musicItem', lazy='select')

    def __init__(self, artistName, songTitle, albumTitle, albumYear, spotifyUrl, songDuration):
        self.artistName = artistName
        self.songTitle = songTitle
        self.albumTitle = albumTitle
        self.albumYear = albumYear
        self.spotifyUrl = spotifyUrl
        self.songDuration = songDuration

class PbMusicTodo(db.Model):
    musicTodoId = db.Column(db.Integer, primary_key=True)
    musicActivityId = db.Column(db.Integer, db.ForeignKey("pb_music_activity.musicActivityId"))
    followerUid = db.Column(db.Integer, db.ForeignKey("pb_user.uid"))
    dateAdded = db.Column(db.DateTime)

    def __init__(self, musicActivityId, followerUid, dateAdded):
        self.musicActivityId = musicActivityId
        self.followerUid = followerUid
        self.dateAdded = dateAdded

class PbEmailListing(db.Model):
    emailId = db.Column(db.Integer, primary_key=True)
    emailAddress = db.Column(db.String, unique=True)
    dateAdded = db.Column(db.DateTime)

    def __init__(self, emailAddress, dateAdded):
        self.emailAddress = emailAddress
        self.dateAdded = dateAdded

# to allow cross domain requests
def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

@app.route("/")
def index():
    return 'hello world.'

# User API
@app.route("/user", methods = ['GET'])
def getUser():
    requestJson = request.json
    user = PbUser.query.filter_by(fbId=requestJson.get('fbId')).first()
    resp = None
    if user == None:
        resp = jsonify({'error':'User does not exist'})
        resp.status_code = 404
    else:
        if user.isPiggybackUser == 1:
            user.dateBecamePbUser = user.dateBecamePbUser.strftime("%Y-%m-%d %H:%M:%S")
        resp = jsonify({"PBUser":{"uid":user.uid, "firstName":user.firstName, "lastName":user.lastName, "fbid":user.fbId, "email":user.email,
            "spotifyUsername":user.spotifyUsername, "foursquareId":user.foursquareId, "youtubeUsername":user.youtubeUsername,
            "isPiggybackUser":user.isPiggybackUser, "dateAdded":user.dateAdded.strftime("%Y-%m-%d %H:%M:%S"), "dateBecamePbUser":user.dateBecamePbUser}})
        resp.status_code = 200

    return resp

@app.route("/addUser", methods = ['POST'])
def addUser():
    requestJson = request.json
    resp = getUser()
    if resp.status_code == 404:
        # user does not exist - add user
        now = datetime.datetime.now()
        dateBecamePbUser = None
        if requestJson['isPiggybackUser'] == 1:
            dateBecamePbUser = now
        user = PbUser(requestJson.get('firstName'), requestJson.get('lastName'), requestJson.get('fbId'), requestJson.get('email'), 
            requestJson.get('spotifyUsername'), requestJson.get('foursquareId'), requestJson.get('youtubeUsername'), 
            requestJson['isPiggybackUser'], now, dateBecamePbUser)
        db.session.add(user)
        db.session.commit()

        # # TODO: if db insert was successful, return status 200. 
        resp = jsonify({"PBUser":{"uid":user.uid}})
        resp.status_code = 200

    return resp

@app.route("/updateUser", methods = ['PUT'])
def updateUser():
    requestJson = request.json
    if requestJson.get('spotifyUsername'):
        PbUser.query.filter_by(uid = requestJson['uid']).update({'spotifyUsername':requestJson['spotifyUsername']})

    if requestJson.get('foursquareId'):
        PbUser.query.filter_by(uid = requestJson['uid']).update({'foursquareId':requestJson['foursquareId']})

    if requestJson.get('youtubeUsername'):
        PbUser.query.filter_by(uid = requestJson['uid']).update({'youtubeUsername':requestJson['youtubeUsername']})

    if requestJson.get('isPiggybackUser'):
        if requestJson['isPiggybackUser'] == 1:
            now = datetime.datetime.now()
            PbUser.query.filter_by(uid = requestJson['uid']).update({'isPiggybackUser':requestJson['isPiggybackUser'], 'dateBecamePbUser':now})
        else:
            PbUser.query.filter_by(uid = requestJson['uid']).update({'isPiggybackUser':requestJson['isPiggybackUser']})

    db.session.commit()
    resp = jsonify({})
    resp.status_code = 200

    return resp

# Ambassador API
@app.route("/addAmbassador", methods = ['POST'])
def addAmbassador():
    requestJson = request.json
    now = datetime.datetime.now()
    ambassador = PbAmbassador(requestJson['followerUid'], requestJson['ambassadorUid'], requestJson['ambassadorType'], now, 0)
    db.session.merge(ambassador)
    db.session.commit()

    resp = jsonify({})
    resp.status_code = 200

    return resp

@app.route("/removeAmbassador", methods = ['PUT'])
def removeAmbassador():
    # doesn't actually remove from DB, just updates flag
    requestJson = request.json
    PbAmbassador.query.filter_by(followerUid = requestJson['followerUid'], ambassadorUid = requestJson['ambassadorUid'], ambassadorType = requestJson['ambassadorType']).update({'deleted':1})

    db.session.commit()
    resp = jsonify({})
    resp.status_code = 200

    return resp

# Push notification
@app.route("/addIphonePushToken", methods = ['POST'])
def pushNotif():
    requestJson = request.json
    now = datetime.datetime.now()
    iphonePushToken = PbIphonePushToken(requestJson['uid'], requestJson['deviceToken'], now)
    db.session.add(iphonePushToken)
    db.session.commit()
    # token_hex = requestJson.get('deviceToken')
    # payload = Payload(alert="hello world.")
    # apns.gateway_server.send_notification(token_hex, payload)

    resp = jsonify({})
    resp.status_code = 200

    return resp

# musicItem API
@app.route("/musicItem", methods = ['GET'])
def getMusicItem():
    requestJson = request.json
    musicItem = PbMusicItem.query.filter_by(spotifyUrl=requestJson.get('spotifyUrl')).first()
    resp = None
    if musicItem == None:
        resp = jsonify({'error':'MusicItem does not exist'})
        resp.status_code = 404
    else:
        resp = jsonify({"PBMusicItem":{"musicItemId":musicItem.musicItemId, 
                        "artistName":musicItem.artistName, 
                        "songTitle":musicItem.songTitle, 
                        "albumTitle":musicItem.albumTitle, 
                        "albumYear":musicItem.albumYear, 
                        "spotifyUrl":musicItem.spotifyUrl, 
                        "songDuration":musicItem.songDuration}})

        resp.status_code = 200

    return resp

@app.route("/addMusicItem", methods = ['POST'])
def addMusicItem():
    requestJson = request.json
    resp = getMusicItem()
    if resp.status_code == 404:
        # musicItem does not exist - add it
        musicItem = PbMusicItem(requestJson.get('artistName'), 
                                requestJson.get('songTitle'), 
                                requestJson.get('albumTitle'), 
                                requestJson.get('albumYear'), 
                                requestJson.get('spotifyUrl'),
                                requestJson.get('songDuration'))
        db.session.add(musicItem)
        db.session.commit()

        resp = jsonify({"PBMusicItem":{"musicItemId":musicItem.musicItemId}})
        resp.status_code = 200

    return resp

# News Feed
@app.route("/news", methods = ['GET'])
def getNews():
    requestJson = request.json
    musicActivity = PbMusicActivity.query.filter_by(uid=requestJson['uid']).all()
    result = {'musicActivity':[]}
    i=0
    for activity in musicActivity:
        result['musicActivity'].append({
            'musicActivityId':activity.musicActivityId,
            'uid':activity.uid,
            'dateAdded':activity.dateAdded.strftime("%Y-%m-%d %H:%M:%S"),
            'musicItem':
            {
                'musicItemId':activity.musicItem.musicItemId,
                'artistName':activity.musicItem.artistName,
                'songTitle':activity.musicItem.songTitle,
                'albumTitle':activity.musicItem.albumTitle,
                'albumYear':activity.musicItem.albumYear,
                'spotifyUrl':activity.musicItem.spotifyUrl
            },
            'todos':[]
        })
        for todo in activity.todos:
            result['musicActivity'][i]['todos'].append(
                {
                    'musicTodoId':todo.musicTodoId,
                    'dateAdded':todo.dateAdded.strftime("%Y-%m-%d %H:%M:%S"),
                    'follower': 
                    {
                        'uid':todo.follower.uid,
                        'firstName':todo.follower.firstName,
                        'lastName':todo.follower.lastName,
                        'fbId':todo.follower.fbId,
                        'email':todo.follower.email,
                        'spotifyUsername':todo.follower.spotifyUsername,
                        'foursquareId':todo.follower.foursquareId,
                        'youtubeUsername':todo.follower.youtubeUsername,
                        'isPiggybackUser':todo.follower.isPiggybackUser,
                        'dateAdded':todo.follower.dateAdded.strftime("%Y-%m-%d %H:%M:%S"),
                        'dateBecamePbUser':todo.follower.dateAdded.strftime("%Y-%m-%d %H:%M:%S")
                    }
                })

        i = i+1

    # resp = jsonify({"data":firstMusicActivity.musicItem.artistName})
    resp = jsonify(result)

    return resp

# emailListing API
@app.route("/emailListing", methods = ['GET'])
def getEmailListing():
    requestJson = request.json
    emailListing = PbEmailListing.query.filter_by(emailAddress=requestJson.get('emailAddress')).first()
    if emailListing == None:
        resp = jsonify({})
        resp.status_code = 404
    else:
        resp = jsonify({"PBEmailListing":{"emailId":emailListing.emailId,"emailAddress":emailListing.emailAddress}})
        resp.status_code = 200

    return resp

@app.route("/addEmailListing", methods = ['POST'])
@crossdomain(origin='*')
def addEmailListing():
    requestJson = request.json
    resp = getEmailListing() 
    if resp.status_code == 404:
        # email does not exist - add it
        now = datetime.datetime.now()
        emailListing = PbEmailListing(requestJson.get('emailAddress'),now)
        db.session.add(emailListing)
        db.session.commit()

        resp = jsonify({"PBEmailListing":{"emailId":emailListing.emailId,"emailAddress":emailListing.emailAddress}})
        resp.status_code = 200

    return resp

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)