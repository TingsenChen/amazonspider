from .Server import DBMongo
import time
import sys
import itertools
import threading

class Reader():

    def __init__(self, collection):
        self.db = DBMongo()
        self.loader = Loader()
        self.collection = collection

        self.loader.start("Fetching data from database...")
        self.ids = self.db.getAll('data', column={"_id":1})
        self.total = len(self.ids)
        self.loader.end("Done\n")


    def all(self):
        time.sleep(0.5)
        for id in self.ids:
            target = self.db.getOne(self.collection, id["_id"])
            if target:
                yield target

    def update(self, col, id, values):
        self.db.update(col, id, values)

class Loader():

    done = False

    def __animate(self, message):
        for c in itertools.cycle(['|', '/', '-', '\\']):
            if self.done:
                break
            sys.stdout.write(f'\r{message} ' + c)
            sys.stdout.flush()
            time.sleep(0.1)
        
    def start(self, message):
        threading.Thread(target=self.__animate, args=(message,)).start()

    def end(self, complete):
        self.done = True
        sys.stdout.write(f'\r{complete}                         \n')
