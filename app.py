from flask import Flask, render_template, jsonify
import requests
import sqlite3

app = Flask(__name__)

# OpenDaylight RESTCONF API settings
ODL_URL = 'http://13.201.79.70:8181/restconf/operational/network-topology:network-topology'
ODL_USERNAME = 'admin'
ODL_PASSWORD = 'admin'

# Database setup
DB_NAME = "hosts.db"

def init_db():
    """Initialize SQLite database and create table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS hosts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        mac TEXT UNIQUE,
                        ip TEXT
                    )''')
    conn.commit()
    conn.close()

def save_to_db(mac, ip):
    """Save host information to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO hosts (mac, ip) VALUES (?, ?)", (mac, ip))
    conn.commit()
    conn.close()

def fetch_hosts_from_odl():
    """Fetch host IP and MAC from OpenDaylight."""
    response = requests.get(ODL_URL, auth=(ODL_USERNAME, ODL_PASSWORD))

    if response.status_code == 200:
        host_list = []
        for nodes in response.json().get('network-topology', {}).get('topology', []):
            for node in nodes.get('node', []):
                try:
                    ip = node['host-tracker-service:addresses'][0]['ip']
                    mac = node['host-tracker-service:addresses'][0]['mac']
                    host_list.append({"mac": mac, "ip": ip})
                    save_to_db(mac, ip)  # Save to database
                except KeyError:
                    pass
        return host_list
    else:
        return []

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/hosts')
def hosts():
    hosts = fetch_hosts_from_odl()
    return render_template('hosts.html', hosts=hosts)

@app.route('/analytics')
def analytics():
    """Show number of unique hosts in database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(DISTINCT mac) FROM hosts")
    host_count = cursor.fetchone()[0]
    conn.close()
    return render_template('analytics.html', host_count=host_count)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
