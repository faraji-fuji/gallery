from flask import Flask, render_template, request, redirect, flash
from werkzeug.utils import secure_filename
from google.cloud import datastore
from google.cloud import storage
from google.auth.transport import requests
from pprint import pprint
from datetime import datetime
import google.oauth2.id_token
import local_constants
import hashlib
from collections import defaultdict

app = Flask(__name__)
app.secret_key = "kafmfakkfdjhjs7535kje"

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
    data={}

    if id_token:
        try:
            # verify token
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter)

            # get user id, key and entity
            user_id = claims['user_id']
            user_key = datastore_client.key('User', user_id)
            user_entity = datastore_client.get(key=user_key)
            
            # create a user if is none
            if user_entity == None:
                entity = datastore.Entity(key=user_key)
                entity.update({
                    'user_id': claims['user_id'],
                    'email':claims['email']
                })
                datastore_client.put(entity)

            # prepare data
            data = {"user_id":user_id}

            # get galleries of a user
            ancestor_key = datastore_client.key('User', user_id)
            query = datastore_client.query(kind='Gallery', ancestor=ancestor_key)
            query.order = ['-created_at']
            galleries = list(query.fetch())

            # Prepare a list to store gallery details with the first image
            gallery_list = []

            for gallery in galleries:
                gallery_id = gallery.id

                # Query the first image associated with the gallery
                query = datastore_client.query(kind='Image')
                query.add_filter('gallery_id', '=', str(gallery_id))
                query.order = ['created_at']
                images = list(query.fetch(1))
                first_image = images[0] if images else None

                # Prepare data for the template
                gallery_data = {
                    'id': gallery_id,
                    'title': gallery['title'],
                    'description': gallery['description'],
                    'first_image_url': first_image.get('url') if first_image else None
                }
                gallery_list.append(gallery_data)

            data = {"galleries": gallery_list}

            return render_template("index.html", data=data)

        except ValueError as exc:
            error_message = str(exc)
            print(f"AN ERROR OCCURED {error_message}")
            data = {"error_message":error_message}
            flash(error_message)

    return render_template("index.html", data=data)


@app.route('/gallery/<string:gallery_id>/detail/')
def gallery_detail(gallery_id):
    """
    View a gallery with associated images.
    """
    id_token = request.cookies.get("token")
    data={}

    try:
        # verify token
        claims = google.oauth2.id_token.verify_firebase_token(
            id_token, firebase_request_adapter)

        # get user id, gallery key and gallery entity
        user_id = claims['user_id']
        gallery_key = datastore_client.key('User', user_id, 'Gallery', int(gallery_id))
        gallery_entity = datastore_client.get(key=gallery_key)

        # Query images associated with the given gallery_id
        query = datastore_client.query(kind='Image')
        query.add_filter('gallery_id', '=', gallery_id)
        images = list(query.fetch())

        data = {
            "gallery": dict(gallery_entity),
            "gallery_id": gallery_id,
            "images": images,
        }

        return render_template('gallery-detail.html', data=data)

    except ValueError as exc:
        error_message = str(exc)
        print(f"AN ERROR OCCURED {error_message}")
        data={"error_message":error_message}
        flash(error_message)
    
    return render_template("index.html", data={})
    

@app.route('/gallery/add/', methods=["POST"])
def gallery_add():
    """
    Add a new gallery.
    """
    id_token = request.cookies.get("token")
    data={}

    try:
        # verify token
        claims = google.oauth2.id_token.verify_firebase_token(
            id_token, firebase_request_adapter)

        # get user id, gallery key and gallery entity
        user_id = claims['user_id']
        gallery_key = datastore_client.key('User', user_id, 'Gallery')
        entity = datastore.Entity(key=gallery_key)
        
        entity['title'] = request.form.get('title')
        entity['description'] = request.form.get('description')
        entity['created_at'] = datetime.now()
        entity['updated_at'] = datetime.now()
        datastore_client.put(entity)

        return redirect("/")


    except ValueError as exc:
        error_message = str(exc)
        data = {"error_message":error_message}
        print(f"AN ERROR OCCURED {error_message}")
        flash(error_message)

    return render_template("index.html", data=data)
    

@app.route('/gallery/<string:gallery_id>/edit/')
def gallery_edit(gallery_id):

    id_token = request.cookies.get("token")
    data={}

    try:
        # verify token
        claims = google.oauth2.id_token.verify_firebase_token(
            id_token, firebase_request_adapter)

        # get user id, key and entity
        user_id = claims['user_id']

        # logic
        gallery_key = datastore_client.key('User', user_id, 'Gallery', int(gallery_id))
        gallery_entity = datastore_client.get(key=gallery_key)
        
        data={
            "gallery": dict(gallery_entity),
            "gallery_id": gallery_id}
        
        return render_template('gallery-edit.html', data=data)

        
    except ValueError as exc:
        error_message = str(exc)
        print(f"AN ERROR OCCURED {error_message}")
        data={"error_message":error_message}
        flash(error_message)

    
    return render_template("index.html", data=data)


@app.route("/gallery/<string:gallery_id>/update/", methods=['POST'])
def gallery_update(gallery_id):
    """
    Update a gallery.
    """

    id_token = request.cookies.get("token")
    data={}

    try:
        # verify token
        claims = google.oauth2.id_token.verify_firebase_token(
            id_token, firebase_request_adapter)

        # get user id, key and entity
        user_id = claims['user_id']

        # logic
        gallery_key = datastore_client.key('User', user_id, 'Gallery', int(gallery_id))    
        gallery_entity = datastore_client.get(key=gallery_key)
        gallery_entity['title'] = request.form.get('title')
        gallery_entity['description'] = request.form.get('description')
        datastore_client.put(gallery_entity)
        return redirect("/")

        
    except ValueError as exc:
        error_message = str(exc)
        print(f"AN ERROR OCCURED {error_message}")
        data={"error_message":error_message}
        flash(error_message)

    return render_template("index.html", data=data)


@app.route("/gallery/<string:gallery_id>/delete/")
def delete_gallery(gallery_id):
    """
    Delete a gallery.
    """
    id_token = request.cookies.get("token")
    data={}

    try:
        # verify token
        claims = google.oauth2.id_token.verify_firebase_token(
            id_token, firebase_request_adapter)

        # get user id, key and entity
        user_id = claims['user_id']

        # logic
        gallery_key = datastore_client.key('User', user_id, 'Gallery', int(gallery_id))    
        gallery_entity = datastore_client.get(key=gallery_key)
        datastore_client.delete(gallery_key)
        return redirect("/")
        
    except ValueError as exc:
        error_message = str(exc)
        print(f"AN ERROR OCCURED {error_message}")
        data={"error_message":error_message}
        flash(error_message)

    return render_template("index.html", data=data)


# Image Routes

app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def calculate_image_hash(image):
    """
    Calculate the MD5 hash of the image content.
    """
    hasher = hashlib.md5()  # or hashlib.sha1() for SHA1 hash
    for chunk in iter(lambda: image.read(4096), b""):
        hasher.update(chunk)
    return hasher.hexdigest()


@app.route('/image/add/', methods=['POST'])
def image_add():
    """
    Add a new image and check for duplicates.
    """
    id_token = request.cookies.get("token")
    data={}

    try:
        # verify token
        claims = google.oauth2.id_token.verify_firebase_token(
            id_token, firebase_request_adapter)

        # get user id, key and entity
        user_id = claims['user_id']
        file = request.files['file_name']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            gallery_id = request.form.get('gallery_id')

            # Calculate the hash of the new image
            new_image_hash = calculate_image_hash(file)

            # Check for duplicates using the hash in Datastore
            query = datastore_client.query(kind='Image')
            query.add_filter('gallery_id', '=', gallery_id)
            query.add_filter('image_hash', '=', new_image_hash)
            duplicate_images = list(query.fetch())

            if duplicate_images:
                flash('Upload failed. Duplicate image detected')
                error_message = 'Upload failed. Duplicate image detected'
                data = {
                    "error_message":error_message
                }
                return redirect(f'/gallery/{gallery_id}/detail/')

            file.seek(0)

            blob = bucket.blob(filename)
            blob.upload_from_file(file)
            blob.make_public()
            image_url = blob.public_url

            image_key = datastore_client.key('User', user_id, 'Image')
            entity = datastore.Entity(key=image_key)
            entity['url'] = image_url
            entity['gallery_id'] = gallery_id
            entity['image_hash'] = new_image_hash
            entity['created_at'] = datetime.now()
            entity['updated_at'] = datetime.now()
            datastore_client.put(entity)

            return redirect(f'/gallery/{gallery_id}/detail/')

    except ValueError as exc:
        error_message = str(exc)
        print(f"AN ERROR OCCURED {error_message}")
        data={"error_message":error_message}
        flash(error_message)

    return render_template("index.html", data=data)


@app.route("/gallery/<string:gallery_id>/image/<string:image_id>/delete/")
def delete_image(gallery_id, image_id):
    """
    Delete an image.
    """
    data={}

    id_token = request.cookies.get("token")

    try:
        # verify token
        claims = google.oauth2.id_token.verify_firebase_token(
            id_token, firebase_request_adapter)

        # get user id, key and entity
        user_id = claims['user_id']

        # logic
        image_key = datastore_client.key('User', user_id, 'Image', int(image_id))  
        image_entity = datastore_client.get(key=image_key)
        datastore_client.delete(image_key)
        return redirect(f"/gallery/{gallery_id}/detail/")

    except ValueError as exc:
        error_message = str(exc)
        print(f"AN ERROR OCCURED {error_message}")
        data={"error_message":error_message}
        flash(error_message)

    return render_template("index.html", data=data)

@app.route('/image/duplicates/')
def image_duplicates():
    """
    View all duplicate images across galleries.
    """

    id_token = request.cookies.get("token")
    data={}

    try:
        # verify token
        claims = google.oauth2.id_token.verify_firebase_token(
            id_token, firebase_request_adapter)

        # get user id, key and entity
        user_id = claims['user_id']

        # logic

        ancestor_key = datastore_client.key('User', user_id)
        query = datastore_client.query(kind='Image', ancestor=ancestor_key)
        images = list(query.fetch())

        # Group images by their image_hash
        image_hash_groups = defaultdict(list)
        for image in images:
            image_hash_groups[image['image_hash']].append(image)

        # Filter out non-duplicate image groups
        duplicate_image_groups = {hash_key: image_group for hash_key, image_group in image_hash_groups.items() if len(image_group) > 1}

        # Prepare data for the template
        data = {"duplicate_image_groups": duplicate_image_groups}

        print(f"Duplicate Image Groups: {duplicate_image_groups}")
        flash("Duplicate images from all your galleries.")

        return render_template('image-duplicates.html', data=data)

        
    except ValueError as exc:
        error_message = str(exc)
        print(f"AN ERROR OCCURED {error_message}")
        data={"error_message":error_message}

    return render_template("index.html", data=data)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
