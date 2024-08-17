# montybase (beta)
Python-based, NoSQL, in-memory, persistent, document database inspired by Firebase Firestore and Pocketbase. Montybase is best suited for small to medium scale Python projects that needs a versatile storage system (e.g. Highscores, Leaderboards, Posts, Accounts, etc). 

```shell
pip install montybase
```

Montybase is in beta, however if demand arises, more features, better documentation and updates will be added. 
Montybase supports chaining (like in JavaScript!).

## Why? (Recommended Uses)
With Montybase, you can natively use a complex NoSQL data structure in your program. If you are hosting a server for a website it can natively store data on the same server and does not need to run seperately on a different host. 

## Features
+ Symmetric Encryption 
+ API Key Authentication
+ Query Filters
+ Storage Bucket Settings

## Documentation
Montybase works as a giant JSON tree. At the moment there are only a few operations available. However, these operations are powerful enough to cover a substantial number of use cases. 

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

## Server Endpoint Setup
#### Development Mode (hosts on 127.0.0.1:5000)
```Python
from montybase import *

mb = Montybase(dev=True)
mb.run()
```
or specify your dev endpoint like so:
```Python
from montybase import *

mb = Montybase(dev="localhost:8000")
mb.run()
```

#### Production Mode (hosts on 0.0.0.0:5000)
```Python
from montybase import *

mb = Montybase(endpoint=True)
mb.run()
```

This will automatically create config files and the persistent db. This will also generate a config-file for the client side application (`client-config.json`). This file must be stored locally on all client side apps since it stores information such as the database's API and encryption key. Otherwise, access to the database will be denied.

### Client-Side Connect to Database Server Endpoint
```Python
from montybase import *

mb = Montybase(api="https://example.com/")
mb.run()
```

<hr>

## Local Setup
If you don't want to run Montybase as an endpoint simply:

```Python
from montybase import *

mb = Montybase()
```

### Hot Reload
Instantly update to persistent storage
```Python
from montybase import *

mb = Montybase(hot=True)
```

### Create Reference
```Python
ref = doc(db, "users", "amooo-ooo")
```

### Append Reference
```Python
new_ref = doc(db, "users").append("amooo-ooo") # new_ref = doc(db, "users", "amooo-ooo")
```

### Set Data
Sets a completely new document.
```Python
ref = doc(db, "users")
uid = ref.set({"name": "Amor"})
```
Any functions that manipulates data will always return the unique ID of the document which can then be appended with `ref.append(uid)` to inspect further. 

For example:
```Python
ref = doc(db, "users")
uid = ref.set({"name": "Amor"}) # uid = "q7Vb2kdX-ZcjOFnZW6zW"

new_ref = ref.append(uid) # doc(db, "users", "q7Vb2kdX-ZcjOFnZW6zW")
print(new_ref.get())
```

Output:
```shell
{"name": "Amor"}
```

You can also specify the `unique-id` instead of a randomly generated ID by doing the following on any functions that manipulates data:

```Python
ref = doc(db, "users")
uid = ref.set({"name": "Amor"}, key="amor.budiyanto@gmail.com") # uid = "amor.budiyanto@gmail.com"

print(uid)
```

Output:
```shell
amor.budiyanto@gmail.com
```

### Add Data
Add a new document.
```Python
ref = doc(db, "users")
uid = ref.add({"name": "Amor"})
```

### Delete Data
Delete a document. Will return its deleted contents.
```Python
ref = doc(db, "users")
uid = ref.delete({"name": "Amor"}) # uid = {"name": "Amor"}
```

### Update Data
Updates value of a document.
```Python
ref = doc(db, "users")
uid = ref.set({"name": "Amor", "score": 100})

new_ref = ref.append(uid)
uid = ref.update({"score": 120})

print(new_ref.get())
```

Output:
```shell
{"name": "Amor", "score": 120}
```

### Get Data
Returns the data from the reference.
```Python
ref = doc(db, "users")
uid = ref.set({"name": "Amor", "score": 100})

print(ref.get())
```

Output:
```shell
{"7d857f9c-ab1a-4906-a7ce-be1e62486b75": {"name": "Amor", "score": 120}}
```

### Stream Data
Returns list of dicts containing their `id` and their `value`.

```Python
ref = doc(db, "scores")

uid = ref.set({"name": "Amor", "score": 100})
uid = ref.add({"name": "Toriel", "score": 120})
uid = ref.add({"name": "Isaac", "score": 130})

docs = ref.stream()
print(docs)
```

Output:
```shell
[{'id': '54e73f44-06c9-4aab-802f-97bde02921b8', 'value': {'name': 'Amor', 'score': 100}}, {'id': 'c3ea0bb7-2c31-4f21-8ff3-bd0d8a8445f0', 'value': {'name': 'Toriel', 'score': 120}}, {'id': '9337609f-e731-4a94-a044-3ca8cc94b466', 'value': {'name': 'Isaac', 'score': 130}}]
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
uid = ref.set({"name": "Amor", "score": 100}, key="amor.budiyanto@gmail.com")

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
    "projectName": "montybase", // Name of the app
    "apiKey":"mb-...", // Also the symmetric encryption key
    "storageBucket": "path/to/database", // Path to the raw JSON file
    "storageMinCount": 1, // Run the long-term saving function after N changes.
    "storageUpdate": 300 // Update the raw JSON data file after N seconds, AFTER exceeding "storageMinCount" changes.
}
```

Database saves information in the long-term by waiting until the `storageMinCount` is exceeded and resetted. This then creates a timer of `storageUpdate` seconds, where the DB is predicted to be active. Once the timer runs out it saves the currect active DB into the raw JSON file for long-term storage.

You can change how often it reloads by setting:
```Python
from montybase import *

mb = Montybase(updateTime = 300,
               storeMin = 1,)
```


## Free Hosting
If you are interested in hosting the database online for free, I recommend using pythonanywhere.com. It is an online service which lets you hosts free python based back-end applications. 

## Origin
Montybase was born out of curiousty, and designed with simplicity in mind. Its main origin started off as a simple online database for a school internal assignment. With Montybase, you can natively use a complex NoSQL data structure alongside your program. If you are hosting a server for a website it can natively store data on the same server and does not need to run seperately on a different host. Another reason was because Firebase Firestore prices can accumulate substantially in the long-term and Pocketbase doesn't seem to have Python integration.  

Its name was inspired from Python's name origin: "Monty Python". 

## Future Features
+ Asymmetric Encryption
+ Realtime Listeners
+ Restricted Client Access
+ Data Type Rules 
+ Data Size Limits

## Contact
Feel free to contact me at amor.budiyanto@gmail.com