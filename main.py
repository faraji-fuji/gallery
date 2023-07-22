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

            # if user_entity == None:
            #     # create user
            #     entity = datastore.Entity(key=user_key)
            #     entity.update({
            #         'setup': 0
            #     })
            #     datastore_client.put(entity)

            #     # get created user
            #     user_entity = datastore_client.get(user_key)

            # if not user_entity['setup']:
            #     url = f"/user/{user_id}/edit"
            #     return redirect(url)

            # # session['user_entity'] = user_entity
            # session['user_id'] = claims['user_id']
            # session['username'] = user_entity['username']

        except ValueError as exc:
            error_message = str(exc)
    return render_template('index.html', user_entity=user_entity, user_id=user_id)

# frontend
@app.route('/user/edit/')
def user_edit():
    return render_template('user-edit.html')

# User
# user list
@app.route('/api/user/', methods=['GET', 'POST'])
def user_list():
    if request.method == 'GET':
        # Get all users
        query = datastore_client.query(kind='User')
        users = list(query.fetch())
        return jsonify(users)

    elif request.method == 'POST':
        # Create a new user
        user_key = datastore_client.key('User')

        entity = datastore.Entity(key=user_key)
        entity.update({
            'setup': 0
        })
        datastore_client.put(entity)

        # Get created user
        user_entity = datastore_client.get(user_key)
        return jsonify(user_entity)

# User detail
@app.route('/api/user/<string:user_id>/', methods=['GET', 'PUT', 'DELETE'])
def user_detail(user_id):
    user_key = datastore_client.key('User', int(user_id))

    if request.method == 'GET':
        # Get a user
        user_entity = datastore_client.get(user_key)
        return jsonify(user_entity)

    elif request.method == 'PUT':
        # Update a user
        user_entity = datastore_client.get(user_key)
        if not user_entity:
            return jsonify({'error': 'User not found'}), 404

        # Update the user properties as needed
        user_entity['setup'] = 1
        datastore_client.put(user_entity)

        return jsonify(user_entity)

    elif request.method == 'DELETE':
        # Delete a user
        user_entity = datastore_client.get(user_key)
        if not user_entity:
            return jsonify({'error': 'User not found'}), 404

        datastore_client.delete(user_key)
        return jsonify({'message': 'User deleted successfully'})

# Gallery
# Gallery list
@app.route('/api/gallery/', methods=['GET', 'POST'])
def gallery_list():
    if request.method == 'GET':
        # Get all galleries
        query = datastore_client.query(kind='Gallery')
        galleries = list(query.fetch())
        return jsonify(galleries)

    elif request.method == 'POST':
        # Create a new gallery
        gallery_key = datastore_client.key('Gallery')

        entity = datastore.Entity(key=gallery_key)
        # Set properties of the gallery entity based on the request data
        entity['name'] = request.json.get('name', '')
        entity['description'] = request.json.get('description', '')
        # Add more properties as needed

        datastore_client.put(entity)

        # Get created gallery
        gallery_entity = datastore_client.get(gallery_key)
        return jsonify(gallery_entity)

# Gallery detail
@app.route('/api/gallery/<string:gallery_id>/', methods=['GET', 'PUT', 'DELETE'])
def gallery_detail(gallery_id):
    gallery_key = datastore_client.key('Gallery', int(gallery_id))

    if request.method == 'GET':
        # Get a gallery
        gallery_entity = datastore_client.get(gallery_key)
        return jsonify(gallery_entity)

    elif request.method == 'PUT':
        # Update a gallery
        gallery_entity = datastore_client.get(gallery_key)
        if not gallery_entity:
            return jsonify({'error': 'Gallery not found'}), 404

        # Update the gallery properties based on the request data
        gallery_entity['name'] = request.json.get('name', gallery_entity['name'])
        gallery_entity['description'] = request.json.get('description', gallery_entity['description'])
        # Update more properties as needed

        datastore_client.put(gallery_entity)

        return jsonify(gallery_entity)

    elif request.method == 'DELETE':
        # Delete a gallery
        gallery_entity = datastore_client.get(gallery_key)
        if not gallery_entity:
            return jsonify({'error': 'Gallery not found'}), 404

        datastore_client.delete(gallery_key)
        return jsonify({'message': 'Gallery deleted successfully'})


# Image
# Image list
@app.route('/api/image/', methods=['GET', 'POST'])
def image_list():
    if request.method == 'GET':
        # Get all images
        query = datastore_client.query(kind='Image')
        images = list(query.fetch())
        return jsonify(images)

    elif request.method == 'POST':
        # Create a new image
        image_key = datastore_client.key('Image')

        entity = datastore.Entity(key=image_key)
        # Set properties of the image entity based on the request data
        entity['url'] = request.json.get('url', '')
        entity['description'] = request.json.get('description', '')
        # Add more properties as needed

        datastore_client.put(entity)

        # Get created image
        image_entity = datastore_client.get(image_key)
        return jsonify(image_entity)
    
# Image detail
@app.route('/api/image/<string:image_id>/', methods=['GET', 'PUT', 'DELETE'])
def image_detail(image_id):
    image_key = datastore_client.key('Image', int(image_id))

    if request.method == 'GET':
        # Get an image
        image_entity = datastore_client.get(image_key)
        return jsonify(image_entity)

    elif request.method == 'PUT':
        # Update an image
        image_entity = datastore_client.get(image_key)
        if not image_entity:
            return jsonify({'error': 'Image not found'}), 404

        # Update the image properties based on the request data
        image_entity['url'] = request.json.get('url', image_entity['url'])
        image_entity['description'] = request.json.get('description', image_entity['description'])
        # Update more properties as needed

        datastore_client.put(image_entity)

        return jsonify(image_entity)

    elif request.method == 'DELETE':
        # Delete an image
        image_entity = datastore_client.get(image_key)
        if not image_entity:
            return jsonify({'error': 'Image not found'}), 404

        datastore_client.delete(image_key)
        return jsonify({'message': 'Image deleted successfully'})



@app.route('/logout/', methods=['GET'])
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(host='127.0.0.1', port=8080, debug=True)
