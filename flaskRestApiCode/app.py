from flask import Flask, jsonify, render_template
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from models import (nodeList, Stats, WeatherNodeData,
                    adminAccessTable, requestHist, adminActionHist)
from models import db as db1
import json
import datetime as dt
import uuid
from random import randint
from flask_cors import CORS, cross_origin

MODE = False
CREATE_DB = False

app = Flask(__name__)
api = Api(app)
cors = CORS(app)

app.config.from_pyfile('config.py')

db = SQLAlchemy(app)

if(CREATE_DB):
    with app.app_context():
        db1.create_all()


class postData(Resource):
    def get(self, rqid, mac_id, id, loc, dtime, temp, pres, humd, uvid):
        isValidRequest = checkReq(rqid, mac_id, id)
        tm = str(dtime)
        datetimeSplit = tm.split("+")
        findtime = datetimeSplit[0] + " " + datetimeSplit[1]
        if(isValidRequest):
            data = WeatherNodeData(rqid, id, loc, findtime,
                                   temp, pres, humd, uvid)
            dt = {'request_id': rqid, 'mac_id': mac_id, 'node_id': id, 'location': loc, 'date_and_time': findtime,
                  'recorded_temperature': temp, 'recorded_presure': pres, 'recorded_humidity': humd, 'recorded_uv_index': uvid}
            db.session.add(data)
            db.session.commit()
            return jsonify({"status_code": 201, "action_status": "successful", "data": dt})

        else:
            return jsonify({"status_code": 403, "action_status": "Invalid Request"})


class getStatus(Resource):
    def get(self, nid):
        data = db.session.query(Stats.id, Stats.status).filter_by(id=nid)

        for lst in data:
            resp = {"status_code": 200, "node_id": nid,
                    "node_status": lst.status}

        return resp


class listApiData(Resource):
    def get(self):
        return jsonify({"status_code": "200", "API_Version": "1.3.0", "Author": "Shaga Sresthaa", "License": "GPL v3.0"})


class sendWeatherData(Resource):
    def get(self, nid):
        data = db.session.query(
            WeatherNodeData.id, WeatherNodeData.loc, WeatherNodeData.dtime, WeatherNodeData.temp, WeatherNodeData.pres, WeatherNodeData.humd, WeatherNodeData.uvid).filter_by(id=nid).order_by(WeatherNodeData.dtime)
        list1 = []
        for lst in data:

            txt = {'id': str(lst.id), 'date_time': str(lst.dtime), 'location': str(lst.loc), 'temp': str(
                lst.temp), 'pres': str(lst.pres), 'humd': str(lst.humd), 'uvindex': str(lst.uvid)}

            list1.append(txt)

        response = jsonify({"status_code": 200, "data": list1})
        return response


def idGenerator():
    rid = uuid.uuid4().hex
    return rid


def checkDuplicate(rndId):
    data = db.session.query(requestHist.rqid).filter_by(rqid=rndId).count()

    if(data == 0):
        return False
    else:
        return True


def checkNodeRequestValidity(nid, mac_id):
    data = db.session.query(nodeList.id, nodeList.mac_id).filter_by(id=nid)

    isValid = False

    for lst in data:

        if(lst.id == nid and lst.mac_id == mac_id):
            isValid = True
        else:
            isValid = False

    return isValid


def sendReqId():
    reqd = idGenerator()

    while(checkDuplicate(reqd)):
        reqd = idGenerator()

    return reqd


def checkReq(rqid, macAddr, nid):
    data = db.session.query(
        requestHist.rqid, requestHist.mac_id, requestHist.id).filter_by(rqid=rqid)
    for lst in data:
        if(lst.rqid == rqid and lst.mac_id == macAddr and lst.id == nid):
            return True

        else:
            return False


def checkDuplicateId(nid):
    data = db.session.query(nodeList.id).filter_by(id=nid).count()
    if(data == 0):
        return False
    else:
        return True


def idGenForNode():
    nid = randint(1000000, 9999999)
    return nid


def nidGenerator():
    nid = idGenForNode()
    while(checkDuplicateId(nid)):
        nid = idGenForNode()

    return nid


def checkNodeCreation(nid, mc_id):
    data = db.session.query(nodeList.id, nodeList.mac_id).filter_by(id=nid)

    for lst in data:
        if(lst.id == nid and lst.mac_id == mc_id):
            return True
        else:
            return False


def checkUserCreation(usid, usemail, uspasswd):
    data = db.session.query(adminAccessTable.id,
                            adminAccessTable.uemail,
                            adminAccessTable.passwd,
                            adminAccessTable.admin).filter_by(id=usid)

    for lst in data:
        if(lst.id == usid and lst.uemail == usemail and lst.passwd == uspasswd):
            return True

    return False


def checkUser(uid, email):
    data = db.session.query(adminAccessTable.id,
                            adminAccessTable.uemail).filter_by(id=uid, uemail=email).count()
    print(data)
    if(data == 0):
        return True
    return False


class reqIdGen(Resource):
    def get(self, nid, mac_id):
        now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        isValid = checkNodeRequestValidity(nid, mac_id)

        if(isValid):
            requestId = sendReqId()
            data = requestHist(requestId, nid, now, mac_id)
            db.session.add(data)
            db.session.commit()
            response = jsonify({"status_code": 200, "dtime": str(
                now), "node_id": nid, "reqid": requestId})

        else:
            response = jsonify(
                {"status_code": 403, "status": "Invalid Request"})

        return response


def userIdGenerator():
    num = idGenerator()
    data = db.session.query(adminAccessTable.id).filter_by(id=num).count()
    if(data == 0):
        return num
    else:
        userIdGenerator()


def checkUserPresence(unames, mailid):
    mailcount = db.session.query(adminAccessTable.uemail).filter_by(
        uemail=mailid).count()
    namecount = db.session.query(adminAccessTable.uemail).filter_by(
        nm=unames).count()
    if(mailcount > 0 or namecount > 0):
        return False
    else:
        return True


def checkDup(id):
    data = db.session.query(adminActionHist.rqid).filter_by(rqid=id).count()
    if(data == 0):
        return False
    else:
        return True


def rgen():
    reqd = idGenerator()

    while(checkDup(reqd)):
        reqd = idGenerator()

    return reqd


def checkIfAdmin(uid):
    data = db.session.query(adminAccessTable.admin).filter_by(id=uid)
    for usr in data:
        if(usr.admin == True):
            return True

        return False


def checkNodeStatusUpdate(nid):
    data = db.session.query(Stats.status).filter_by(id=nid)

    for node in data:
        return node.status


class nodeIdGenerator(Resource):
    def get(self, adm_id, loc, mac_id):
        req = rgen()
        now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        nodeId = nidGenerator()

        if(checkIfAdmin(adm_id)):
            data = nodeList(nodeId, loc, mac_id)
            db.session.add(data)
            dta = Stats(nodeId, "Inactive", mac_id)
            db.session.add(dta)

            if(checkNodeCreation(nodeId, mac_id)):
                strg = "Node Created " + str(nodeId)
                data = adminActionHist(req, adm_id, now, strg)
                db.session.add(data)
                db.session.commit()
                return jsonify({"status_code": 201, "node_reg_status": "node registered successfully", "assigned_node_id": nodeId})
            return jsonify({"status_code": 424, "node_reg_status": "node registration failed"})
        return jsonify({"status_code": 401, "msg": "you are not admin"})


class loginManager(Resource):
    def get(self, mail, passwd):
        data = db.session.query(adminAccessTable.uemail,
                                adminAccessTable.passwd,
                                adminAccessTable.nm,
                                adminAccessTable.id,
                                adminAccessTable.admin).filter_by(uemail=mail)

        for lst in data:
            return jsonify({"status_code": 200, "data": {"atoken": lst.passwd, "uid": lst.id, "name": lst.nm, "admin_status": lst.admin}}, 200)


class registerUser(Resource):
    def get(self, name, mail, passwd):
        uid = userIdGenerator()
        if(checkUserPresence(name, mail)):
            data = adminAccessTable(uid, name, mail, passwd, False)
            db.session.add(data)
            db.session.commit()
            if(checkUserCreation(uid, mail, passwd)):
                return jsonify({"status_code": 201, "user_reg_status": "user registered successfully", "assigned_user_id": uid})
            else:
                return jsonify({"status_code": 424, "user_reg_status": "user registration failed"})
        else:
            return jsonify({"status_code": 403, "user_reg_status": "user with same name or email already exists"})


class listAllNodes(Resource):
    def get(self):
        nodedata = db.session.query(nodeList).all()
        nodecount = db.session.query(nodeList.id).count()
        nodes = []

        for lst in nodedata:
            nodes.append(str(lst.id))

        return jsonify({"status_code": 201, "nodes": nodes, "total_nodes": str(nodecount)})


class sendUsersList(Resource):
    def get(self, adm_id):
        req = rgen()
        now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if(checkIfAdmin(adm_id)):
            strg = "User Data List Request"
            dta = adminActionHist(req, adm_id, now, strg)
            db.session.add(dta)
            db.session.commit()
            data = db.session.query(adminAccessTable.id, adminAccessTable.nm,
                                    adminAccessTable.uemail, adminAccessTable.admin).order_by(adminAccessTable.id)
            ulist = []

            for i in data:
                usr = {'id': str(i.id), 'name': str(i.nm), 'mailid': str(
                    i.uemail), 'admin_stat': str(i.admin)}
                ulist.append(usr)

            return jsonify({"status_code": 201, "data": ulist})
        return jsonify({"status_code": 401, "msg": "you are not admin"})


class assignAdmin(Resource):
    def get(self, adm_id, uid, admstat):
        req = rgen()
        now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if(admstat == "True"):
            astat = True
        else:
            astat = False
        if(checkIfAdmin(adm_id)):
            usr = db.session.query(adminAccessTable).filter_by(
                id=uid).first()
            usr.admin = astat
            db.session.commit()

            if(checkIfAdmin(uid) == astat):
                strg = "Admin status update: " + uid + " to " + admstat
                dta = adminActionHist(req, adm_id, now, strg)
                db.session.add(dta)
                db.session.commit()
                return jsonify({"status_code": 201, "msg": "update successful"})
            return jsonify({"status_code": 201, "msg": "update failed"})

        return jsonify({"status_code": 401, "msg": "you are not admin"})


class updateNodeStatus(Resource):
    def get(self, adm_id, nid, status):
        req = rgen()
        now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if(checkIfAdmin(adm_id)):
            node = db.session.query(Stats).filter_by(id=nid).first()
            node.status = status
            db.session.commit()
            if(checkNodeStatusUpdate(nid) == status):
                strg = "Node status update: " + str(nid)
                dta = adminActionHist(req, adm_id, now, strg)
                db.session.add(dta)
                db.session.commit()
                return jsonify({"status_code": 201, "msg": "node status update successful"})
            return jsonify({"status_code": 201, "msg": "node status update failed"})
        return jsonify({"status_code": 404, "msg": "endpoint under construction"})


class deleteNode(Resource):
    def get(self, adm_id, nid, mac_id):
        req = rgen()
        now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if(checkIfAdmin(adm_id)):
            db.session.query(nodeList).filter_by(
                id=nid, mac_id=mac_id).delete()
            if(not checkNodeCreation(nid, mac_id)):
                strg = "Node Deletion " + str(nid)
                data = adminActionHist(req, adm_id, now, strg)
                db.session.add(data)
                db.session.commit()
                return jsonify({"status_code": 201, "msg": "node deleted successfully"})
            return jsonify({"status_code": 304, "msg": "node deletetion failed"})

        return jsonify({"status_code": 401, "msg": "you are not admin"})


class deleteUser(Resource):
    def get(self, adm_id, uid, mailid):
        req = rgen()
        now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if(checkIfAdmin(adm_id)):
            db.session.query(adminAccessTable).filter_by(
                id=uid).delete()
            if(checkUser(uid, mailid)):
                strg = "User Deletion " + str(uid)
                data = adminActionHist(req, adm_id, now, strg)
                db.session.add(data)
                db.session.commit()
                return jsonify({"status_code": 201, "msg": "user deleted successfully"})
            return jsonify({"status_code": 304, "msg": "user deletetion failed"})

        return jsonify({"status_code": 401, "msg": "you are not admin"})


class sendNodeStats(Resource):
    def get(self, adm_id):
        req = rgen()
        now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if(checkIfAdmin(adm_id)):
            strg = "Nodes Status Request"
            data = adminActionHist(req, adm_id, now, strg)
            db.session.add(data)
            db.session.commit()
            nodes = db.session.query(Stats.id, Stats.status).all()
            ncount = db.session.query(Stats.id).count()
            ndata = []

            for node in nodes:
                txt = {"nid": str(node.id), "status": node.status}
                ndata.append(txt)

            return jsonify({"status_code": 201, "node_data": ndata, "total_nodes": ncount})


class listActiveAndPassiveNodesCount(Resource):
    def get(self):
        actNodes = db.session.query(Stats).filter_by(status="active").count()
        pasNodes = db.session.query(Stats).filter_by(status="inactive").count()
        return jsonify({"status_code": 200, "active_nodes": actNodes, "inactive_nodes": pasNodes})


api.add_resource(listActiveAndPassiveNodesCount, "/getActPasNodeCount")
api.add_resource(sendNodeStats, "/getAllNodeStats/<string:adm_id>")
api.add_resource(
    deleteUser, "/delUser/<string:adm_id>/<string:uid>/<string:mailid>")
api.add_resource(
    deleteNode, "/delNode/<string:adm_id>/<int:nid>/<string:mac_id>")
api.add_resource(updateNodeStatus,
                 "/updateNodeStatus/<string:adm_id>/<int:nid>/<string:status>")
api.add_resource(
    assignAdmin, "/updateAdmin/<string:adm_id>/<string:uid>/<string:admstat>")
api.add_resource(sendUsersList, "/usersList/<string:adm_id>")
api.add_resource(listAllNodes, "/getNodes")
api.add_resource(
    registerUser, "/regUser/<string:name>/<string:mail>/<string:passwd>")
api.add_resource(loginManager, "/authUser/<string:mail>/<string:passwd>")
api.add_resource(
    nodeIdGenerator, "/nodeCreate/<string:adm_id>/<string:loc>/<string:mac_id>")
api.add_resource(reqIdGen, "/getReqIdAuth/<int:nid>/<string:mac_id>")
api.add_resource(listApiData, "/apiInfo")
api.add_resource(sendWeatherData, "/getWtData/<int:nid>")
api.add_resource(getStatus, "/getStatus/<int:nid>")
api.add_resource(
    postData, "/postData/<string:rqid>/<string:mac_id>/<int:id>/<string:loc>/<string:dtime>/<float:temp>/<float:pres>/<float:humd>/<float:uvid>")

if __name__ == '__main__':
    app.run(debug=MODE, threaded=True)
