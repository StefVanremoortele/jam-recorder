import pymongo
import os
from pathlib import Path
from datetime import datetime


class Audioclip():
    def __init__(self, filename, startTime, size ):
        self.filename = filename
        self.startTime = startTime
        self.size = size
         


def connect_db(db, username, password):
    myclient = pymongo.MongoClient(f"mongodb://{username}:{password}@localhost:27017/")
    mydb = myclient["jamify"]
    return mydb

def write_to_db(db):
    mycol = db["audioclips"]
    mydict = { "name": "John", "address": "Highway 37" }
    x = mycol.insert_one(mydict)

def get_file_stats(path):
    return Path(path).stat()


if __name__ == '__main__':
    db = connect_db('jamify', 'stef', 'Pass123')
    write_to_db(db)
    # filepath = '/home/stef/audioclips/2022-04-29/17/20220429-173834.wav'
    # stats = get_file_stats(filepath)
    # print(stats.st_size)
    # print('done')