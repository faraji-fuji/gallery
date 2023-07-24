from flask import Flask, render_template, request, redirect, session, url_for, jsonify, flash
from werkzeug.utils import secure_filename
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
    return render_template("index.html")

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
    View a gallery with associated images.
    """
    user_id = session.get('user_id')
    gallery_key = datastore_client.key('User', user_id, 'Gallery', int(gallery_id))
    gallery_entity = datastore_client.get(key=gallery_key)

    # Query images associated with the given gallery_id
    query = datastore_client.query(kind='Image')
    query.add_filter('gallery_id', '=', gallery_id)
    images = list(query.fetch())

    print(f"GALLERY ID {gallery_id}")
    print(f"IMAGES {images}")
    
    data = {
        "gallery": dict(gallery_entity),
        "gallery_id": gallery_id,
        "images": images,
    }

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

app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/image/add/', methods=['POST'])
def image_add():
    """
    Add a new image.
    """
    if 'file_name' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file_name']

    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        gallery_id = request.form.get('gallery_id')

        blob = bucket.blob(filename)
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

        flash('File uploaded successfully')

        return redirect(f'/gallery/{gallery_id}/detail/')

    flash('Invalid file format. Only JPG, JPEG, and PNG files are allowed.')
    return redirect(request.url)


@app.route("/gallery/<string:gallery_id>/image/<string:image_id>/delete/")
def delete_image(gallery_id, image_id):
    """
    Delete an image.
    """
    user_id = session.get('user_id')
    image_key = datastore_client.key('Image', int(image_id))  
    image_entity = datastore_client.get(key=image_key)
    datastore_client.delete(image_key)
    return redirect(f"/gallery/{gallery_id}/detail/")
   

@app.route('/logout/', methods=['GET'])
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(host='127.0.0.1', port=8080, debug=True)
