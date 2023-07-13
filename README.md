#  🐦 warbler 🐦

#### twitter clone


* [Live Demo](https://warblertwitterclone-itzw.onrender.com/)
    * Demo user:
        * Username: TestUser
        * Password: password

## Technologies:

* Language: Python
* Web framework: Flask
* ORM: SQLAlchemy
* Additional libraries: Brypt, WTFforms, Unittests, jinja2

## Features:

* Users registration and login
* Users create and delete messages
* Users can like and unlike other user's messages
* Users can edit their own profile
* Search for other users

## Set Up:

1. Clone or fork this repository and be sure Python is installed on your machine

2. Setup a Python virtual environment 
 
 * ```$ python3 -m venv venv```
 * ```$ source venv/bin/activate```
 * ```(venv) $ pip3 install -r requirements.txt```

3. Set up data and seed your database(this application uses psql)
* ```(venv) $ psql```
* ```=# CREATE DATABASE warbler;```
* ```*ctrl d*```
* ```(venv) python3 seed.py*```

4. Create .env in the project directory with the two variable below

* ```SECRET_KEY="this-is-a-secret-shhhh"```
* ```DATABASE_URL=postgresql:///warbler```

5. Start the server by running

* ```$ flask run```
    * Mac users, port 5000 might be taken by another application to run on another port use the command below
    * ```$ flask run -p 5001```

6. View application by going to http://localhost:5000 or http://localhost:5001 on your browser

## Run test:

1. Create the test database
* ```(venv) $ psql``
* ```CREATE DATABASE warbler-test;```
2. Run tests:

* test all: ```python3 -m unittest```
* test specific files: ```python3 -m unittest "test_file_name"```


