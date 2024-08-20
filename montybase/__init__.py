import requests
from pathlib import Path
from cryptography.fernet import Fernet
from flask import request, jsonify, Flask
import threading
from nanoid import generate
import time
import json
import os

def encrypt(key: str, value: dict) -> str:
    return Fernet(key).encrypt(json.dumps(value).encode())

def decrypt(key: str, value: str) -> dict: 
    data = json.loads(json.loads(Fernet(key).decrypt(value).decode()))["data"] # quotation marks getting weird lol
    return data 

def dynamic_if(field, operation, field_value):
    if operation == "==":
        return field == field_value
    elif operation == "!=":
        return field != field_value 
    elif operation == ">=":
        return field >= field_value
    elif operation == "<=":
        return field <= field_value
    elif operation == ">":
        return field > field_value
    elif operation == "<":
        return field < field_value
    else:
        return False

class Database:
    def __init__(self, path: Path | None = None, name: str = "db"):
        path = path if path else Path(os.getcwd(), f"{name}-db", "db.json")
        self.path = path
        if path:
            with open(path, "r") as f:
                self.data = json.loads(f.read())
        else:
            self.data = {}
        self.name = name

    def __str__(self):
        return self.name

class Montybase:
    def __init__(self, 
                 name: str = Path(os.getcwd()).name, 
                 db_path: Path | None = None, 
                 updateTime: int = 300, 
                 storeMin: int = 1,
                 endpoint=False,
                 hot=False,
                 id_length=20,
                 dev=False,
                 api = None):
        
        db_path = db_path if db_path else Path(os.getcwd(), f"{name}-db")
        self.endpoint = endpoint
        self.dev = dev
        self.api = api
        
        if dev is True:
            self.endpoint = "127.0.0.1:5000" 
        elif dev:
            self.endpoint = dev
        elif endpoint:
            self.endpoint = "0.0.0.0:5000"
            
        self.name = name
        self.db_path = db_path
        self.hot = hot
        self.id_length = id_length

        if db_path.is_dir():
            with open(Path(db_path, "db.config.json"), "r") as f:
                self.setup = json.loads(f.read())
                
            if self.hot:
                self.setup["storageMinCount"] = 0
                self.setup["storageUpdate"] = 0
        else:
            db_path.mkdir(parents=True, exist_ok=True)
            self.setup_db(name, db_path, updateTime, storeMin)
            
        if endpoint:
            self.setup_client()
            
            self.app = Flask(__file__)
            client_config = Path(db_path, "client.config.json")
            if not client_config.is_file():
                self.setup_client()

            self.encryption_key = self.setup["apiKey"][len(self.setup["projectName"])+1:]
            self.setup_routes()
            
        if self.api:
            with open(Path(db_path, "client.config.json"), "r") as f:
                self.headers = json.loads(f.read())
                self.headers["key"] = self.headers["apiKey"][len(self.headers["projectName"])+1:]
            
        self.storageUpdateCount = 0
        self.saveTimer = False

        self.db = Database(self.setup["storageBucket"], name=self.setup["projectName"])
        
    def __str__(self):
        return f"Montybase(name={self.name})"
    
    def setup_routes(self):
        self.app.route("/add_doc", methods=["POST"])(self.add_doc)
        self.app.route("/set_doc", methods=["POST"])(self.set_doc)
        self.app.route("/update_doc", methods=["POST"])(self.update_doc)
        self.app.route("/get_doc", methods=["POST"])(self.get_doc)

    def setup_db(self, name: str, db_path: str, updateTime: int, storeMin: int):

        self.setup = {
            "projectName": name,
            "apiKey": "mb-" + Fernet.generate_key().decode(),
            "storageBucket": str(Path(db_path, "db.json")),
            "storageUpdate": updateTime,
            "storageMinCount": storeMin
        }
        
        with open(Path(db_path, "db.config.json"), "w") as f:
            f.write(json.dumps(self.setup))
        
        with open(self.setup["storageBucket"], "w") as f:
            f.write("{}")

    def setup_client(self):

        setup = {
            "projectName": self.setup["projectName"],
            "apiKey": self.setup["apiKey"]
        }

        with open(Path(self.db_path, "client.config.json"), "w") as f:
            f.write(json.dumps(setup))

    def startSaveTimer(self):
        self.saveTimer = True
        time.sleep(self.setup["storageUpdate"]) 

        with open(self.db.path, "w") as f:
            f.write(json.dumps(self.db.data))

        self.storageUpdateCount = 0
        self.saveTimer = False
        
    def auth_request(self):
        apikey = request.headers.get("apiKey")
        if apikey:
            if apikey != self.setup["apiKey"]: 
                return False, {"data": "Access denied. Incorrect API Key."}, 403
        else: 
            return False, {"data": "Access denied. Missing API Key."}, 400
        return True, None, 200
    
    def exists(self, data):
        if self.endpoint:
            access, response, status = self.auth_request()
            if not access:
                return jsonify(response), status
            data = decrypt(self.encryption_key, request.get_data())
            
        current_dict = self.db.data
        if (ref := data.get("ref", None)):
            response = {"data": all((current_dict := current_dict.get(key)) for key in ref)}
        return encrypt(self.encryption_key, json.dumps(response)) if self.endpoint else response["data"]
    

    def add_doc(self, data=None):
        if self.endpoint:
            access, response, status = self.auth_request()
            if not access:
                return jsonify(response), status
            data = decrypt(self.encryption_key, request.get_data())

        reference, value, uid = data["ref"], data.get("value", None), data.get("id", generate(size=self.id_length))
        current_dict = self.db.data

        for key in reference[:-1]:
            current_dict = current_dict.setdefault(key, {})
   
        current_dict.setdefault(reference[-1], {})[uid] = value

        # save on long-term db
        self.storageUpdateCount += 1
        if not self.saveTimer and self.storageUpdateCount >= self.setup["storageMinCount"]:
            threading.Thread(target=self.startSaveTimer).start()

        return encrypt(self.encryption_key, json.dumps({"data": uid})) if self.endpoint else uid


    def set_doc(self, data=None):
        if self.endpoint:
            access, response, status = self.auth_request()
            if not access:
                return jsonify(response), status
            data = decrypt(self.encryption_key, request.get_data())

        reference, value, uid = data["ref"], data.get("value", None), data.get("id", generate(size=self.id_length))
        current_dict = self.db.data

        for key in reference[:-1]:
            current_dict = current_dict.setdefault(key, {})
            
        current_dict[reference[-1]] = {uid: value}

        # save on long-term db
        self.storageUpdateCount += 1
        if not self.saveTimer and self.storageUpdateCount >= self.setup["storageMinCount"]:
            threading.Thread(target=self.startSaveTimer).start()

        return encrypt(self.encryption_key, json.dumps({"data": uid})) if self.endpoint else uid

    def update_doc(self, data=None):
        if self.endpoint:
            access, response, status = self.auth_request()
            if not access:
                return jsonify(response), status
            data = decrypt(self.encryption_key, request.get_data())

        reference, value = data["ref"], data["value"]
        current_dict = self.db.data

        for key in reference[:-1]:
            current_dict = current_dict.setdefault(key, {})

        current_dict[reference[-1]] = {**current_dict[reference[-1]], **value}

        # save on long-term db
        self.storageUpdateCount += 1
        if not self.saveTimer and self.storageUpdateCount >= self.setup["storageMinCount"]:
            threading.Thread(target=self.startSaveTimer).start()

        return encrypt(self.encryption_key, json.dumps({"data": True})) if self.endpoint else True
    
    def delete_doc(self, data=None):
        if self.endpoint:
            access, response, status = self.auth_request()
            if not access:
                return jsonify(response), status
            data = decrypt(self.encryption_key, request.get_data())
        
        if (ref := data["ref"] + data.get("value", tuple())):
            current_dict = self.db.data
            for key in ref[:-1]:
                current_dict = current_dict.get(key, {})
            response = {"data": current_dict.pop(ref[-1], None)}
        else:
            response = {"data": {}}
            
        return encrypt(self.encryption_key, json.dumps(response)) if self.endpoint else response["data"]

    def get_doc(self, data=None):
        if self.endpoint:
            access, response, status = self.auth_request()
            if not access:
                return jsonify(response), status
            data = decrypt(self.encryption_key, request.get_data())
        
        if not (reference := data["ref"]):
            return encrypt(self.encryption_key, json.dumps({"data": self.db.data})) if self.endpoint else self.db.data
        current_dict = self.db.data

        try:
            for key in reference[:-1]:
                current_dict = current_dict.setdefault(key, {})
            dict_tree: dict = current_dict[reference[-1]]

            if "value" in data:
                filtered = {}
                field, operation, field_value = tuple(data["value"])

                for key, value in dict_tree.items():
                    if dynamic_if(value[field], operation, field_value):
                        filtered[key] = value
                dict_tree = filtered

            response = {"data": dict_tree}
        except KeyError:
            response = {"data": {}}
        except TypeError:
            response = {"data": {}}

        return encrypt(self.encryption_key, json.dumps(response)) if self.endpoint else response["data"]

    def run(self):
        ip, port = self.endpoint.split(':')
        self.app.run(debug=self.dev, host=ip, port=port)


class Reference:
    def __init__(self, db: Montybase, *args, api: str = None):
        self.db = db
        self.ref = args
        self.api_endpoint = db.api

    def __str__(self):
        ref = ", ".join([f'"{i}"' for i in self.ref])
        return f"doc({self.db.name}, {ref})"
    
    def where(self, key: str, operation: str, value: int | str):
        return FilteredReference(self, condition=(key, operation, value))
    
    def document(self, *args):
        self.ref += args
        return self
    
    def append(self, *args):
        return Reference(self.db, *self.ref, *args)
    
    def fetch(self, endpoint, value: str | int | float | bool | list | dict = None, key: str = None):
        data = {"ref": self.ref} | ({} if value is None else { "value": value }) | ({ "id": key } if key else {})
        if self.api_endpoint:
            url = self.api_endpoint + "/" + endpoint
            headers = {'Content-Type': 'application/json'} | self.db.headers  # Set the correct content type

            response = requests.post(url, data=encrypt(self.db.headers["key"], data), headers=headers)

            if response.status_code != 200: raise requests.HTTPError(decrypt(self.db.headers["key"], response.content.decode()))
            else: return decrypt(self.db.headers["key"], response.content.decode())
        return getattr(self.db, endpoint)(data)
                
    def set(self, value=None, key: str | None = None):
        if key: return self.fetch("set_doc", value, key=key)
        return self.fetch("set_doc", value)
    
    def add(self, value=None, key: str | None = None):
        return self.fetch("add_doc", value, key=key)
    
    def update(self, value, key: str | None = None):
        return self.fetch("update_doc", value, key=key)
    
    def delete(self, value=None, key: str | None = None):
        return self.fetch("delete_doc", value, key=key)
    
    def stream(self) -> list[dict]:
        docs: dict = self.fetch("get_doc")
        return [(key, value) for key, value in docs.items()]
    
    def get(self) -> dict:
        return self.fetch("get_doc")
    
    def exists(self) -> bool:
        return self.fetch("exists")


class FilteredReference(Reference):
    def __init__(self, doc: Reference, condition: tuple):
        super().__init__()
        
        self.db = doc.db
        self.ref = doc.ref
        self.api_endpoint = doc.api_endpoint
        self.condition = condition

    def __str__(self):
        ref = ", ".join([f'"{i}"' for i in self.ref])
        return f"doc({self.db.name}, {ref}).where{self.condition}"
    
    def fetch(self, endpoint, value = None):
        data = {"ref": self.ref, "value": value}
        
        if self.api_endpoint:
            url = self.api_endpoint + "/" + endpoint
            headers = {'Content-Type': 'application/json'} | self.db.headers # Set the correct content type

            response = requests.post(url, data=encrypt(self.db.headers["key"], data), headers=headers)
            
            if response.status_code != 200: raise requests.HTTPError(decrypt(self.db.headers["key"], response.content.decode()))
            else: docs = decrypt(self.db.headers["key"], response.content.decode())
    
        docs = getattr(self.db, endpoint)(data)
        
        if type(docs, dict):
            key, operation, val = self.condition
            docs = [(doc, docs[doc]) 
                    for doc in tuple(docs) 
                    if dynamic_if(docs[doc].get(key, None), operation, val)]
        
        return docs   


    def stream(self) -> list[dict]:
        docs: dict = self.fetch("get_doc")
        return [(key, value) for key, value in docs.items()]
    
    def get(self):
        return self.fetch("get_doc") 
    
    def exists(self) -> bool:
        return bool(self.fetch("get_doc"))

def doc(db: Montybase, *args):
    return Reference(db, *args)

async def addDoc(ref: Reference, value):
    return ref.add(value)

async def setDoc(ref: Reference, value):
    return ref.set(value)

async def updateDoc(ref: Reference, value):
    return ref.update(value)
