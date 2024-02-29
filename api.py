from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
from pathlib import Path
import threading
import uuid
import json
import time

def encrypt(key: str, value: dict) -> str:
    return Fernet(key).encrypt(json.dumps(value).encode())

def decrypt(key: str, value: str) -> dict: 
    return json.loads(Fernet(key).decrypt(value).decode())

def dynamic_if(field, operation, field_value):
    if operation == "==":
        return True if field == field_value else False
    elif operation == "!=":
        return True if field != field_value else False
    elif operation == ">=":
        return True if field >= field_value else False
    elif operation == "<=":
        return True if field <= field_value else False
    elif operation == ">":
        return True if field > field_value else False
    elif operation == "<":
        return True if field < field_value else False
    else:
        return False


class Montybase:
    def __init__(self, path: Path = Path(Path(__file__).parent, "db.json"), name: str = "db"):
        self.path = path
        if path:
            with open(path, "r") as f:
                self.data = json.loads(f.read())
        else:
            self.data = {}
        self.name = name

    def __str__(self):
        return self.name


class MontybaseAPI:
    def __init__(self, name: str = Path(__file__).name[:3], db_path: str = "db.json", updateTime: int = 180, storeMin: int = 10):
        self.app = Flask(__name__)

        db_config = Path(Path(__file__).parent, "db-config.json")
        if db_config.is_file():
            with open(db_config, "r") as f:
                self.setup = json.loads(f.read())
        else:
            self.setup_db(name, db_path, updateTime, storeMin)

        client_config = Path(Path(__file__).parent, "client-config.json")
        if not client_config.is_file():
            self.setup_client()

        self.encryption_key = self.setup["apiKey"][len(self.setup["projectName"])+1:]
        self.storageUpdateCount = 0
        self.saveTimer = False

        self.db = Montybase(self.setup["storageBucket"], name=self.setup["projectName"])
        self.setup_routes()

    def setup_db(self, name: str, db_path: str, updateTime: int, storeMin: int):

        self.setup = {
            "projectName": name,
            "apiKey": name + "-" + Fernet.generate_key().decode(),
            "storageBucket": db_path,
            "storageUpdate": updateTime,
            "storageMinCount": storeMin
        }

        with open("api-config.json", "w") as f:
            f.write(json.dumps(self.setup))

        with open(self.setup["storageBucket"], "w") as f:
            f.write("{}")

        self.setup_client()

    def setup_client(self):

        setup = {
            "projectName": self.setup["projectName"],
            "apiKey": self.setup["apiKey"]
        }

        with open("client-config.json", "w") as f:
            f.write(json.dumps(setup))

    def setup_routes(self):
        self.app.route("/add_doc", methods=["POST"])(self.add_doc)
        self.app.route("/set_doc", methods=["POST"])(self.set_doc)
        self.app.route("/update_doc", methods=["POST"])(self.update_doc)
        self.app.route("/get_doc", methods=["POST"])(self.get_doc)

    def auth_request(self):
        apikey = request.headers.get("apiKey")
        if apikey:
            if apikey != self.setup["apiKey"]: 
                return False, {"data": "Access denied. Incorrect API Key."}, 403
        else: 
            return False, {"data": "Access denied. Missing API Key."}, 400
        return True, None, 200
    
    def startSaveTimer(self):
        self.saveTimer = True
        time.sleep(self.setup["storageUpdate"]) 

        with open(self.db.path, "w") as f:
            f.write(json.dumps(self.db.data))

        self.storageUpdateCount = 0
        self.saveTimer = False


    def add_doc(self):
        access, response, status = self.auth_request()
        if not access:
            return jsonify(response), status

        data = decrypt(self.encryption_key, request.get_data())

        reference = data["ref"]
        value = data["value"]
        current_dict = self.db.data

        for key in reference[:-1]:
            current_dict = current_dict.setdefault(key, {})

        if "id" in data: uid = data["id"]
        else: uid = str(uuid.uuid4())
        current_dict[reference[-1]][uid] = value

        # save on long-term db
        self.storageUpdateCount += 1
        if not self.saveTimer and self.storageUpdateCount >= self.setup["storageMinCount"]:
            threading.Thread(target=self.startSaveTimer).start()

        response = {"data": uid}
        return encrypt(self.encryption_key, json.dumps(response))

    def set_doc(self):
        access, response, status = self.auth_request()
        if not access:
            return jsonify(response), status
    
        data = decrypt(self.encryption_key, request.get_data())

        reference = data["ref"]
        value = data["value"]
        current_dict = self.db.data

        for key in reference[:-1]:
            current_dict = current_dict.setdefault(key, {})

        if "id" in data: uid = data["id"]
        else: uid = str(uuid.uuid4())
        current_dict[reference[-1]] = {uid: value}

        # save on long-term db
        self.storageUpdateCount += 1
        if not self.saveTimer and self.storageUpdateCount >= self.setup["storageMinCount"]:
            threading.Thread(target=self.startSaveTimer).start()

        response = {"data": uid}
        return encrypt(self.encryption_key, json.dumps(response))

    def update_doc(self):
        access, response, status = self.auth_request()
        if not access:
            return jsonify(response), status
    
        data = decrypt(self.encryption_key, request.get_data())
        headers = request.headers.get("User")

        reference = data["ref"]
        value = data["value"]
        current_dict = self.db.data

        for key in reference[:-1]:
            current_dict = current_dict.setdefault(key, {})

        current_dict[reference[-1]] = {**current_dict[reference[-1]], **value}

        # save on long-term db
        self.storageUpdateCount += 1
        if not self.saveTimer and self.storageUpdateCount >= self.setup["storageMinCount"]:
            threading.Thread(target=self.startSaveTimer).start()

        response = {"data": True}
        return encrypt(self.encryption_key, json.dumps(response))

    def get_doc(self):
        access, response, status = self.auth_request()
        if not access:
            return jsonify(response), status
    
        data = decrypt(self.encryption_key, request.get_data())
        headers = request.headers.get("User")

        reference = data["ref"]
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

        return encrypt(self.encryption_key, json.dumps(response))

    def run(self):
        self.app.run(debug=True)
