import os
import simplejson
from flask import Flask, render_template, redirect, url_for, request, Response, jsonify
from flaskext.sqlalchemy import SQLAlchemy
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

if not os.environ.get('PROD'):
    app.config['SQLALCHEMY_ECHO'] = True
    app.debug = True

db = SQLAlchemy(app)

class PbUser(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(64))
    lastName = db.Column(db.String(64))
    fbId = db.Column(db.BigInteger, unique=True)
    email = db.Column(db.String(64))
    spotifyUsername = db.Column(db.String(32), unique=True)
    foursquareId = db.Column(db.BigInteger, unique=True)
    youtubeUsername = db.Column(db.String(32), unique=True)
    isPiggybackUser = db.Column(db.Boolean)
    ambassadors = db.relationship('PbAmbassador', backref='follower', lazy='dynamic')

    def __init__(self, firstName, lastName, fbId, email, spotifyUsername, foursquareId, youtubeUsername, isPiggybackUser):
        self.firstName = firstName
        self.lastName = lastName
        self.fbId = fbId
        self.email = email
        self.spotifyUsername = spotifyUsername
        self.foursquareId = foursquareId
        self.youtubeUsername = youtubeUsername  
        self.isPiggybackUser = isPiggybackUser

class PbAmbassador(db.Model):
    followerUid = db.Column(db.Integer, db.ForeignKey("pb_user.uid"))
    ambassadorUid = db.Column(db.Integer, primary_key=True)
    ambassadorType = db.Column(db.String(16), primary_key=True)

    def __init__(self, followerUid, ambassadorUid, ambassadorType):
        self.ambassadorUid = ambassadorUid
        self.ambassadorType = ambassadorType
        self.followerUid = followerUid

@app.route("/")
def index():
    return 'Hello World'

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
        resp = jsonify(uid=user.uid, firstName=user.firstName, lastName=user.lastName, fbid=user.fbId, email=user.email,
            spotifyUsername=user.spotifyUsername, foursquareId=user.foursquareId, youtubeUsername=user.youtubeUsername,
            isPiggybackUser=user.isPiggybackUser)
        resp.status_code = 200

    return resp

@app.route("/addUser", methods = ['POST'])
def addUser():
    requestJson = request.json
    resp = getUser()
    if resp.status_code == 404:
        # user does not exist - add user
        user = PbUser(requestJson.get('firstName'), requestJson.get('lastName'), requestJson.get('fbId'), requestJson.get('email'), 
            requestJson.get('spotifyUsername'), requestJson.get('foursquareId'), requestJson.get('youtubeUsername'), 
            requestJson.get('isPiggybackUser'))
        db.session.add(user)
        db.session.commit()

        # TODO: if db insert was successful, return status 200. 
        resp = jsonify({"PbUser":{"uid":user.uid, "firstName":user.firstName, "lastName":user.lastName, "fbid":user.fbId, "email":user.email,
            "spotifyUsername":user.spotifyUsername, "foursquareId":user.foursquareId, "youtubeUsername":user.youtubeUsername,
            "isPiggybackUser":user.isPiggybackUser}})
        resp.status_code = 200

    return resp

@app.route("/updateUserSpotify", methods = ['POST'])
def updateUserSpotify():
    requestJson = request.json
    PbUser.query.filter_by(uid = requestJson['uid']).update({'spotifyUsername':requestJson['spotifyUsername']})
    db.session.commit()

    # TODO: if db insert was successful, return status 200. 
    message = {'status': 200}
    resp = jsonify(message)
    resp.status_code = 200

    return resp

@app.route("/updateUserFoursquare", methods = ['POST'])
def updateUserFoursquare():
    requestJson = request.json
    PbUser.query.filter_by(uid = requestJson['uid']).update({'foursquareId':requestJson['foursquareId']})
    db.session.commit()

    # TODO: if db insert was successful, return status 200. 
    message = {'status': 200}
    resp = jsonify(message)
    resp.status_code = 200

    return resp

@app.route("/updateUserYoutube", methods = ['POST'])
def updateUserYoutube():
    requestJson = request.json
    PbUser.query.filter_by(uid = requestJson['uid']).update({'youtubeUsername':requestJson['youtubeUsername']})
    db.session.commit()

    # TODO: if db insert was successful, return status 200. 
    message = {'status': 200}
    resp = jsonify(message)
    resp.status_code = 200

    return resp

@app.route("/updateUserUsingPb", methods = ['POST'])
def updateUserUsingPb():
    requestJson = request.json
    PbUser.query.filter_by(uid = requestJson['uid']).update({'isPiggybackUser':requestJson['isPiggybackUser']})
    db.session.commit()

    # TODO: if db insert was successful, return status 200. 
    message = {'status': 200}
    resp = jsonify(message)
    resp.status_code = 200

    return resp

# Ambassador API
@app.route("/addAmbassador", methods = ['POST'])
def addAmbassador():
    requestJson = request.json
    ambassador = PbAmbassador(requestJson['followerUid'], requestJson['ambassadorUid'], requestJson['ambassadorType'])
    db.session.add(ambassador)
    db.session.commit()

    # TODO: if db insert was successful, return status 200. 
    message = {'status': 200}
    resp = jsonify(message)
    resp.status_code = 200

    return resp


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)