from flask import Blueprint, Flask, render_template, request
import sqlite3 as sql
from views.docker import docker_connect
from werkzeug.security import generate_password_hash, check_password_hash

database_bp = Blueprint("database", __name__)


# use blueprint as app
@database_bp.route("/")
def database_index():
    return "Database Index"

def db_init():
    
    conn = sql.connect('database.db')
    print("Created / Opened database successfully")
    try:
         conn.execute("SELECT * FROM " + 'USERS;') # judge connect or not
         print("Table opened successfully")
    except:
        conn.execute('''
            CREATE TABLE USERS 
            (
                id INTEGER AUTO_INCREMENT, 
                name TEXT NOT NULL, 
                pwhash TEXT NOT NULL, 
                container_id TEXT NOT NULL,
                PRIMARY KEY (id)
            );''')
        #create table USERS
        print("Table created successfully")
    conn.close()
    return None

def db_insert(name, pw):
    pwhash= generate_password_hash('NAME:'+name+'|PW:'+pw,method='pbkdf2:sha256',salt_length=8)
    container_id = docker_connect(name + "_python")
    try:
        conn = sql.connect('database.db')
        conn.execute("INSERT INTO USERS (name, pwhash, container_id) \
            VALUES ('"+name+"','"+pwhash+"','"+container_id+"');")
        conn.commit()
        conn.close()
    except sql.Error as error:
        print("Failed to insert data into sqlite table", error)
        if conn:
            conn.close()

def db_select(name): # return tuple: (name, pwhash, container_id) 
    try:
        conn = sql.connect('database.db')
        cur = conn.execute("SELECT * FROM USERS WHERE name ='"+name+"';")
        res = None
        for i in cur:
            res = (i[1], i[2], i[3])
        conn.commit()
        conn.close()
        return res
    except sql.Error as error:
        print("Failed to select data from sqlite table", error)
        if conn:
            conn.close()
        return None

def db_verify_pw(name, pw):
    try:
        pw = 'NAME:'+name+'|PW:'+pw
        pwhash = db_select(name)[1]
        return check_password_hash(pwhash, pw)
    except:
        return False