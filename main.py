from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from google.cloud import datastore
from google.cloud import storage
from google.auth.transport import requests
from pprint import pprint
from datetime import datetime
import google.oauth2.id_token
import local_constants

app = Flask(__name__)
datastore_client = datastore.Client()
firebase_request_adapter = requests.Request()
storage_client = storage.Client(project=local_constants.PROJECT_NAME)
bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)


@app.route('/')
def root():
    """
    Function to handle the home route. 
    """
    id_token = request.cookies.get("token")
    user_entity = None
    user_id = None

    if id_token:
        try:
            # verify token
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter)

            session['user_id'] = claims['user_id']
            user_id = claims['user_id']
            user_key = datastore_client.key('User', user_id)
            user_entity = datastore_client.get(key=user_key)
            
            if user_entity == None:
                # create user if user object does not exist
                entity = datastore.Entity(key=user_key)
                entity.update({
                    'user_id': claims['user_id']
                })
                datastore_client.put(entity)
                return redirect("/gallery/create/")
            
        except ValueError as exc:
            error_message = str(exc)
    return redirect("/gallery/index/")

# frontend
# User
@app.route('/user/<string:user_id>/edit/')
def user_edit(user_id):
    data={"user_id": user_id}
    return render_template('user-edit.html', data=data)



# Gallery Routes

@app.route("/gallery/index/")
def gallery_index():
    """
    A list of all galleries for a particular user.
    """
    user_id = session.get('user_id')
    ancestor_key = datastore_client.key('User', user_id)
    query = datastore_client.query(kind='Gallery', ancestor=ancestor_key)
    query.order = ['-created_at']
    galleries = list(query.fetch())

    # Extract gallery IDs and convert galleries to a list of dictionaries
    gallery_list = [{'id': gallery.id, 'title': gallery['title'], 'description': gallery['description']} for gallery in galleries]

    data = {
        "galleries": gallery_list
    }

    return render_template("gallery-index.html", data=data)

@app.route('/gallery/<string:gallery_id>/detail/')
def gallery_detail(gallery_id):
    """
    View a gallery.
    """
    user_id = session.get('user_id')
    gallery_key = datastore_client.key('User', user_id, 'Gallery', int(gallery_id))
    gallery_entity = datastore_client.get(key=gallery_key)
    
    data={
        "gallery": dict(gallery_entity),
        "gallery_id": gallery_id}
    
    return render_template('gallery-detail.html', data=data)


@app.route('/gallery/create/')
def gallery_create():
    """
    Form to create a new gallery.
    """
    return render_template('gallery-create.html')


@app.route('/gallery/add/', methods=["POST"])
def gallery_add():
    """
    Add a new gallery.
    """
    user_id = session.get('user_id')
    gallery_key = datastore_client.key('User', user_id, 'Gallery')
    entity = datastore.Entity(key=gallery_key)
    
    entity['title'] = request.form.get('title')
    entity['description'] = request.form.get('description')
    entity['created_at'] = datetime.now()
    entity['updated_at'] = datetime.now()
    datastore_client.put(entity)

    return redirect("/gallery/index/")


@app.route('/gallery/<string:gallery_id>/edit/')
def gallery_edit(gallery_id):
    user_id = session.get('user_id')
    gallery_key = datastore_client.key('User', user_id, 'Gallery', int(gallery_id))
    gallery_entity = datastore_client.get(key=gallery_key)
    
    data={
        "gallery": dict(gallery_entity),
        "gallery_id": gallery_id}
    
    return render_template('gallery-edit.html', data=data)
    
@app.route("/gallery/<string:gallery_id>/update/", methods=['POST'])
def gallery_update(gallery_id):
    """
    Update a gallery.
    """
    user_id = session.get('user_id')
    gallery_key = datastore_client.key('User', user_id, 'Gallery', int(gallery_id))    
    gallery_entity = datastore_client.get(key=gallery_key)
    gallery_entity['title'] = request.form.get('title')
    gallery_entity['description'] = request.form.get('description')
    datastore_client.put(gallery_entity)
    return redirect("/gallery/index/")


@app.route("/gallery/<string:gallery_id>/delete/")
def delete_gallery(gallery_id):
    """
    Delete a gallery.
    """
    user_id = session.get('user_id')
    gallery_key = datastore_client.key('User', user_id, 'Gallery', int(gallery_id))    
    gallery_entity = datastore_client.get(key=gallery_key)
    datastore_client.delete(gallery_key)
    return redirect("/gallery/index/")




# Image Routes
@app.route('/image/add/', methods=['POST'])
def image_add():
    """
    Add a new image.
    """
    # get file and caption uploaded from the browser
    gallery_id = request.form.get('gallery_id')
    print(f"GALLERY ID: {gallery_id}")
    file = request.files['file_name']
    print(file)
    gallery_id = request.form.get('gallery_id')

    # upload file to cloud storage, get public image url
    blob = bucket.blob(file.filename)
    blob.upload_from_file(file)
    blob.make_public()
    image_url = blob.public_url

    image_key = datastore_client.key('Image')
    entity = datastore.Entity(key=image_key)
    entity['url'] = image_url
    entity['gallery_id'] = gallery_id
    entity['created_at'] = datetime.now()
    entity['updated_at'] = datetime.now()
    datastore_client.put(entity)

    return redirect(f'/gallery/{gallery_id}/detail/')




# User
# user list
@app.route('/api/user/', methods=['GET', 'POST'])
def api_user_list():
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
def api_user_detail(user_id):
    user_key = datastore_client.key('User', user_id)

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
        user_entity['name'] = request.form.get("name") 
        datastore_client.put(user_entity)

        return redirect("/gallery/create/")

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
def api_gallery_list():
    user_id = session.get('user_id')

    if request.method == 'GET':
        if user_id:
            # Get galleries for a specific user
            ancestor_key = datastore_client.key('User', user_id)
            query = datastore_client.query(kind='Gallery', ancestor=ancestor_key)
            query.order = ['-created_at']
            galleries = list(query.fetch())

        else:
            # Get all galleries if no user_id is provided
            query = datastore_client.query(kind='Gallery')
            galleries = list(query.fetch())
        
        # Extract gallery IDs and convert galleries to a list of dictionaries
        gallery_list = [{'id': gallery.id, 'title': gallery['title'], 'description': gallery['description']} for gallery in galleries]

        return jsonify(gallery_list)

    elif request.method == 'POST':
        # Create a new gallery
        gallery_key = datastore_client.key('User', user_id, 'Gallery')
        entity = datastore.Entity(key=gallery_key)
        
        # Set properties of the gallery entity based on the request data
        entity['title'] = request.form.get('title')
        entity['description'] = request.form.get('description')
        entity['created_at'] = datetime.now()
        entity['updated_at'] = datetime.now()
        datastore_client.put(entity)

        return jsonify(entity)


# Gallery detail
@app.route('/api/gallery/<string:gallery_id>/', methods=['GET', 'PUT', 'DELETE'])
def api_gallery_detail(gallery_id):
    user_id = session['user_id']

    print(f"USER ID {user_id}")
    gallery_key = datastore_client.key('User', user_id, 'Gallery', int(gallery_id))
    print(f"GALLERY KEY {gallery_key}")

    if request.method == 'GET':
        # Get a gallery
        gallery_entity = datastore_client.get(key=gallery_key)
        if not gallery_entity:
            print("NOT FOUND")
            return jsonify({'error': 'Gallery not found'}), 404
        return jsonify(gallery_entity)

    elif request.method == 'PUT':
        gallery_entity = datastore_client.get(key=gallery_key)
        gallery_entity['title'] = request.form.get('title')
        datastore_client.put(gallery_entity)
        return jsonify(gallery_entity)



# Image
# Image list
@app.route('/api/image/', methods=['GET', 'POST'])
def api_image_list():
    if request.method == 'GET':
        gallery_id = request.args.get('gallery_id')
        if gallery_id:
            # Filter images by gallery ID
            query = datastore_client.query(kind='Image')
            query.add_filter('gallery_id', '=', gallery_id)
            images = list(query.fetch())
        else:
            # Get all images if no 'gallery_id' is provided
            query = datastore_client.query(kind='Image')
            images = list(query.fetch())

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
def api_image_detail(image_id):
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
