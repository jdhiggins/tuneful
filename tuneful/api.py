import os.path
import json

from flask import request, Response, url_for, send_from_directory
from werkzeug.utils import secure_filename
from jsonschema import validate, ValidationError

import models
import decorators
from tuneful import app
from database import session
from utils import upload_path


@app.route("/api/songs", methods=["GET"])
@decorators.accept("application/json")
def songs_get():
    """Get a list of songs """
    
    # Get the songs from the database
    songs = session.query(models.Song).all()
    
    # Convert the posts to JSON and return a response
    data = json.dumps([song.as_dictionary() for song in songs])
    return Response(data, 200, mimetype="application/json")

@app.route("/api/songs", methods=["POST"])
@decorators.accept("application/json")
@decorators.require("application/json")
def songs_post():
    """ Post a new song """
    data = request.json

    # Add the file to the database
    song = models.Song()
    file = models.File(id=data["file"]["id"])
    
    file.owner = song
    
    
    session.add(file)
    session.add(song)
    session.commit()
    
    # Return a 201 Created, containing the post as JSON and with the
    # Location header set to the location of the post
    
    data = json.dumps(song.as_dictionary())
    headers = {"Location": url_for("songs_get")}
    return Response(data, 201, headers=headers,
                   mimetype="application/json")

@app.route("/api/songs/<int:id>", methods=["DELETE"])
@decorators.accept("application/json")
def song_delete(id):

        #Delete the post from the database
        song = session.query(models.Song).get(id)
        file = song.file

    
        #Check whether the post exists
        #If not return 404 with a helpful message
        if not song:
            message = "Could not find song with id {}".format(id)
            data = json.dumps({"message": message})
            return Response(data, 404, mimetype="application/json")
    
        session.delete(song)
        session.delete(file)
        session.commit()
        
        songs = session.query(models.Song).all()
    
        #return the remaining posts as JSON
        #could choose to return data as empty by doing a query on the deleted post id
        data = json.dumps([song.as_dictionary() for song in songs])
        return Response(data, 200, mimetype="application/json")
    
@app.route("/api/songs/<int:id>", methods=["PUT"])
@decorators.accept("application/json")
def song_edit(id):
    """ Edit an existing post """
    data = request.json
    
    # Check that the JSON supplied is valid
    # If not you return a 422 Unprocessable Entity
#    try:
#        validate(data, post_schema)
#    except ValidationError as error:
#        data = {"message": error.message}
#        return Response(json.dumps(data), 422, mimetype="application/json")
    
    # Get the post from the database
    song = session.query(models.Song).get(id)
    file = song.file
    
    # Edit the post in the database
    file.name = data["name"]
    session.commit()

    # Return a 201 Created, containing the post as JSON and with the
    # Location header set to the location of the post
    data = json.dumps(song.as_dictionary())
    headers = {"Location": url_for("songs_get")}
    return Response(data, 201, headers=headers,
                    mimetype="application/json")

@app.route("/uploads/<filename>", methods=["GET"])
def uploaded_file(filename):
    return send_from_directory(upload_path(), filename)

@app.route("/api/files", methods=["POST"])
@decorators.require("multipart/form-data")
@decorators.accept("application/json")
def file_post():
    file = request.files.get("file")
    if not file:
        data = {"message": "Could not find file data"}
        return Response(json.dumps(data), 422, mimetype="application/json")
    
    filename = secure_filename(file.name)
    db_file = models.File(name=filename)
    session.add(db_file)
    session.commit()
    file.save(upload_path(filename))
    
    data = db_file.as_dictionary()
    return Response(json.dumps(data), 201, mimetype="application/json")

    
    


