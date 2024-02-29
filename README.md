# montybase (beta)
Simple, Python-based, NoSQL database inspired by Firebase Firestore and Pocketbase. Montybase is a small database written in Python. It simply works as a giant dictionary tree! Montybase is best suited for small to medium scale Python projects which may require an online storage system (e.g. Highscores, Leaderboards, Posts, Accounts, etc). 

Montybase is in beta, however if demand arises, more features, better documentation and updates will be added. 


## Features
+ Symmetric Encryption 
+ API Key Authentication
+ Query Filters
+ Storage Bucket Settings

## Setup
Set up the program by downloading the files on this repo. 

```shell
git clone https://github.com/amooo-ooo/montybase
```

To install required dependencies, simply run the following on terminal:

```shell
pip install -r requirements.txt
```

### API (back-end)
Store `api.py` locally and run the following to host the server:

```Python
from api import MontybaseAPI

mb = MontybaseAPI()
mb.run()
```

It will automatically initialise its working environment and create config files, as well as the raw json database format. This will also generate a config-file for the client side application (`client-config.json`). This file must be stored locally on all client side apps since it stores information such as the database's API and encryption key. Otherwise, access to the database will be denied.

### Client (Front-end)
Store `montybase.py` locally and run the following:

```Python
from montybase import *

db = Montybase()
...
```


## Documentation (Client-side)
Montybase simply works as a giant JSON tree. At the moment there are only a few operations available. However, these operations are powerful enough to cover a substantial number of use cases. 

Authentication Example:
```Python
def signup(db, email, password):
    ref = doc(db, "users")
    if ref.append(email).exists():
        raise ValueError("User already exists!")
    
    return ref.add({"password": password}, key=email)

def login(db, email, password):
    ref = doc(db, "users", email)
    if ref.exists():
        if ref.where("password", "==", password).exists():
            return ref.get()

        raise ValueError("Password is incorect!")
    raise ValueError("User doesn't exist!")
```

### Initialise DB
```Python
db = Montybase("http://127.0.0.1:5000")
```

### Create Reference
```Python
ref = doc(db, "users", "amooo-ooo")
```

### Append Reference
```Python
new_ref = doc(db, "users").append("amooo-ooo")
```

### Set Data
Sets a completely new document.
```Python
ref = doc(db, "users")
uid = ref.set({"name": "Alan"})
```
Any functions that manipulates data will always return the unique ID of the document which can then be appended with `ref.append(uid)` to inspect further. 

For example:
```Python
ref = doc(db, "users")
uid = ref.set({"name": "Alan"}) # uid = "7d857f9c-ab1a-4906-a7ce-be1e62486b75"

new_ref = ref.append(uid) # doc(db, "users", "7d857f9c-ab1a-4906-a7ce-be1e62486b75")
print(new_ref.get())
```

Output:
```shell
{"name": "Alan"}
```

<hr>

You can also specify the `unique-id` instead of a randomly generated ID by doing the following on any functions that manipulates data:

```Python
ref = doc(db, "users")
uid = ref.set({"name": "Alan"}, key="alan@gmail.com") # uid = "alan@gmail.com"

print(uid)
```

Output:
```shell
alan@gmail.com
```

### Add Data
Add a new document to existing path.
```Python
ref = doc(db, "users")
uid = ref.add({"name": "Alan"})
```

### Update Data
Updates value of a document.
```Python
ref = doc(db, "users")
uid = ref.set({"name": "Alan", "score": 100})

new_ref = ref.append(uid)
uid = ref.update({"score": 120})

print(new_ref.get())
```

Output:
```shell
{"name": "Alan", "score": 120}
```

### Get Data
Returns the data from the reference.
```Python
ref = doc(db, "users")
uid = ref.set({"name": "Alan", "score": 100})

print(ref.get())
```

Output:
```shell
{"7d857f9c-ab1a-4906-a7ce-be1e62486b75": {"name": "Alan", "score": 120}}
```

### Stream Data
Returns list of dicts containing their `id` and their `value`.

```Python
ref = doc(db, "scores")

uid = ref.set({"name": "Alan", "score": 100})
uid = ref.add({"name": "Toriel", "score": 120})
uid = ref.add({"name": "Isaac", "score": 130})

docs = ref.stream()
print(docs)
```

Output:
```shell
[{'id': '54e73f44-06c9-4aab-802f-97bde02921b8', 'value': {'name': 'Alan', 'score': 100}}, {'id': 'c3ea0bb7-2c31-4f21-8ff3-bd0d8a8445f0', 'value': {'name': 'Toriel', 'score': 120}}, {'id': '9337609f-e731-4a94-a044-3ca8cc94b466', 'value': {'name': 'Isaac', 'score': 130}}]
```

### Filter Data
Filters the data according to a condition.

```Python
ref = doc(db, "users")
data = ref.where("score", ">", 100)
```

Conditions:
|Symbol|Description|
|---|---|
| `==`| Equal to |
| `!=`| Not equal to |
| `>` | Greater than |
| `<` | Lesser than |
| `>=` | Greater or equal to |
| `<=` | Lesser or equal to |


### Check if data exists
Checks if data exists (returns `True` or `False`)
```Python
ref = doc(db, "users")
uid = ref.set({"name": "Alan", "score": 100}, key="alan@gmail.com")

print(ref.append(uid).exist())
```

Output:
```shell
True
```

## Documentation (Server-side)

### Config File

```json
{
    "projectName": "api", // Name of the app
    "apiKey":"api-...", // Also the symmetric encryption key
    "storageBucket": "path/to/database", // Path to the raw JSON file
    "storageMinCount": 1, // Run the long-term saving function after N changes.
    "storageUpdate": 300 // Update the raw JSON data file after N seconds, AFTER exceeding "storageMinCount" changes.
}
```

Database saves information in the long-term by waiting until the `storageMinCount` is exceeded and resetted. This then creates a timer of `storageUpdate` seconds, where the DB is predicted to be active. Once the timer runs out it saves the currect active DB into the raw JSON file for long-term storage.


## Free Hosting
If you are interested in hosting the database online for free, I recommend using pythonanywhere.com. It is an online service which lets you hosts python based back-end applications. Simply setup the serverside system on the pythonanyhere server and change the api endpoint of client programs to the server's url.

## Origin
Montybase was born out of curiousty, and designed with simplicity in mind. Its main origin started off as a simple online database for a school internal assignment. Another reason was because Firebase Firestore prices can accumulate substantially in the long-term and Pocketbase doesn't seem to have Python integration.

Its name was inspired from Python's name origin: "Monty Python". 

## Future Features
+ Asymmetric Encryption
+ Realtime Listeners
+ Restricted Client Access
+ Data Type Rules 

## Contact
Feel free to contact me at amor.budiyanto@gmail.com