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
    musicFeedback = db.relationship('PbMusicFeedback', backref='follower', lazy='dynamic')
    placesActivity = db.relationship('PbPlacesActivity', backref='user', lazy='dynamic')
    placesFeedback = db.relationship('PbPlacesFeedback', backref='follower', lazy='dynamic')
    videosActivity = db.relationship('PbVideosActivity', backref='user', lazy='dynamic')
    videosFeedback = db.relationship('PbVideosFeedback', backref='follower', lazy='dynamic')

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

class PbMusicActivity(db.Model):
    musicActivityId = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer, db.ForeignKey("pb_user.uid"))
    musicItemId = db.Column(db.Integer, db.ForeignKey("pb_music_item.musicItemId"))
    musicActivityType = db.Column(db.String(16))
    dateAdded = db.Column(db.DateTime)
    feedback = db.relationship('PbMusicFeedback', backref='musicActivity', lazy='select')

    def __init__(self, uid, musicItemId, musicActivityType, dateAdded):
        self.uid = uid
        self.musicItemId = musicItemId
        self.musicActivityType = musicActivityType
        self.dateAdded = dateAdded

class PbMusicFeedback(db.Model):
    musicFeedbackId = db.Column(db.Integer, primary_key=True)
    musicActivityId = db.Column(db.Integer, db.ForeignKey("pb_music_activity.musicActivityId"))
    followerUid = db.Column(db.Integer, db.ForeignKey("pb_user.uid"))
    musicFeedbackType = db.Column(db.String(16))    # todo, like
    dateAdded = db.Column(db.DateTime)
    status = db.Column(db.SmallInteger, default=0)      # 0=todo, 1=deleted, 2=completed

    def __init__(self, musicActivityId, followerUid, musicFeedbackType, dateAdded, status):
        self.musicActivityId = musicActivityId
        self.followerUid = followerUid
        self.musicFeedbackType = musicFeedbackType
        self.dateAdded = dateAdded
        self.status = status

class PbPlacesItem(db.Model):
    placesItemId = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    phone = db.Column(db.String(32))
    addr = db.Column(db.String(128))
    addrCity = db.Column(db.String(64))
    addrState = db.Column(db.String(32))
    addrCountry = db.Column(db.String(64))
    addrZip = db.Column(db.String(16))
    foursquareReferenceId = db.Column(db.String(32))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    photoURL = db.Column(db.String(256))
    inPlacesActivity = db.relationship('PbPlacesActivity', backref='placesItem', lazy='select')

    def __init__(self, name, phone, addr, addrCity, addrState, addrCountry, addrZip, foursquareReferenceId, lat, lng, photoURL):
        self.name = name
        self.phone = phone
        self.addr = addr
        self.addrCity = addrCity
        self.addrState = addrState
        self.addrCountry = addrCountry
        self.addrZip = addrZip
        self.foursquareReferenceId = foursquareReferenceId
        self.lat = lat
        self.lng = lng
        self.photoURL = photoURL

class PbPlacesActivity(db.Model):
    placesActivityId = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer, db.ForeignKey("pb_user.uid"))
    placesItemId = db.Column(db.Integer, db.ForeignKey("pb_places_item.placesItemId"))
    placesActivityType = db.Column(db.String(32))
    dateAdded = db.Column(db.DateTime)
    feedback = db.relationship('PbPlacesFeedback', backref='placesActivity', lazy='select')

    def __init__(self, uid, placesItemId, placesActivityType, dateAdded):
        self.uid = uid
        self.placesItemId = placesItemId
        self.placesActivityType = placesActivityType
        self.dateAdded = dateAdded

class PbPlacesFeedback(db.Model):
    placesFeedbackId = db.Column(db.Integer, primary_key=True)
    placesActivityId = db.Column(db.Integer, db.ForeignKey("pb_places_activity.placesActivityId"))
    followerUid = db.Column(db.Integer, db.ForeignKey("pb_user.uid"))
    placesFeedbackType = db.Column(db.String(16))    # todo, like
    dateAdded = db.Column(db.DateTime)
    status = db.Column(db.SmallInteger, default=0)      # 0=todo, 1=deleted, 2=completed

    def __init__(self, placesActivityId, followerUid, placesFeedbackType, dateAdded, status):
        self.placesActivityId = placesActivityId
        self.followerUid = followerUid
        self.placesFeedbackType = placesFeedbackType
        self.dateAdded = dateAdded
        self.status = status

class PbVideosItem(db.Model):
    videosItemId = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    videoURL = db.Column(db.String(256))
    inVideosActivity = db.relationship('PbVideosActivity', backref='videosItem', lazy='select')

    def __init__(self, name, videoURL):
        self.name = name
        self.videoURL = videoURL

class PbVideosActivity(db.Model):
    videosActivityId = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer, db.ForeignKey("pb_user.uid"))
    videosItemId = db.Column(db.Integer, db.ForeignKey("pb_videos_item.videosItemId"))
    videosActivityType = db.Column(db.String(32))
    dateAdded = db.Column(db.DateTime)
    feedback = db.relationship('PbVideosFeedback', backref='videosActivity', lazy='select')

    def __init__(self, uid, videosItemId, videosActivityType, dateAdded):
        self.uid = uid
        self.videosItemId = videosItemId
        self.videosActivityType = videosActivityType
        self.dateAdded = dateAdded

class PbVideosFeedback(db.Model):
    videosFeedbackId = db.Column(db.Integer, primary_key=True)
    videosActivityId = db.Column(db.Integer, db.ForeignKey("pb_videos_activity.videosActivityId"))
    followerUid = db.Column(db.Integer, db.ForeignKey("pb_user.uid"))
    videosFeedbackType = db.Column(db.String(16))    # todo, like
    dateAdded = db.Column(db.DateTime)
    status = db.Column(db.SmallInteger, default=0)      # 0=todo, 1=deleted, 2=completed

    def __init__(self, videosActivityId, followerUid, videosFeedbackType, dateAdded, status):
        self.videosActivityId = videosActivityId
        self.followerUid = followerUid
        self.videosFeedbackType = videosFeedbackType
        self.dateAdded = dateAdded
        self.status = status

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
    PbAmbassador.query.filter_by(followerUid = requestJson['followerUid'], ambassadorUid = requestJson['ambassadorUid'], 
        ambassadorType = requestJson['ambassadorType']).update({'deleted':1})

    db.session.commit()
    resp = jsonify({})
    resp.status_code = 200

    return resp

# Feedback API
@app.route("/addMusicFeedback", methods = ['POST'])
def addMusicFeedback():
    requestJson = request.json
    now = datetime.datetime.now()

    # check if feedback already exists in DB. if so, update status to 0
    musicFeedback = PbMusicFeedback.query.filter_by(musicActivityId = requestJson['musicActivityId'], 
        followerUid = requestJson['followerUid'], musicFeedbackType = requestJson['musicFeedbackType']).first()

    if musicFeedback:
        PbMusicFeedback.query.filter_by(musicFeedbackId = musicFeedback.musicFeedbackId).update({'dateAdded':now, 'status':0})
        db.session.commit()

    else:
        musicFeedback = PbMusicFeedback(requestJson['musicActivityId'], requestJson['followerUid'], requestJson['musicFeedbackType'], now, 0)
        db.session.add(musicFeedback)
        db.session.commit()

    resp = jsonify({})

    # Send push notification to trusted friend!
    iphonePushTokenObject = PbIphonePushToken.query.filter_by(uid=requestJson['musicActivity']['uid']).first()
    if iphonePushTokenObject:
        token_hex = iphonePushTokenObject.iphonePushToken
        if requestJson['musicFeedbackType'] == 'todo':
            payloadMessage = requestJson['follower']['firstName'] + ' ' + requestJson['follower']['lastName'] + ' saved your song "' + requestJson['musicActivity']['musicItem']['songTitle'] + '"!'
        elif requestJson['musicFeedbackType'] == 'like':
            payloadMessage = requestJson['follower']['firstName'] + ' ' + requestJson['follower']['lastName'] + ' liked your song "' + requestJson['musicActivity']['musicItem']['songTitle'] + '"!'
        payload = Payload(alert=payloadMessage)
        apns.gateway_server.send_notification(token_hex, payload)

    resp = jsonify({"PBMusicFeedback":{"musicFeedbackId":musicFeedback.musicFeedbackId, "dateAdded":now.strftime("%Y-%m-%d %H:%M:%S")}})
    resp.status_code = 200

    return resp

@app.route("/removeMusicFeedback", methods = ['PUT'])
def removeMusicFeedback():
    requestJson = request.json
    PbMusicFeedback.query.filter_by(musicFeedbackId = requestJson['musicFeedbackId']).update({'status':1})

    db.session.commit()
    resp = jsonify({})
    resp.status_code = 200;

    return resp; 

@app.route("/addPlacesFeedback", methods = ['POST'])
def addPlacesFeedback():
    requestJson = request.json
    now = datetime.datetime.now()

    # check if feedback already exists in DB. if so, update status to 0
    placesFeedback = PbPlacesFeedback.query.filter_by(placesActivityId = requestJson['placesActivityId'], 
        followerUid = requestJson['followerUid'], placesFeedbackType = requestJson['placesFeedbackType']).first()

    if placesFeedback:
        PbPlacesFeedback.query.filter_by(placesFeedbackId = placesFeedback.placesFeedbackId).update({'dateAdded':now, 'status':0})
        db.session.commit()

    else:
        placesFeedback = PbPlacesFeedback(requestJson['placesActivityId'], requestJson['followerUid'], requestJson['placesFeedbackType'], now, 0)
        db.session.add(placesFeedback)
        db.session.commit()

    resp = jsonify({})

    # Send push notification to trusted friend!
    iphonePushTokenObject = PbIphonePushToken.query.filter_by(uid=requestJson['placesActivity']['uid']).first()
    if iphonePushTokenObject:
        token_hex = iphonePushTokenObject.iphonePushToken
        if requestJson['placesFeedbackType'] == 'todo':
            payloadMessage = requestJson['follower']['firstName'] + ' ' + requestJson['follower']['lastName'] + ' saved your check-in at "' + requestJson['placesActivity']['placesItem']['name'] + '"!'
        elif requestJson['placesFeedbackType'] == 'like':
            payloadMessage = requestJson['follower']['firstName'] + ' ' + requestJson['follower']['lastName'] + ' liked your check-in at "' + requestJson['placesActivity']['placesItem']['name'] + '"!'
        payload = Payload(alert=payloadMessage)
        apns.gateway_server.send_notification(token_hex, payload)

    resp = jsonify({"PBPlacesFeedback":{"placesFeedbackId":placesFeedback.placesFeedbackId, "dateAdded":now.strftime("%Y-%m-%d %H:%M:%S")}})
    resp.status_code = 200

    return resp

@app.route("/removePlacesFeedback", methods = ['PUT'])
def removePlacesFeedback():
    requestJson = request.json
    PbPlacesFeedback.query.filter_by(placesFeedbackId = requestJson['placesFeedbackId']).update({'status':1})

    db.session.commit()
    resp = jsonify({})
    resp.status_code = 200;

    return resp;

@app.route("/addVideosFeedback", methods = ['POST'])
def addVideosFeedback():
    requestJson = request.json
    now = datetime.datetime.now()

    # check if feedback already exists in DB. if so, update status to 0
    videosFeedback = PbVideosFeedback.query.filter_by(videosActivityId = requestJson['videosActivityId'], 
        followerUid = requestJson['followerUid'], videosFeedbackType = requestJson['videosFeedbackType']).first()

    if videosFeedback:
        PbVideosFeedback.query.filter_by(videosFeedbackId = videosFeedback.videosFeedbackId).update({'dateAdded':now, 'status':0})
        db.session.commit()

    else:
        videosFeedback = PbVideosFeedback(requestJson['videosActivityId'], requestJson['followerUid'], requestJson['videosFeedbackType'], now, 0)
        db.session.add(videosFeedback)
        db.session.commit()

    resp = jsonify({})

    # Send push notification to trusted friend!
    iphonePushTokenObject = PbIphonePushToken.query.filter_by(uid=requestJson['videosActivity']['uid']).first()
    if iphonePushTokenObject:
        token_hex = iphonePushTokenObject.iphonePushToken
        if requestJson['videosFeedbackType'] == 'todo':
            payloadMessage = requestJson['follower']['firstName'] + ' ' + requestJson['follower']['lastName'] + ' saved your video "' + requestJson['videosActivity']['videosItem']['name'] + '"!'
        elif requestJson['videosFeedbackType'] == 'like':
            payloadMessage = requestJson['follower']['firstName'] + ' ' + requestJson['follower']['lastName'] + ' liked your video "' + requestJson['videosActivity']['videosItem']['name'] + '"!'
        payload = Payload(alert=payloadMessage)
        apns.gateway_server.send_notification(token_hex, payload)

    resp = jsonify({"PBVideosFeedback":{"videosFeedbackId":videosFeedback.videosFeedbackId, "dateAdded":now.strftime("%Y-%m-%d %H:%M:%S")}})
    resp.status_code = 200

    return resp

@app.route("/removeVideosFeedback", methods = ['PUT'])
def removeVideosFeedback():
    requestJson = request.json
    PbVideosFeedback.query.filter_by(videosFeedbackId = requestJson['videosFeedbackId']).update({'status':1})

    db.session.commit()
    resp = jsonify({})
    resp.status_code = 200;

    return resp;

# Push notification
@app.route("/addIphonePushToken", methods = ['POST'])
def pushNotif():
    requestJson = request.json
    now = datetime.datetime.now()
    iphonePushToken = PbIphonePushToken(requestJson['uid'], requestJson['deviceToken'], now)
    db.session.merge(iphonePushToken)
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
@app.route("/musicNews", methods = ['GET'])
def getMusicNews():
    musicActivity = PbMusicActivity.query.filter_by(uid=request.args['uid']).all()
    result = {'PBMusicActivity':[]}
    i=0
    for activity in musicActivity:
        result['PBMusicActivity'].append({
            'musicActivityId':activity.musicActivityId,
            'musicActivityType':activity.musicActivityType,
            'musicItemId':activity.musicItem.musicItemId,
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
            'news':[]
        })
        for feedback in activity.feedback:
            result['PBMusicActivity'][i]['news'].append(
                {
                    'musicNewsId':feedback.musicFeedbackId,
                    'followerUid':feedback.followerUid,
                    'musicActivityId':activity.musicActivityId,
                    'newsActionType':feedback.musicFeedbackType,
                    'dateAdded':feedback.dateAdded.strftime("%Y-%m-%d %H:%M:%S"),
                    'follower': 
                    {
                        'uid':feedback.follower.uid,
                        'firstName':feedback.follower.firstName,
                        'lastName':feedback.follower.lastName,
                        'fbId':feedback.follower.fbId,
                        'email':feedback.follower.email,
                        'spotifyUsername':feedback.follower.spotifyUsername,
                        'foursquareId':feedback.follower.foursquareId,
                        'youtubeUsername':feedback.follower.youtubeUsername,
                        'isPiggybackUser':feedback.follower.isPiggybackUser,
                        'dateAdded':feedback.follower.dateAdded.strftime("%Y-%m-%d %H:%M:%S"),
                        'dateBecamePbUser':feedback.follower.dateAdded.strftime("%Y-%m-%d %H:%M:%S")
                    }
                })

        i = i+1

    resp = jsonify(result)

    return resp

@app.route("/placesNews", methods = ['GET'])
def getPlacesNews():
    placesActivity = PbPlacesActivity.query.filter_by(uid=request.args['uid']).all()
    result = {'PBPlacesActivity':[]}
    i=0
    for activity in placesActivity:
        result['PBPlacesActivity'].append({
            'placesActivityId':activity.placesActivityId,
            'placesActivityType':activity.placesActivityType,
            'placesItemId':activity.placesItem.placesItemId,
            'uid':activity.uid,
            'dateAdded':activity.dateAdded.strftime("%Y-%m-%d %H:%M:%S"),
            'placesItem':
            {
                'placesItemId':activity.placesItem.placesItemId,
                'name':activity.placesItem.name,
                'phone':activity.placesItem.phone,
                'addr':activity.placesItem.addr,
                'addrCity':activity.placesItem.addrCity,
                'addrState':activity.placesItem.addrState,
                'addrCountry':activity.placesItem.addrCountry,
                'addrZip':activity.placesItem.addrZip,
                'foursquareReferenceId':activity.placesItem.foursquareReferenceId,
                'lat':activity.placesItem.lat,
                'lng':activity.placesItem.lng,
                'photoURL':activity.placesItem.photoURL
            },
            'news':[]
        })
        for feedback in activity.feedback:
            result['PBPlacesActivity'][i]['news'].append(
                {
                    'placesNewsId':feedback.placesFeedbackId,
                    'followerUid':feedback.followerUid,
                    'placesActivityId':activity.placesActivityId,
                    'newsActionType':feedback.placesFeedbackType,
                    'dateAdded':feedback.dateAdded.strftime("%Y-%m-%d %H:%M:%S"),
                    'follower': 
                    {
                        'uid':feedback.follower.uid,
                        'firstName':feedback.follower.firstName,
                        'lastName':feedback.follower.lastName,
                        'fbId':feedback.follower.fbId,
                        'email':feedback.follower.email,
                        'spotifyUsername':feedback.follower.spotifyUsername,
                        'foursquareId':feedback.follower.foursquareId,
                        'youtubeUsername':feedback.follower.youtubeUsername,
                        'isPiggybackUser':feedback.follower.isPiggybackUser,
                        'dateAdded':feedback.follower.dateAdded.strftime("%Y-%m-%d %H:%M:%S"),
                        'dateBecamePbUser':feedback.follower.dateAdded.strftime("%Y-%m-%d %H:%M:%S")
                    }
                })

        i = i+1

    resp = jsonify(result)

    return resp

@app.route("/videosNews", methods = ['GET'])
def getVideosNews():
    videosActivity = PbVideosActivity.query.filter_by(uid=request.args['uid']).all()
    result = {'PBVideosActivity':[]}
    i=0
    for activity in videosActivity:
        result['PBVideosActivity'].append({
            'videosActivityId':activity.videosActivityId,
            'videosActivityType':activity.videosActivityType,
            'videosItemId':activity.videosItem.videosItemId,
            'uid':activity.uid,
            'dateAdded':activity.dateAdded.strftime("%Y-%m-%d %H:%M:%S"),
            'videosItem':
            {
                'videosItemId':activity.videosItem.videosItemId,
                'name':activity.videosItem.name,
                'videoURL':activity.videosItem.videoURL
            },
            'news':[]
        })
        for feedback in activity.feedback:
            result['PBVideosActivity'][i]['news'].append(
                {
                    'videosNewsId':feedback.videosFeedbackId,
                    'followerUid':feedback.followerUid,
                    'videosActivityId':activity.videosActivityId,
                    'newsActionType':feedback.videosFeedbackType,
                    'dateAdded':feedback.dateAdded.strftime("%Y-%m-%d %H:%M:%S"),
                    'follower': 
                    {
                        'uid':feedback.follower.uid,
                        'firstName':feedback.follower.firstName,
                        'lastName':feedback.follower.lastName,
                        'fbId':feedback.follower.fbId,
                        'email':feedback.follower.email,
                        'spotifyUsername':feedback.follower.spotifyUsername,
                        'foursquareId':feedback.follower.foursquareId,
                        'youtubeUsername':feedback.follower.youtubeUsername,
                        'isPiggybackUser':feedback.follower.isPiggybackUser,
                        'dateAdded':feedback.follower.dateAdded.strftime("%Y-%m-%d %H:%M:%S"),
                        'dateBecamePbUser':feedback.follower.dateAdded.strftime("%Y-%m-%d %H:%M:%S")
                    }
                })

        i = i+1

    resp = jsonify(result)

    return resp

@app.route("/musicActivity", methods = ['GET'])
def getMusicActivity():
    requestJson = request.json
    musicActivity = PbMusicActivity.query.filter_by(musicItemId=requestJson.get('musicItemId'), uid=requestJson.get('uid')).first()
    resp = None
    if musicActivity == None:
        resp = jsonify({'error':'MusicActivity does not exist'})
        resp.status_code = 404
    else:
        resp = jsonify({"PBMusicActivity":{"musicActivityId":musicActivity.musicActivityId,
                                            "uid":musicActivity.uid,
                                            "musicItemId":musicActivity.musicItemId,
                                            "musicActivityType":musicActivity.musicActivityType,
                                            "dateAdded":musicActivity.dateAdded.strftime("%Y-%m-%d %H:%M:%S")}})
        resp.status_code = 200

    return resp

@app.route("/addMusicActivity", methods = ['POST'])
def addMusicActivity():
    requestJson = request.json
    resp = getMusicActivity()
    if resp.status_code == 404:
        now = datetime.datetime.now()
        musicActivity = PbMusicActivity(requestJson.get('uid'),
                                        requestJson.get('musicItemId'),
                                        requestJson.get('musicActivityType'),
                                        now)
        db.session.add(musicActivity)
        db.session.commit()

        resp = jsonify({"PBMusicActivity":{"musicActivityId":musicActivity.musicActivityId,"dateAdded":musicActivity.dateAdded.strftime("%Y-%m-%d %H:%M:%S")}})
        resp.status_code = 200

    return resp

# placesItem API
@app.route("/placesItem", methods = ['GET'])
def getPlacesItem():
    requestJson = request.json
    placesItem = PbPlacesItem.query.filter_by(foursquareReferenceId=requestJson.get('foursquareReferenceId')).first()
    resp = None
    if placesItem == None:
        resp = jsonify({'error':'PlacesItem does not exist'})
        resp.status_code = 404
    else:
        resp = jsonify({"PBPlacesItem":{"placesItemId":placesItem.placesItemId, 
                        "name":placesItem.name, 
                        "phone":placesItem.phone, 
                        "addr":placesItem.addr, 
                        "addrCity":placesItem.addrCity, 
                        "addrState":placesItem.addrState, 
                        "addrCountry":placesItem.addrCountry,
                        "addrZip":placesItem.addrZip,
                        "foursquareReferenceId":placesItem.foursquareReferenceId,
                        "lat":placesItem.lat,
                        "lng":placesItem.lng,
                        "photoURL":placesItem.photoURL}})
        
        resp.status_code = 200

    return resp

@app.route("/updatePlacesItem", methods = ['PUT'])
def updatePlacesItem():
    requestJson = request.json
    resp = jsonify({})
    if requestJson.get('photoURL'):
        PbPlacesItem.query.filter_by(foursquareReferenceId=requestJson['foursquareReferenceId']).update({'photoURL':requestJson['photoURL']})
        db.session.commit()
        resp = jsonify({"PBPlacesItem":{"photoURL":requestJson['photoURL']}})
        resp.status_code = 200

    return resp

@app.route("/addPlacesItem", methods = ['POST'])
def addPlacesItem():
    requestJson = request.json
    resp = getPlacesItem()
    if resp.status_code == 404:
        placesItem = PbPlacesItem(requestJson.get('name'),
                                    requestJson.get('phone'),
                                    requestJson.get('addr'),
                                    requestJson.get('addrCity'),
                                    requestJson.get('addrState'),
                                    requestJson.get('addrCountry'),
                                    requestJson.get('addrZip'),
                                    requestJson.get('foursquareReferenceId'),
                                    requestJson.get('lat'),
                                    requestJson.get('lng'),
                                    requestJson.get('photoURL'))
        db.session.add(placesItem)
        db.session.commit()

        resp = jsonify({"PBPlacesItem":{"placesItemId":placesItem.placesItemId}})
        resp.status_code = 200

    return resp

@app.route("/placesActivity", methods = ['GET'])
def getPlacesActivity():
    requestJson = request.json
    placesActivity = PbPlacesActivity.query.filter_by(placesItemId=requestJson.get('placesItemId'), uid=requestJson.get('uid')).first()
    resp = None
    if placesActivity == None:
        resp = jsonify({'error':'PlacesActivity does not exist'})
        resp.status_code = 404
    else:
        resp = jsonify({"PBPlacesActivity":{"placesActivityId":placesActivity.placesActivityId,
                                            "uid":placesActivity.uid,
                                            "placesItemId":placesActivity.placesItemId,
                                            "placesActivityType":placesActivity.placesActivityType,
                                            "dateAdded":placesActivity.dateAdded.strftime("%Y-%m-%d %H:%M:%S")}})
        resp.status_code = 200

    return resp

@app.route("/addPlacesActivity", methods = ['POST'])
def addPlacesActivity():
    requestJson = request.json
    resp = getPlacesActivity()
    if resp.status_code == 404:
        now = datetime.datetime.now()
        placesActivity = PbPlacesActivity(requestJson.get('uid'),
                                        requestJson.get('placesItemId'),
                                        requestJson.get('placesActivityType'),
                                        now)
        db.session.add(placesActivity)
        db.session.commit()

        resp = jsonify({"PBPlacesActivity":{"placesActivityId":placesActivity.placesActivityId,"dateAdded":placesActivity.dateAdded.strftime("%Y-%m-%d %H:%M:%S")}})
        resp.status_code = 200

    return resp

@app.route("/videosActivity", methods = ['GET'])
def getVideosActivity():
    requestJson = request.json
    videosActivity = PbVideosActivity.query.filter_by(videosItemId=requestJson.get('videosItemId'), uid=requestJson.get('uid')).first()
    resp = None
    if videosActivity == None:
        resp = jsonify({'error':'videosActivity does not exist'})
        resp.status_code = 404
    else:
        resp = jsonify({"PBVideosActivity":{"videosActivityId":videosActivity.videosActivityId,
                                            "uid":videosActivity.uid,
                                            "videosItemId":videosActivity.videosItemId,
                                            "videosActivityType":videosActivity.videosActivityType,
                                            "dateAdded":videosActivity.dateAdded.strftime("%Y-%m-%d %H:%M:%S")}})
        resp.status_code = 200

    return resp

@app.route("/addVideosActivity", methods = ['POST'])
def addVideosActivity():
    requestJson = request.json
    resp = getVideosActivity()
    if resp.status_code == 404:
        now = datetime.datetime.now()
        videosActivity = PbVideosActivity(requestJson.get('uid'),
                                            requestJson.get('videosItemId'),
                                            requestJson.get('videosActivityType'),
                                            now)
        db.session.add(videosActivity)
        db.session.commit()

        resp = jsonify({"PBVideosActivity":{"videosActivityId":videosActivity.videosActivityId,"dateAdded":videosActivity.dateAdded.strftime("%Y-%m-%d %H:%M:%S")}})
        resp.status_code = 200

    return resp

# videosItem API
@app.route("/videosItem", methods = ['GET'])
def getVideosItem():
    requestJson = request.json
    videosItem = PbVideosItem.query.filter_by(videoURL=requestJson.get('videoURL')).first()
    resp = None
    if videosItem == None:
        resp = jsonify({'error':'PlacesItem does not exist'})
        resp.status_code = 404
    else:
        resp = jsonify({"PBVideosItem":{"videosItemId":videosItem.videosItemId,
                                        "name":videosItem.name,
                                        "videoURL":videosItem.videoURL}})

        resp.status_code = 200

    return resp
    
@app.route("/addVideosItem", methods = ['POST'])
def addVideosItem():
    requestJson = request.json
    resp = getVideosItem()
    if resp.status_code == 404:
        videosItem = PbVideosItem(requestJson.get('name'),
                                    requestJson.get('videoURL'))
        db.session.add(videosItem)
        db.session.commit()

        resp = jsonify({"PBVideosItem":{"videosItemId":videosItem.videosItemId}})
        resp.status_code = 200

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
        resp.headers['Access-Control-Allow-Origin'] = '*'

    return resp

@app.route("/addEmailListing", methods = ['POST'])
@crossdomain(origin='*')
def addEmailListing():
    # resp = jsonify({})

    requestJson = request.json
    resp = getEmailListing() 
    if resp.status_code == 404:
        # email does not exist - add it
        now = datetime.datetime.now()
        emailListing = PbEmailListing(requestJson.get('emailAddress'),now)
        db.session.add(emailListing)
        db.session.commit()

        resp = jsonify({"PBEmailListing":{"emailId":emailListing.emailId,"emailAddress":emailListing.emailAddress}})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.status_code = 200

    return resp

# profile page API
@app.route("/profilePage", methods = ['GET'])
def getProfilePage():
    numMusicPiggybackers = 0
    numPlacesPiggybackers = 0
    numVideosPiggybackers = 0
    numMusicLikes = 0
    numPlacesLikes = 0
    numVideosLikes = 0
    numMusicSaves = 0
    numPlacesSaves = 0
    numVideosSaves = 0
    piggybackers = PbAmbassador.query.filter_by(ambassadorUid=request.args['uid'], deleted=0 ).all()
    musicActivity = PbMusicActivity.query.filter_by(uid=request.args['uid']).all()
    placesActivity = PbPlacesActivity.query.filter_by(uid=request.args['uid']).all()
    videosActivity = PbVideosActivity.query.filter_by(uid=request.args['uid']).all()

    for piggybacker in piggybackers:
        if piggybacker.ambassadorType == "music":
            numMusicPiggybackers = numMusicPiggybackers + 1
        if piggybacker.ambassadorType == "places":
            numPlacesPiggybackers = numPlacesPiggybackers + 1
        if piggybacker.ambassadorType == "videos":
            numVideosPiggybackers = numVideosPiggybackers + 1

    for activity in musicActivity:
        for feedback in activity.feedback:
            if feedback.musicFeedbackType == "todo":
                numMusicSaves = numMusicSaves + 1
            elif feedback.musicFeedbackType == "like":
                numMusicLikes = numMusicLikes + 1

    for activity in placesActivity:
        for feedback in activity.feedback:
            if feedback.placesFeedbackType == "todo":
                numPlacesSaves = numPlacesSaves + 1
            elif feedback.placesFeedbackType == "like":
                numPlacesLikes = numPlacesLikes + 1

    for activity in videosActivity:
        for feedback in activity.feedback:
            if feedback.videosFeedbackType == "todo":
                numVideosSaves = numVideosSaves + 1
            elif feedback.videosFeedbackType == "like":
                numVideosLikes = numVideosLikes + 1

    # result = {'numPiggybackers':numPiggybackers, 'numLikes':numLikes, 'numSaves':numSaves}
    result = {'numMusicPiggybackers':numMusicPiggybackers, 'numPlacesPiggybackers':numPlacesPiggybackers, 'numVideosPiggybackers':numVideosPiggybackers,
                'numMusicLikes':numMusicLikes, 'numPlacesLikes':numPlacesLikes, 'numVideosLikes':numVideosLikes, 'numMusicSaves':numMusicSaves,
                'numPlacesSaves':numPlacesSaves, 'numVideosSaves':numVideosSaves}
    resp = jsonify(result)

    return resp

# routing
@app.route("/", methods = ['GET'])
def index():
    return render_template('home.html', route="about" )

@app.route("/splash", methods = ['GET'])
def showSplash():
    return render_template('home.html', route="about")

@app.route("/about", methods = ['GET'])
def showAbout():
    return render_template('home.html', route="about")

@app.route("/team", methods = ['GET'])
def showTeam():
    return render_template('home.html', route="team")

@app.route("/demo", methods = ['GET'])
def showDemo():
    return render_template('home.html', route="demo")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)