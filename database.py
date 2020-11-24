from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv
import os

load_dotenv()


class DatabaseConnection:
    def __init__(self):
        client = MongoClient(port=int(3000), username=os.getenv('USERNAME'),
                             password=os.getenv("PASSWORD"))
        self.db = client.application
        self.db.users.create_index([("username", ASCENDING), ("email", ASCENDING)], unique=True)

    def get_all_data(self):
        return self.db.users.find({}, {"_id": 0})

    def create_user(self, user):
        self.db.users.insert_one(user)

    def get_user(self, query):
        return self.db.users.find_one(query)

    def update_user(self, old_user, new_user):
        self.db.users.replace_one(old_user, new_user)
