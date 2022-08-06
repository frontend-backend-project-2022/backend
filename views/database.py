from flask import Blueprint, Flask, render_template, request, redirect, url_for
import sqlite3 as sql
from views.docker import docker_connect,docker_rm
from werkzeug.security import generate_password_hash, check_password_hash
import time

database_bp = Blueprint("database", __name__)


# use blueprint as app
@database_bp.route("/")
def database_index():
    return "Database Index"

@database_bp.route("/test")
def test():
    return redirect(url_for('database.database_index'))

@database_bp.route("/init")
def db_init():
    conn = sql.connect('database.db')
    print("Created / Opened database successfully")
    try:
         conn.execute("PRAGMA foreign_keys=ON;")
         conn.execute("SELECT * FROM " + 'users;') # judge connect or not
         print("Table opened successfully")
    except:
        conn.execute('''
            CREATE TABLE users
            (
                id INTEGER AUTO_INCREMENT,
                username TEXT NOT NULL UNIQUE,
                pwhash TEXT NOT NULL,
                PRIMARY KEY(username)
            );''')
        conn.execute('''
            CREATE TABLE containers
            (
                id INTEGER AUTO_INCREMENT,
                containerid TEXT NOT NULL,
                time DATETIME NOT NULL,
                username TEXT,
                FOREIGN KEY(username) REFERENCES users(username),
                PRIMARY KEY(id)
            );''')
        #create table users
        print("Table created successfully")
    conn.close()
    return None

@database_bp.route("/register")
def db_insertuser(name, pw):
    pwhash= generate_password_hash('NAME:'+name+'|PW:'+pw,method='pbkdf2:sha256',salt_length=8)
    try:
        conn = sql.connect('database.db')
        conn.execute("INSERT INTO users (username, pwhash) \
            VALUES ('"+name+"','"+pwhash+"');")
        conn.commit()
        conn.close()
    except sql.Error as error:
        print("Failed to insert data into sqlite table", error)
        if conn:
            conn.close()

@database_bp.route("/createproject")
def db_insertcontainer(name):
    container_id = docker_connect()
    try:
        conn = sql.connect('database.db')
        conn.execute("INSERT INTO containers (containerid, time, username) \
            VALUES ('"+container_id+"','"+time.strftime('%Y-%m-%d %H:%M:%S')+"','"+name+"');")
        conn.commit()
        conn.close()
        print("success")
    except sql.Error as error:
        print("Failed to insert data into sqlite table", error)
        if conn:
            conn.close()

@database_bp.route("/selectuser")
def db_selectuser(name): # return tuple: (name, pwhash)
    try:
        conn = sql.connect('database.db')
        cur = conn.execute("SELECT username, pwhash FROM users WHERE username ='"+name+"';")
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
def db_selectcontainer(name): # return list: [containerid]
    try:
        conn = sql.connect('database.db')
        cur = conn.execute("SELECT containerid FROM containers WHERE username ='"+name+"';")
        res = []
        for i in cur:
            res.append(i[0])
        conn.commit()
        conn.close()
        return res
    except sql.Error as error:
        print("Failed to select data from sqlite table", error)
        if conn:
            conn.close()
        return None

@database_bp.route("/verify")
def db_verify_pw(name, pw):
    try:
        pw = 'NAME:'+name+'|PW:'+pw
        pwhash = db_selectuser(name)[1]
        print("verify",db_selectuser(name)[1])
        return check_password_hash(pwhash, pw)
    except:
        return False

@database_bp.route("/deregister")
def db_deleteuser(name, pw): # delete from db: True for successful, False for failed
    try:
        if db_verify_pw(name, pw):
            conn = sql.connect('database.db')
            container_list = db_selectcontainer(name)
            if container_list:
                for i in container_list:
                    docker_rm(i)
            conn.execute("DELETE FROM containers WHERE username ='"+name+"';")
            conn.execute("DELETE FROM users WHERE username ='"+name+"';")
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
