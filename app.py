from flask import Flask, request, jsonify, render_template, session
import json, os, uuid, threading
from datetime import datetime

app = Flask(__name__)
app.secret_key = b'drinkcount_secret_2024'

DATA_FILE = "/home/claude/drinkcount/data.json"
lock = threading.Lock()

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE) as f:
        try: return json.load(f)
        except: return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/join", methods=["POST"])
def join():
    body = request.get_json()
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Nom requis"}), 400
    uid = session.get("uid")
    if not uid:
        uid = str(uuid.uuid4())[:8].upper()
        session["uid"] = uid
        session.permanent = True
    with lock:
        data = load_data()
        if uid not in data:
            data[uid] = {"name": name, "count": 0, "joined": datetime.now().isoformat()}
        else:
            data[uid]["name"] = name
        save_data(data)
    return jsonify({"uid": uid, "name": name})

@app.route("/api/add", methods=["POST"])
def add():
    uid = session.get("uid")
    if not uid:
        return jsonify({"error": "Session invalide"}), 403
    with lock:
        data = load_data()
        if uid not in data:
            return jsonify({"error": "Utilisateur inconnu"}), 403
        data[uid]["count"] += 1
        save_data(data)
    return jsonify({"count": data[uid]["count"]})

@app.route("/api/state")
def state():
    with lock:
        data = load_data()
    uid = session.get("uid")
    total = sum(v["count"] for v in data.values())
    participants = sorted(
        [{"uid": k, "name": v["name"], "count": v["count"], "me": k == uid}
         for k, v in data.items()],
        key=lambda x: -x["count"]
    )
    return jsonify({
        "total": total,
        "participants": participants,
        "myUid": uid,
        "myCount": data[uid]["count"] if uid and uid in data else 0
    })

@app.route("/api/reset_mine", methods=["POST"])
def reset_mine():
    uid = session.get("uid")
    if not uid:
        return jsonify({"error": "Session invalide"}), 403
    with lock:
        data = load_data()
        if uid in data:
            data[uid]["count"] = 0
            save_data(data)
    return jsonify({"ok": True})

@app.route("/api/reset_all", methods=["POST"])
def reset_all():
    with lock:
        data = load_data()
        for k in data: data[k]["count"] = 0
        save_data(data)
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)
