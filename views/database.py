from flask import Blueprint, Flask, render_template, request, redirect, url_for
import sqlite3 as sql
from views.docker import docker_connect,docker_rm
from werkzeug.security import generate_password_hash, check_password_hash
import time

database_bp = Blueprint("database", __name__)
DB_DIR = 'database.db'


# use blueprint as app
@database_bp.route("/")
def database_index():
    return "Database Index"

@database_bp.route("/test")
def test():
    return redirect(url_for('database.database_index'))

@database_bp.route("/init")
def db_init():
    conn = sql.connect(DB_DIR)
    conn.execute("PRAGMA foreign_keys=ON;")
    print("Created / Opened database successfully")
    try:
         conn.execute("SELECT * FROM " + 'users;') # judge connect or not
         print("Table opened successfully")
    except:
        conn.execute('''
            CREATE TABLE users
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                pwhash TEXT NOT NULL
            );''')
        conn.execute('''
            CREATE TABLE containers
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                containerid TEXT NOT NULL,
                projectname TEXT,
                time DATETIME NOT NULL,
                userid INTEGE,
                FOREIGN KEY(userid) REFERENCES users(id) on delete cascade
            );''')
        #create table users
        print("Table created successfully")
    conn.close()
    return None

@database_bp.route("/register")
def db_insertuser(name, pw):
    pwhash= generate_password_hash('NAME:'+name+'|PW:'+pw,method='pbkdf2:sha256',salt_length=8)
    try:
        conn = sql.connect(DB_DIR)
        
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("INSERT INTO users (username, pwhash) \
            VALUES ('"+name+"','"+pwhash+"');")
        conn.commit()
        conn.close()
    except sql.Error as error:
        print("Failed to insert data into sqlite table", error)
        if conn:
            conn.close()

@database_bp.route("/createproject")
def db_insertcontainer(name, projectname='DEFAULT'):
    container_id = docker_connect()
    try:
        userid = db_selectuser(name)[0]
        conn = sql.connect(DB_DIR)
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("INSERT INTO containers (containerid, projectname, time, userid) \
            VALUES ('"+container_id+"','"+projectname+"','"+time.strftime('%Y-%m-%d %H:%M:%S')+"',"+str(userid)+");")
        conn.commit()
        conn.close()
        print("success")
    except sql.Error as error:
        print("Failed to insert data into sqlite table", error)
        if conn:
            conn.close()

@database_bp.route("/selectuser")
def db_selectuser(name): # return tuple: (userid, pwhash)
    try:
        conn = sql.connect(DB_DIR)
        conn.execute("PRAGMA foreign_keys=ON;")
        cur = conn.execute("SELECT id, pwhash FROM users WHERE username ='"+name+"';")
        res = None
        for i in cur:
            res = (i[0], i[1])
        conn.commit()
        conn.close()
        return res
    except sql.Error as error:
        print("Failed to select data from sqlite table", error)
        if conn:
            conn.close()
        return None

@database_bp.route("/selectproject")
def db_selectcontainer(name): # return list: [(projectname, containerid)]
    try:
        userid = db_selectuser(name)[0]
        conn = sql.connect(DB_DIR)
        conn.execute("PRAGMA foreign_keys=ON;")
        cur = conn.execute("SELECT projectname, containerid FROM containers WHERE userid ="+str(userid)+";")
        res = []
        for i in cur:
            res.append((i[0],i[1]))
        conn.commit()
        conn.close()
        return res
    except sql.Error as error:
        print("Failed to select data from sqlite table", error)
        if conn:
            conn.close()
        return None
    except:
        print('Failed to select data from sqlite table')
        return None

@database_bp.route("/verify")
def db_verify_pw(name, pw):
    try:
        pw = 'NAME:'+name+'|PW:'+pw
        pwhash = db_selectuser(name)[1]
        # print("verify",db_selectuser(name)[1])
        return check_password_hash(pwhash, pw)
    except:
        return False

@database_bp.route("/deregister")
def db_deleteuser(name, pw): # delete from db: True for successful, False for failed
    try:
        if db_verify_pw(name, pw):
            container_list = db_selectcontainer(name)
            conn = sql.connect(DB_DIR)
            conn.execute("PRAGMA foreign_keys=ON;")
            if container_list:
                for i in container_list:
                    docker_rm(i[1])
            conn.execute("DELETE FROM users WHERE username ='"+name+"';") # delete cascade
            conn.commit()
            print("Total number of rows deleted :%d"%conn.total_changes)
            conn.close()
            return True
        else:
            print("Failed to delete data from sqlite table", "name/pw wrong!")
            return False
    except sql.Error as error:
        print("Failed to delete data from sqlite table", error)
        if conn:
            conn.close()
        return False
