import os
import simplejson
import datetime
from flask import Flask, render_template, redirect, url_for, request, Response, jsonify
from flaskext.sqlalchemy import SQLAlchemy
from apns import APNs, Payload
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

class PbAmbassadorMusicActivity(db.Model):
    musicActivityId = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer, db.ForeignKey("pb_user.uid"))
    musicItemId = db.Column(db.Integer, db.ForeignKey("pb_music_item.musicItemId"))
    dateAdded = db.Column(db.DateTime)

    def __init__(self, uid, musicItemId, dateAdded):
        self.uid = uid
        self.musicItemId = musicItemId
        self.dateAdded = dateAdded

class PbMusicItem(db.Model):
    musicItemId = db.Column(db.Integer, primary_key=True)
    artistName = db.Column(db.String(64))
    songTitle = db.Column(db.String(64))
    albumTitle = db.Column(db.String(32))
    albumYear = db.Column(db.Integer)
    spotifyUrl = db.Column(db.String(64), unique=True)

    def __init__(self, artistName, songTitle, albumTitle, albumYear, spotifyUrl):
        self.artistName = artistName
        self.songTitle = songTitle
        self.albumTitle = albumTitle
        self.albumYear = albumYear
        self.spotifyUrl = spotifyUrl

class PbMusicTodo(db.Model):
    musicNewsId = db.Column(db.Integer, primary_key=True)
    musicActivityId = db.Column(db.Integer, db.ForeignKey("pb_ambassador_music_activity.musicActivityId"))
    followerUid = db.Column(db.Integer, db.ForeignKey("pb_user.uid"))
    dateAdded = db.Column(db.DateTime)

    def __init__(self, musicActivityId, followerUid, dateAdded):
        self.musicActivityId = musicActivityId
        self.followerUid = followerUid
        self.dateAdded = dateAdded

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
        # resp = jsonify({"PBUser":{"uid":user.uid, "firstName":user.firstName, "lastName":user.lastName, "fbid":user.fbId, "email":user.email,
        #     "spotifyUsername":user.spotifyUsername, "foursquareId":user.foursquareId, "youtubeUsername":user.youtubeUsername,
        #     "isPiggybackUser":user.isPiggybackUser, "dateAdded":user.dateAdded.strftime("%Y-%m-%d %H:%M:%S"), "dateBecamePbUser":user.dateBecamePbUser.strftime("%Y-%m-%d %H:%M:%S")}})
        
        resp = jsonify({"PBUser":{"uid":user.uid, "firstName":user.firstName, "lastName":user.lastName, "fbid":user.fbId, "email":user.email,
            "spotifyUsername":user.spotifyUsername, "foursquareId":user.foursquareId, "youtubeUsername":user.youtubeUsername, 
            "isPiggybackUser":user.isPiggybackUser, "dateAdded":user.dateAdded.strftime("%Y-%m-%d %H:%M:%S"), "dateBecamePbUser":user.dateBecamePbUser.strftime("%Y-%m-%d %H:%M:%S")}})
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
    musicItem = PbMusicItem.query.filter_by(musicItemId=requestJson.get('musicItemId')).first()
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
                        "spotifyUrl":musicItem.spotifyUrl}})
        resp.status_code = 200

    return resp

@app.route("/addMusicItem", methods = ['POST'])
def addMusicItem():
    requestJson = request.json
    resp = getMusicItem()
    if resp.status_code == 404:
        # musicItem does not exist - add it
        now = datetime.datetime.now()
        musicItem = PbMusicItem(requestJson.get('artistName'), requestJson.get('songTitle'), requestJson.get('albumTitle'), requestJson.get('albumYear'), requestJson.get('spotifyUrl'))
        db.session.add(musicItem)
        db.session.commit()

        resp = jsonify({"PBMusicItem":{"musicItemId":musicItem.musicItemId}})
        resp.status_code = 200

    return resp

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)