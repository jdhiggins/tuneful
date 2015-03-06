import unittest
import os
import shutil
import json
from urlparse import urlparse
from StringIO import StringIO

import sys; print sys.modules.keys()
# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "tuneful.config.TestingConfig"

from tuneful import app
from tuneful import models
from tuneful.utils import upload_path
from tuneful.database import Base, engine, session

class TestAPI(unittest.TestCase):
    """ Tests for the tuneful API """

    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

        # Set up the tables in the database
        Base.metadata.create_all(engine)

        # Create folder for test uploads
        os.mkdir(upload_path())
        
    def testGetEmptySongs(self):
        """ Getting songs from an empty database """
        response = self.client.get("/api/songs",
            headers=[("Accept", "application/json")]
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        
        data = json.loads(response.data)
        self.assertEqual(data,[])
        
    def testGetPosts(self):
        """Getting posts from a populated database"""
        songA = models.Song()
        songB = models.Song()
        songC = models.Song()

        fileA = models.File(name="Test Name A")
        fileB = models.File(name="Test Name B")
        fileC = models.File(name="Test Name C")
        
        fileA.owner = songA
        fileB.owner = songB
        fileC.owner = songC
        
        session.add_all([songA, songB, songC, fileA, fileB, fileC])
        session.commit()
        
        response = self.client.get("/api/songs",
            headers=[("Accept", "application/json")]
        )
                       
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        
        data = json.loads(response.data)
        self.assertEqual(len(data), 3)
                              
        songA = data[0]
        self.assertEqual(songA["file"]["name"], "Test Name A")
                
        songB = data[1]
        self.assertEqual(songB["file"]["name"], "Test Name B")
        
        songC = data[2]
        self.assertEqual(songC["file"]["name"], "Test Name C")

    def testPostSong(self):
        """Posting a new song"""
        data = {
            "file": {
                "id": 7
            }
        }
        
        response = self.client.post("/api/songs",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")])
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(urlparse(response.headers.get("Location")).path,
                        "/api/songs")
        
        data = json.loads(response.data)
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["file"]["id"], 7)
        
        songs = session.query(models.Song).all()
        self.assertEqual(len(songs), 1)
        
        song = songs[0]
        self.assertEqual(song.file.id, 7)
        
        
    def testUnsupportedAcceptHeader(self):
        response = self.client.get("/api/songs",
            headers=[("Accept", "application/xml")]
        )
        
        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.mimetype, "application/json")
        
        data = json.loads(response.data)
        self.assertEqual(data["message"],
                        "Request must accept application/json data")
        
    def testUnsupportedMimetype(self):
        data = "<xml></xml>"
        response = self.client.post("/api/songs",
            data = json.dumps(data),
            content_type="application/xml",
            headers=[("Accept", "application/json")]
        )
        
        self.assertEqual(response.status_code, 415)
        self.assertEqual(response.mimetype, "application/json")
        
        data = json.loads(response.data)
        self.assertEqual(data["message"],
                        "Request must contain application/json data")
        
    def testDeleteSong(self):
        """Deleting song from a populated database"""
        #First populate database
        songA = models.Song()
        songB = models.Song()
        songC = models.Song()

        fileA = models.File(name="Test Name A")
        fileB = models.File(name="Test Name B")
        fileC = models.File(name="Test Name C")
        
        fileA.owner = songA
        fileB.owner = songB
        fileC.owner = songC
        
        session.add_all([songA, songB, songC, fileA, fileB, fileC])
        session.commit()
        
        response = self.client.delete("/api/songs/3",
            headers=[("Accept", "application/json")]
        )
                       
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)
                              
        songA = data[0]
        self.assertEqual(songA["file"]["name"], "Test Name A")
                
        songB = data[1]
        self.assertEqual(songB["file"]["name"], "Test Name B")
    
    def testEditSong(self):
        """Edit song from a populated database"""
        #First populate database
        songA = models.Song()
        songB = models.Song()
        songC = models.Song()

        fileA = models.File(name="Test Name A")
        fileB = models.File(name="Test Name B")
        fileC = models.File(name="Test Name C")
        
        fileA.owner = songA
        fileB.owner = songB
        fileC.owner = songC
        
        session.add_all([songA, songB, songC, fileA, fileB, fileC])
        session.commit()
        
        data = {
            "name": "An Edited Test Name"
        }
        
        response = self.client.put("/api/songs/{}".format(songC.id),
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
        )
                       
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(data["file"]["name"], "An Edited Test Name")

        songs = session.query(models.Song).all()
        self.assertEqual(len(songs), 3)
                              
        songC = songs[2]
        self.assertEqual(songC.file.name, "An Edited Test Name")

    def test_get_uploaded_file(self):
        path = upload_path("test.txt")
        with open(path, "w") as f:
            f.write("File contents")
            
        response = self.client.get("/uploads/test.txt")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/plain")
        self.assertEqual(response.data, "File contents")
    
    def test_file_upload(self):
        data = {
            "file": (StringIO("File contents"), "test.txt")
        }
    
        response = self.client.post("/api/files",
            data=data,
            content_type="multipart/form-data",
            headers=[("Accept", "application/json")]
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")
        
        data = json.loads(response.data)
        self.assertEqual(urlparse(data["path"]).path, "/uploads/test.txt")
        
        path = upload_path("test.txt")
        self.assertTrue(os.path.isfile(path))
        with open(path) as f:
            contents =f.read()
        self.assertEqual(contents, "File contents")
                        
        
    def tearDown(self):
        """ Test teardown """
        session.close()
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)

        # Delete test upload folder
        shutil.rmtree(upload_path())


