from flask import Blueprint, Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3 as sql
from views.docker import docker_connect,docker_rm
from werkzeug.security import generate_password_hash, check_password_hash
import time
import json

database_bp = Blueprint("database", __name__)
DB_DIR = 'database.db'


# use blueprint as app
@database_bp.route("/")
def database_index():
    sql.connect(DB_DIR)
    return "Database Index"

@database_bp.route("/test")
def test():
    return redirect(url_for('database.database_index'))

@database_bp.route("/init/", methods=['POST'])
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
                language TEXT NOT NULL,
                version TEXT NOT NULL,
                userid INTEGE,
                FOREIGN KEY(userid) REFERENCES users(id) on delete cascade
            );''')
        #create table users
        print("Table created successfully")
    conn.close()
    return None

def db_insertuser(name, pw):
    pwhash= generate_password_hash('NAME:'+name+'|PW:'+pw,method='pbkdf2:sha256',salt_length=8)
    try:
        conn = sql.connect(DB_DIR)

        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("INSERT INTO users (username, pwhash) \
            VALUES ('"+name+"','"+pwhash+"');")
        conn.commit()
        conn.close()
        return True

    except sql.Error as error:
        print("Failed to insert data into sqlite table", error)
        if conn:
            conn.close()
        return False



def db_insertcontainer(name, projectname='',language='',version=0):
    container_id = docker_connect()
    try:
        userid = db_selectUserByName(name)[0]
        conn = sql.connect(DB_DIR)
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("INSERT INTO containers (containerid, projectname, time, language, version, userid) \
            VALUES ('"+container_id+"','"+projectname+"','"+time.strftime('%Y-%m-%d %H:%M:%S')+"','"+language+"','"+str(version)+"','"+str(userid)+"');")
        conn.commit()
        conn.close()
        return container_id
    except sql.Error as error:
        print("Failed to insert data into sqlite table", error)
        if conn:
            conn.close()

def db_selectUserByName(name): # return tuple: (userid, pwhash)
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

def db_selectContainerByUser(name): # return list: [(projectname, containerid, language, version, time)]
    try:
        userid = db_selectUserByName(name)[0]
        conn = sql.connect(DB_DIR)
        conn.execute("PRAGMA foreign_keys=ON;")
        cur = conn.execute("SELECT projectname, containerid, language, version, time FROM containers WHERE userid ="+str(userid)+";")
        res = []
        for i in cur:
            res.append((i[0],i[1],i[2],i[3],i[4]))
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

def db_verify_pw(name, pw):
    try:
        pw = 'NAME:'+name+'|PW:'+pw
        pwhash = db_selectUserByName(name)[1]
        # print("verify",db_selectUserByName(name)[1])
        return check_password_hash(pwhash, pw)
    except:
        return False

def db_deleteuser(name, pw): # delete from db: True for successful, False for failed
    try:
        if db_verify_pw(name, pw):
            container_list = db_selectContainerByUser(name)
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

@database_bp.route("/createProject/", methods=['POST'])
def db_createProject():
    name = session['username']
    data = json.loads(request.data)
    projectname = data['projectname']
    language = data['language']
    version = data['version']
    res = db_insertcontainer(name, projectname, language, version)
    if res:
        return str(res), 200
    return "failed", 500

@database_bp.route("/getAllProjects/", methods=['GET'])
def db_getAllProjects():
    name = session['username']
    result = db_selectContainerByUser(name)
    if result is not None:
        return_list = []
        for i in result:
            temp = dict()
            temp['projectname'] = i[0]
            temp['containerid'] = i[1]
            temp['language'] = i[2]
            temp['version'] = i[3]
            temp['time'] = i[4]
            return_list.append(temp)
        return jsonify(return_list), 200
    return "failed", 500

@database_bp.route("/getProject/<container_id>", methods=['GET'])
def db_getProject(container_id):
    try:
        conn = sql.connect(DB_DIR)
        conn.execute("PRAGMA foreign_keys=ON;")
        cur = conn.execute("SELECT projectname, containerid, language, version, time FROM containers WHERE containerid ='"+container_id+"';")
        res = dict()
        for i in cur:
            res['projectname'] = i[0]
            res['containerid'] = i[1]
            res['language'] = i[2]
            res['version'] = i[3]
            res['time'] = i[4]
        conn.close()
        return jsonify(res), 200
    except:
        print('Failed to select data from sqlite table')
        return "failed", 500

@database_bp.route("/deleteProject/<container_id>", methods=['DELETE'])
def db_deleteProject(container_id):
    try:
        conn = sql.connect(DB_DIR)
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("DELETE FROM containers WHERE containerid ='"+container_id+"';")
        conn.commit()
        print("Total number of rows deleted :%d"%conn.total_changes)
        conn.close()
        return "success", 200
    except:
        print('Failed to select data from sqlite table')
        return "failed", 500

@database_bp.route("/updateProject/", methods=['POST'])
def db_updateProject():
    try:
        data = json.loads(request.data)
        container_id = data['containerid']
        newname = data['newname']
        conn = sql.connect(DB_DIR)
        conn.execute("PRAGMA foreign_keys=ON;")
        cur = conn.execute("UPDATE containers SET projectname='"+newname+"'WHERE containerid ='"+container_id+"';")
        conn.commit()
        conn.close()
        return "success", 200
    except:
        return "failed", 500
