import pymongo

def connect_db(db, username, password):
    myclient = pymongo.MongoClient(f"mongodb://{username}:{password}@localhost:27017/")
    mydb = myclient["jamify"]
    return mydb

def write_to_db(db, audioclip):
    mycol = db["audioclips"]
    x = mycol.insert_one({"filename": audioclip.filename, "path": audioclip.path, "startTime": audioclip.startTime, "size": audioclip.size, "duration": audioclip.duration})
