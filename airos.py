#!/usr/bin/python3

import requests
import json
import pymysql


# Read the config file
with open('config.json') as f:
    config = json.load(f)

# Process it
DB_HOSTNAME = config['db_hostname']
DB_DATABASE = config['db_database']
DB_USERNAME = config['db_username']
DB_PASSWORD = config['db_password']

HOSTNAME = config['hostname']
PROTOCOL = config['protocol']
USERNAME = config['username']
PASSWORD = config['password']

BASE_URL = "{}://{}".format(PROTOCOL, HOSTNAME)

# TODO: See if there's an existing cookie file
# try:
#     with open("cookie.cache", 'r') as f:
#         cookie = f.read()
# except Exception as e:
#     # Probably couldn't find the cookie file, make cookie empty
#     cookie = ""
#     print(e)


# Connect to the DB
db = pymysql.connect(DB_HOSTNAME, DB_USERNAME, DB_PASSWORD,
                     DB_DATABASE, cursorclass=pymysql.cursors.DictCursor)
cursor = db.cursor()

s = requests.Session()
s.get(BASE_URL)

# Login
data = {"username": (None, USERNAME), "password": (None, PASSWORD)}
login_url = "{}/login.cgi".format(BASE_URL)
r = s.post(login_url, files=data)
# Get status page
status_url = "{}/status.cgi".format(BASE_URL)
status = s.get(status_url)
# print(status.text)
status_json = json.loads(status.text)

# Get ifstats
ifstats_url = "{}/ifstats.cgi".format(BASE_URL)
ifstats = s.get(ifstats_url)
ifstats_json = json.loads(ifstats.text)
# print(ifstats.text)
# Make a json structure of things I care about collecting
output = {
    "hostname": HOSTNAME,
    "uptime": status_json['host']['uptime'],
    "time": status_json['host']['time'],
    "ssid": status_json['wireless']['essid'],
    "hide_ssid": status_json['wireless']['hide_essid'],
    "channel": status_json['wireless']['channel'],
    "frequency": float(status_json['wireless']['frequency'].split()[0]),
    "signal": status_json['wireless']['signal'],
    "txpower": status_json['wireless']['txpower'],
    "distance": status_json['wireless']['distance'],
    "noise": status_json['wireless']['noisef'],
    "txrate": float(status_json['wireless']['txrate']),
    "rxrate": float(status_json['wireless']['rxrate']),
    "chwidth": status_json['wireless']['chwidth'],
    "eth_status": status_json['interfaces'][1]['status']['plugged'],
    "eth_speed": status_json['interfaces'][1]['status']['speed'],
    "ath0_rx": float(ifstats_json['interfaces'][0]['stats']['rx_bytes']),
    "ath0_tx": float(ifstats_json['interfaces'][0]['stats']['tx_bytes']),
    "eth0_rx": float(ifstats_json['interfaces'][1]['stats']['rx_bytes']),
    "eth0_tx": float(ifstats_json['interfaces'][1]['stats']['tx_bytes'])
}

# print(json.dumps(output))
sql1 = "INSERT INTO airos ("
sql2 = ") VALUES ("
for tup in output.items():
    key = tup[0]
    value = tup[1]
    sql1 = "{}`{}`,".format(sql1, key)
    if isinstance(value, str):
        sql2 = "{}'{}',".format(sql2, value)
    else:
        sql2 = "{}{},".format(sql2, value)
sql1 = sql1[:-1]
sql2 = sql2[:-1]
sql2 += ")"
sql = "{}{}".format(sql1, sql2)
print(sql)
# print(json.dumps(output))

cursor.execute(sql)
db.commit()
db.close()
