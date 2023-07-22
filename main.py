from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from google.cloud import datastore
from google.cloud import storage
from google.auth.transport import requests
from pprint import pprint
import datetime
import google.oauth2.id_token

app = Flask(__name__)
datastore_client = datastore.Client()
firebase_request_adapter = requests.Request()


@app.route('/')
def root():
    ''' Function to handle the home route. '''
    id_token = request.cookies.get("token")
    user_entity = None
    user_id = None

    if id_token:
        try:
            # verify id token
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter)

            user_id = claims['user_id']
            user_key = datastore_client.key('User', user_id)

            # get user entity
            user_entity = datastore_client.get(user_key)

            if user_entity == None:
                # create user
                entity = datastore.Entity(key=user_key)
                entity.update({
                    'setup': 0
                })
                datastore_client.put(entity)

                # get created user
                user_entity = datastore_client.get(user_key)

            if not user_entity['setup']:
                url = f"/user/{user_id}/edit"
                return redirect(url)

            # session['user_entity'] = user_entity
            session['user_id'] = claims['user_id']
            session['username'] = user_entity['username']

        except ValueError as exc:
            error_message = str(exc)
    return render_template('index.html', user_entity=user_entity, user_id=user_id)



# User
# user list
@app.route('/api/user/', methods=['GET', 'POST'])
def user_list():
    if request.method == 'GET':
        # get all users
        pass
    elif request.method == 'POST':
        # create a new user
        pass

# user detail
@app.route('/api/user/<string:user_id>/', methods=['GET', 'PUT', 'DELETE'])
def user_list(user_id):
    if request.method == 'GET':
        # get a user
        pass
    elif request.method == 'PUT':
        # update a user
        pass
    elif request.method == 'DELETE':
        # delete a user
        pass

# Gallery
# Gallery list
@app.route('/api/gallery/', methods=['GET', 'POST'])
def gallery_list():
    if request.method == 'GET':
        # get all galleries
        pass
    elif request.method == 'POST':
        # create a new gallery
        pass

# detail
@app.route('/api/gallery/<string:gallery_id>/', methods=['GET', 'PUT', 'DELETE'])
def gallery_detail(gallery_id):
    if request.method == 'GET':
        # get a gallery
        pass
    elif request.method == 'PUT':
        # update a gallery
        pass
    elif request.method == 'DELETE':
        # delete a gallery
        pass

# Image
# Image list
@app.route('/api/image/', methods=['GET', 'POST'])
def image_list():
    if request.method == 'GET':
        # get all images
        pass
    elif request.method == 'POST':
        # create a new image
        pass

# Image detail
@app.route('/api/image/<string:image_id>/', methods=['GET', 'PUT', 'DELETE'])
def image_detail():
    if request.method == 'GET':
        # get an image
        pass
    elif request.method == 'PUT':
        # update an image
        pass
    elif request.method == 'DELETE':
        # delete an image
        pass



@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(host='127.0.0.1', port=8080, debug=True)
