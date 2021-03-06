from flask import Flask, redirect, url_for, render_template, request, session, flash
import requests as rq
import pandas as pd
import config
import json
import csv
from datetime import timedelta
import datetime as dt
import plotly
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
from flask_bcrypt import Bcrypt

MODE = False

app = Flask(__name__)
crypt = Bcrypt(app)
app.config.from_pyfile('config.py')
app.permanent_session_lifetime = timedelta(minutes=5)

murl = config.url

# App Methods


def getWeatherData(nodeId):
    surl = murl + "getWtData/" + str(nodeId)
    data = rq.get(surl)
    dt = data.json()
    findt = json.dumps(dt["data"], indent=4)
    dt1 = json.loads(findt)
    filePath = "static/data_files/" + str(nodeId) + ".csv"
    csvfile = open(filePath, 'w', newline='')

    with csvfile:
        header = ['date_time', 'humd', 'id',
                  'location', 'pres', 'temp', 'uvindex']
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writeheader()
        for i in dt1:
            writer.writerow(i)

    df = pd.read_csv(filePath)
    findata = df[["date_time", "temp", "pres", "humd", "uvindex"]]
    temp = findata.to_dict('records')
    columnNames = findata.columns.values
    return temp, columnNames


def getNodesList():
    url = murl + "getNodes"
    data = rq.get(url)
    nodeData = data.json()
    nodeListStr = json.dumps(nodeData["nodes"], indent=4)
    nodeList = json.loads(nodeListStr)
    return nodeList


def getNodesCount():
    url = murl + "getNodes"
    data = rq.get(url)
    nodeData = data.json()
    nodeListStr = json.dumps(nodeData["nodes"], indent=4)
    nodeList = json.loads(nodeListStr)
    findt1 = json.dumps(nodeData["total_nodes"], indent=4)
    dt11 = json.loads(findt1)
    nodeCount = int(dt11)
    return nodeCount


def checkAuth(mailid, mpasswd):
    url = murl + "authUser/" + mailid + "/" + mpasswd
    dt = rq.get(url)
    rsp = dt.json()
    hashed = str(rsp[0]['data']['atoken'])
    crthash = hashed.replace('_', '/').encode('utf-8')
    auth = crypt.check_password_hash(crthash, mpasswd)

    return auth, rsp[0]['data']['admin_status'], rsp[0]['data']['name'], rsp[0]['data']['uid']


def userRegistration(name, email, password):
    url = murl + "regUser/" + name + "/" + email + "/" + password
    dt = rq.get(url)
    rsp = dt.json()
    result = int(rsp['status_code'])
    print(rsp['status_code'])
    return result


def fetchDataFromAPI():
    nds = getNodesList()
    for i in nds:
        getWeatherData(i)

# App Routing


fetchDataFromAPI()


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form['memail']
        passwd = request.form['mpasswd']
        approveLogin, isAdmin, userName, uid = checkAuth(email, passwd)
        if(approveLogin):
            session.permanent = True
            session["user"] = email
            session["isAdmin"] = isAdmin
            session["uname"] = userName
            session["uid"] = uid
            return redirect(url_for("home"))

    else:
        if "user" in session:
            return redirect(url_for("home"))

        return render_template("index.html")


@app.route('/home')
def home():
    if "user" in session:
        user = session["user"]
        name = session["uname"]
        ncount = getNodesCount()
        timest = dt.datetime.now()
        time = timest.strftime("%d-%m-%Y %I:%M:%S %p")

        return render_template("main.html", nodesCount=ncount, timestamp=time, uname=name)
    else:
        return render_template("index.html")


@app.route('/logout')
def logoutUser():
    session.pop("user", None)
    session.pop("isAdmin", None)
    session.pop("uname", None)
    session.pop("uid", None)
    return redirect(url_for("login"))


@app.route('/register', methods=['GET', 'POST'])
def registerUser():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['memail']
        passwd = request.form['mpasswd']
        hashed = crypt.generate_password_hash(passwd, 15)
        hp = hashed.decode("utf-8")
        fhash = hp.replace('/', '_')
        res = userRegistration(name, email, fhash)
        if(res == 201):
            flash("Successfully Registered")
            return render_template("index.html")
        else:
            flash("Registration failed. Please try again")
            redirect(url_for("registerUser"))

    else:
        if "user" in session:
            return redirect(url_for("home"))

    return render_template("register.html")


@app.route('/home/nodeDataTables', methods=['GET', 'POST'])
def dataTables():
    if request.method == "POST":
        nodeSelVal = request.form.get('nodeId')
        nds = getNodesList()
        rcords, cols = getWeatherData(nodeSelVal)
        return render_template("datatables.html", nodeList=nds, records=rcords, colnames=cols)

    else:
        if "user" in session:
            user = session["user"]
            nds = getNodesList()
            return render_template("datatables.html", nodeList=nds)
        else:
            return redirect(url_for("login"))


@app.route('/home/nodeDataVisualization', methods=['GET', 'POST'])
def visualizeNodeData():
    if request.method == "POST":
        nodeSelVal = request.form.get('nodeId')
        nds = getNodesList()
        fetchDataFromAPI()
        fname = "static/data_files/" + nodeSelVal + ".csv"
        df = pd.read_csv(fname)

        dtimedata = df["date_time"].values.tolist()
        tempdata = df["temp"].values.tolist()
        presdata = df["pres"].values.tolist()
        humddata = df["humd"].values.tolist()
        uvindata = df["uvindex"].values.tolist()

        tr_1 = go.Line(x=dtimedata, y=tempdata, name="Temperature Plot", line=dict(
            color="#EE480A", smoothing=1.3), mode='lines+markers', line_shape='spline')
        tr_2 = go.Line(x=dtimedata, y=presdata, name="Pressure Plot", line=dict(
            color="#0066ff", smoothing=1.3), mode='lines+markers', line_shape='spline')
        tr_3 = go.Line(x=dtimedata, y=humddata, name="Humidity Plot", line=dict(
            color="#30CC6C", smoothing=1.3), mode='lines+markers', line_shape='spline')
        tr_4 = go.Line(x=dtimedata, y=uvindata,
                       name="UV-Index Plot", line=dict(color="#00ffcc", smoothing=1.3), mode='lines+markers', line_shape='spline')

        fig1 = make_subplots(
            rows=2,
            cols=2,
            vertical_spacing=0.5,
        )

        fig1.add_trace(tr_1, row=1, col=1)
        fig1.add_trace(tr_2, row=1, col=2)
        fig1.add_trace(tr_3, row=2, col=1)
        fig1.add_trace(tr_4, row=2, col=2)

        fig1.update_yaxes(title_text="Temperature",
                          row=1, col=1, showgrid=False)
        fig1.update_yaxes(title_text="Pressure", row=1, col=2, showgrid=False)
        fig1.update_yaxes(title_text="Humidity", row=2, col=1, showgrid=False)
        fig1.update_yaxes(title_text="UV Index", row=2, col=2, showgrid=False)

        fig1.update_xaxes(title_text="Date", row=1, col=1, showgrid=False)
        fig1.update_xaxes(title_text="Date", row=1, col=2, showgrid=False)
        fig1.update_xaxes(title_text="Date", row=2, col=1, showgrid=False)
        fig1.update_xaxes(title_text="Date", row=2, col=2, showgrid=False)

        titleName = "<b>Node:" + nodeSelVal + " Data</b>"
        fig1.update_layout(title=titleName,
                           autosize=True,
                           title_x=0.5,
                           font=dict(
                               color="#000000",
                           )
                           )

        graphJSON = json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder)

        return render_template("nodeDataVisualization.html", nodeList=nds, graphJSON=graphJSON)

    else:
        if "user" in session:
            user = session["user"]
            nds = getNodesList()
            return render_template("nodeDataVisualization.html", nodeList=nds)
        else:
            return redirect(url_for("login"))


@app.route('/nodeManagement', methods=['GET', 'POST'])
def nodeManager():
    if "user" in session:
        user = session["user"]
        admstat = session["isAdmin"]

        if(admstat == 'False'):
            return redirect(url_for("adminError"))
        else:
            return render_template("nodeManagement.html", isadm=admstat)


@app.route('/adminError', methods=['GET', 'POST'])
def adminError():
    return render_template("notAdminError.html")


if __name__ == "__main__":
    app.run(debug=MODE, port=8009, threaded=True)
