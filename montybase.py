import requests
from pathlib import Path
from cryptography.fernet import Fernet
import json

def encrypt(key: str, value: dict) -> str:
    return Fernet(key).encrypt(json.dumps(value).encode())

def decrypt(key: str, value: str) -> dict: 
    data = json.loads(json.loads(Fernet(key).decrypt(value).decode()))["data"] # quotation marks getting weird lol
    return data 

class Montybase:
    def __init__(self, api: str = "http://127.0.0.1:5000", name: str = "db"):
        self.name = name
        self.api = api

        with open(Path(Path(__file__).parent, "client-config.json"), "r") as f:
            self.headers = json.loads(f.read())
            self.headers["key"] = self.headers["apiKey"][len(self.headers["projectName"])+1:]

    def __str__(self):
        return self.name
    
    def collection(self, *args):
        return Reference(self, api=self.api, *args)

class Reference:
    def __init__(self, db: Montybase, *args, api: str = "http://127.0.0.1:5000"):
        self.db = db
        self.ref = args
        self.api_endpoint = api

    def __str__(self):
        ref = ", ".join([f'"{i}"' for i in self.ref])
        return f"doc({self.db.name}, {ref})"
    
    def where(self, key: str, operation: str, value: int | str):
        return FilteredReference(self, condition=(key, operation, value))
    
    def document(self, *args):
        self.ref += args
        return self
    
    def append(self, *args):
        self.ref += args
        return self
    
    def fetch(self, endpoint, value: str | int | float | bool | list | dict = None, key: str = None):
        url = self.api_endpoint + "/" + endpoint
        headers = {'Content-Type': 'application/json'} | self.db.headers  # Set the correct content type

        data = {"ref": self.ref}
        if value: data["value"] = value
        if key: data["id"] = key 

        response = requests.post(url, data=encrypt(self.db.headers["key"], data), headers=headers)

        if response.status_code != 200: raise requests.HTTPError(decrypt(self.db.headers["key"], response.content.decode()))
        else: return decrypt(self.db.headers["key"], response.content.decode())
    
    def set(self, value, key: str | None = None):
        if key: return self.fetch("set_doc", value, key=key)
        return self.fetch("set_doc", value)
    
    def add(self, value, key: str | None = None):
        return self.fetch("add_doc", value, key=key)
    
    def update(self, value, key: str | None = None):
        return self.fetch("update_doc", value, key=key)
    
    def stream(self) -> list[dict]:
        docs: dict = self.fetch("get_doc")
        return [{"id": key, "value":value} for key, value in docs.items()]
    
    def get(self) -> dict:
        return self.fetch("get_doc")
    
    def exists(self) -> bool:
        return bool(self.fetch("get_doc"))


class FilteredReference:
    def __init__(self, doc: Reference, condition: tuple):
        self.db = doc.db
        self.ref = doc.ref
        self.api_endpoint = doc.api_endpoint
        self.condition = condition

    def __str__(self):
        ref = ", ".join([f'"{i}"' for i in self.ref])
        return f"doc({self.db.name}, {ref}).where{self.condition}"
    
    def fetch(self, endpoint, value = None):
        url = self.api_endpoint + "/" + endpoint
        headers = {'Content-Type': 'application/json'} | self.db.headers # Set the correct content type

        data = {"ref": self.ref, "value": value}

        response = requests.post(url, data=encrypt(self.db.headers["key"], data), headers=headers)
        
        if response.status_code != 200: raise requests.HTTPError(decrypt(self.db.headers["key"], response.content.decode()))
        else: return decrypt(self.db.headers["key"], response.content.decode())

    def stream(self) -> list[dict]:
        docs: dict = self.fetch("get_doc", self.condition)
        return [{"id": key, "value":value} for key, value in docs.items()]
    
    def get(self):
        return self.fetch("get_doc", self.condition) 
    
    def exists(self) -> bool:
        return bool(self.fetch("get_doc", self.condition))

def doc(db: Montybase, *args):
    return Reference(db, *args)

async def addDoc(ref: Reference, value):
    return ref.add(value)

async def setDoc(ref: Reference, value):
    return ref.set(value)

async def updateDoc(ref: Reference, value):
    return ref.update(value)
