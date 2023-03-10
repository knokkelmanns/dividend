import config
import psycopg2
from flask_cors import CORS
from flask import Flask, jsonify, render_template

app = Flask(__name__)
CORS(app)

con = psycopg2.connect(database=config.database, user=config.user, password=config.password,
                       host=config.host, port=config.port)
cur = con.cursor()


@app.route("/", methods=["GET"])
def view_home():
    cur.execute("SELECT * FROM dividend;")
    data = cur.fetchall()
    return render_template('index.html', data=data)


@app.route("/company/", methods=["GET"])
@app.route("/company/<ticker>", methods=["GET"])
def get_company():
    cur.execute("SELECT * FROM dividend;")
    name = cur.fetchall()

    return render_template('company.html', data=name)


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
