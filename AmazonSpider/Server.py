#%%
import pymongo
from loguru import logger
from Config.settings import DATABASE

class DBMongo(object):
    
    def __init__(self, database=DATABASE['db']):
        self.address = DATABASE['host'] + ":" + DATABASE['port']

        self.user = DATABASE['username']
        password = DATABASE['password']
        self.source = DATABASE['source']
        if self.user and password:
            self.client = pymongo.MongoClient( 
                f'mongodb://{self.user}:{password}@{self.address}/?authSource={self.source}'
            )
        else:
            self.client = pymongo.MongoClient( 
                f'mongodb://{self.address}/'
            )


        self.db = self.client[database]

        print(f"Establishing connection to {self.address}...")

        try:
            self.client.server_info()
            print("Connection has established")
        except pymongo.errors.ServerSelectionTimeoutError as err:
            print("Target server has gone away")
    
    def insert(self, table, listItem):
        try:
            self.db[table].insert_many(listItem, ordered=False)
        except pymongo.errors.BulkWriteError as e:
            logger.info(e)
            #pass
        return

    def insert_one(self, table, item):
        self.db[table].insert_one(item)
        return

    def exists(self, table, id):
        if self.db[table].count_documents( {'_id':id}, limit = 1 ) >= 1:
            return True
        else:
            return False

    def colExists(self, col):
        return col in self.db.list_collection_names()

    def count(self, table):
        return self.db[table].count()

    def delete(self, table, id):
        self.db[table].delete_one({'_id':id})

    def getAll(self, table, filter={}, column={}):
        return list(self.db[table].find(filter, column) )

    def getOne(self, table, id):
        return self.db[table].find_one({"_id":id})

    def update(self, table, id, new_item):
        self.db[table].update_one(
            { "_id":id },
            { "$set": new_item }
        )
    
    def updateMany(self, table, new_value):
        self.db[table].update_many({}, new_value)



# %%
