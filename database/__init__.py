import datetime, pymongo
from bson.objectid import ObjectId
# from Crypto.Cipher import AES

from database.mysql_db import MySQLDatabase

"""
START MONGO DAEMON INSTANCE - "C:\Program Files\MongoDB\Server\3.4\bin\mongod.exe"
START MONGO CLI APP - "C:\Program Files\MongoDB\Server\3.4\bin\mongo.exe"
"""
MONGO_URI = "mongodb://localhost:27017/"
DATABASE = {
    'name': "ugcs",
    'categories': ["All"],
    'collections': []  # "Examination" (MAKE THIS ARRAY EMPTY SO NO REMNANT COLLECTIONS ARE CREATED WITHIN THE DATABASE
}
COLLECTION = "Collection"


class Database:
    db, encryption = None, None
    default_filter = None
    default_collection = "New Collection"
    default_filename = "New File"
    default_category = "All"
    default_file_type = "xlsx"

    def __init__(self):
        self.encryption = self.Encryption()

    def setup_db(self, app):
        name = DATABASE['name']
        app.config["MONGO_URI"] = MONGO_URI
        mongoclient = pymongo.MongoClient(MONGO_URI)
        dblist = mongoclient.list_database_names()
        print("DATABASES -> {}".format(dblist))
        self.db = mongoclient[name]
        self.test_db()
        return app

    def test_db(self):
        #   FIRST, DELETE ALL COLLECTIONS WITHIN THE DATABASE
        print("FIRST, DELETING ALL THE OTHER COLLECTIONS")
        for collection in self.db.list_collection_names():
            print("Clearing Database Collection '{}'".format(self.db[collection].remove()))
            self.db[collection].drop()
        # THEN, CREATE THE MAIN 'Collection' COLLECTION
        print("NOW, CREATING THE 'Collection' COLLECTION".format(self.db[COLLECTION]))
        # THEN, TEST THE DATABASE CRUD OPERATIONS
        category, obj1, obj2, obj3 = "All", {"hello": "world1"}, {"hello": "world2"}, {"hello": "world3"}
        for collection in DATABASE["collections"]:
            if self.validate_collection({'filename': '', 'collection': collection, 'category': category}):
                print("Creating Database Collection '{}' -> {}".format(collection, self.db[collection]))
                print("Now, Clearing Database Collection '{}' -> {} item(s)".format(self.db[collection].remove(),
                                                                                    self.db[collection].find().count()))
                # obj["hello"] = self.encryption.encrypt(obj["hello"])
                print(self.db[collection].insert([obj1, obj2, obj3]))
                print(self.db[collection].find().count())
                print("DONE SAVING DATA, NOW GETTING IT ALL BACK")
                cursor, data = self.db[collection].find(), []
                for o in cursor:
                    print()
                    print(o)
                    # if "hello" in o:
                    #     print("NOW, DECRYPTING DATA")
                    #     o["hello"] = self.encryption.decrypt(o["hello"])
                    #     print(o)
                    data.append(o)
                print()
                print("DONE DECRYTING ALL DATA")
                print("{} item(s) -> {}".format(len(data), data))
                print("Done testing, Clearing Database Collection '{}' again -> {} item(s)"
                      .format(self.db[collection].remove(), self.db[collection].find().count()))
                print()

    def validate_collection(self, extra):
        def create_new_collection(col, file, cat):
            obj = {'collection': col, 'filename': file, 'categories': ["All"]}
            if cat not in obj["categories"]:
                print("Appending new category '{}' to collection '{}'".format(cat, col))
                obj["categores"].append(cat)
            print("New Collection Object -> {}".format(obj))
            return obj

        # THESE 3 SHOULD NEVER RAISE ANY EXCEPTIONS, BUT JUST IN CASE :)
        if (extra is not None) and ("collection" in extra):
            collection = extra["collection"]
            filename = extra["filename"] if ("filename" in extra) else self.default_filename
            category = extra["category"] if ("category" in extra) else self.default_category
            #
            print("NOW, VALIDATING COLLECTION '{}'".format(collection))
            # CHECK IF collection ALREADY EXISTS WITHIN THE DB, IF NOT, THEN ADD IT
            if category in DATABASE["categories"]:
                if collection not in self.db.list_collection_names():
                    print("CREATING NEW COLLECTION -> {}".format(self.db[collection]))
                    self.db[COLLECTION].insert(create_new_collection(collection, filename, category), check_keys=False)
                    print("Done testing, Clearing Database Collection '{}' again -> {} item(s)"
                          .format(self.db[collection].remove(), self.db[collection].find().count()))
                else:
                    print("NO NEED TO VALIDATE, COLLECTION '{}' ALREADY EXISTS".format(collection))
                print("FINALLY, DONE WITH VALIDATION OF COLLECTION '{}'".format(collection))
                return collection
            print("SORRY, THIS CATEGORY '{}' IS NOT ALLOWED :(".format(category))
        else:
            print("SORRY, THERE IS NO COLLECTION TO VALIDATE :(")
        return None

    def get_collections(self, category=default_category):
        print("GETTING COLLECTIONS WITHIN CATEGORY '{}'".format(category))
        # data = self.db[COLLECTION].find()  # THESE 2 CAN BOTH WORK
        # data = [x for x in data if (category in x["categories"])]
        cursor, data = self.db[COLLECTION].find({'categories': category}), []
        for o in cursor:
            if "_id" in o:
                print("CONVERTING OBJECT-ID TO STRING -> {}".format(o["_id"]))
                o["_id"] = str(o["_id"])
            data.append(o)
        print("{} COLLECTION(S) -> {}".format(len(data), data))
        return data

    def delete_collection(self, extra):
        if '_id' in extra:
            filter = {'_id': ObjectId(extra["_id"])}
            collection_obj = self.db[COLLECTION].find_one(filter)
            print("COLLECTION OBJECT TO BE DELETED -> {}".format(collection_obj))
            if self.db[COLLECTION].delete_many(filter).deleted_count > 0:
                print("DELETED COLLECTION OBJECT -> {} OBJECT(S) LEFT".format(self.db[COLLECTION].find().count()))
                if 'collection' in collection_obj:
                    collection = collection_obj["collection"]
                    print("Now, Clearing Database Collection '{}' -> {} item(s)".format(self.db[collection].remove(),
                                                                                        self.db[
                                                                                            collection].find().count()))
                    print("DELETING COLLECTION '{}' -> {}".format(collection, extra["_id"]))
                    self.db[collection].drop()
                    return True
                print("SORRY, COULD NOT DELETE THE COLLECTION ITSELF")
            print("SORRY, COULD NOT DELETE THE COLLECTION OBJECT")
        else:
            print("NO OBJECT-ID AVAILABLE")
        return False

    def get_data(self, filter=None, extra=None):
        collection = self.validate_collection(extra)
        if collection is not None:
            filter = None if (filter == "all") else filter  # DO THIS, IN CASE filter = "all"
            cursor, data = self.db[collection].find(filter if (filter is not None) else {}), []
            i = 0
            for o in cursor:
                print(i)
                print(o)
                o = self.serialize_to("dict", o)
                data.append(o)
                i += 1
            print()
            print("DONE RETRIEVING AND DECRYPTING ALL DATA")
            print("{} item(s) -> {}".format(len(data), data))
            return data
        return None

    def save_data_object(self, obj, extra=None):
        collection = self.validate_collection(extra)
        if collection is not None:
            obj = self.serialize_to("mongodb", obj)
            print("OBJECT {} -> {}".format(type(obj), obj))
            # NOW, YOU CAN SAVE THE DATA OBJECT
            self.db[collection].insert(obj, check_keys=False)
            # COZ YOU'RE LETTING MONGO-DB ALLOW '.' & '$' WITHIN YOUR KEYS, IT MIGHT HAVE SOME ISSUES
            # ISSUES WHEN YOU'RE USING A FILTER WITH .find({'key.prop':'value'}) TO ACCESS INNER DOCUMENTS
            return True
        return False

    def serialize_to(self, param, obj):
        if param == "mongodb":  # 1ST, TRY TO DO SOME FURTHER PREPROCESSING (eg. CONVERT datetime.time OBJECTS INTO STRINGS)
            print("Serializing from Dictionary to Mongo-DB object")
            if 'pin' in obj:
                print("NOW, ENCRYPTING PIN -> {}".format(obj['pin']))
                obj['pin'] = self.encryption.encrypt(obj['pin'])
            for key in obj:
                if type(obj[key]) is datetime.time:
                    obj[key] = obj[key].strftime("%H:%M:%S")
        elif param == "dict":
            print("Serializing from Mongo-DB to Dictionary object")
            if 'pin' in obj:
                print("NOW, DECYPTING PIN -> {}".format(obj['pin']))
                obj['pin'] = self.encryption.decrypt(obj['pin'])
            for key in obj:
                pass
                # FIND A WAY TO CONVERT "TIME STRING" BACK TO A datetime.time OBJECT
                # if type(obj[key]) is datetime.time:
                #     obj[key] = obj[key].strftime("%H:%M:%S")
        else:
            print("Incorrect parameter value")
        print("SERIALIZED OBJECT -> {}".format(obj))
        return obj

    class Encryption:
        key, nonce = "", None

        def __init__(self, key="DEFAULT KEY COMES HERE"):
            self.key = key
            self.nonce = None

        def encrypt(self, text):  # FIND OUT THE KEY YOU'RE USING TO ENCRYPT THE PINS
            # self.cipher = AES.new(self.key, AES.MODE_EAX)
            # self.nonce = self.cipher.nonce
            # ciphertext, self.tag = self.cipher.encrypt_and_digest(text)
            # return ciphertext
            pass

        def decrypt(self, ciphertext):
            # try:
            #     self.cipher = AES.new(self.key, AES.MODE_EAX, nonce=self.nonce)
            #     plaintext = self.cipher.decrypt(ciphertext)
            #     self.cipher.verify(self.tag)
            #     print("The message is authentic:", plaintext)
            #     return plaintext
            # except ValueError:
            #     print("Key incorrect or message corrupted")
            #     print("Returning Ciphertext back")
            # return ciphertext
            pass
