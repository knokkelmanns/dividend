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
    cur.execute("SELECT * FROM dividend t1 WHERE t1.PAYOUT = (SELECT MAX(t2.PAYOUT) "
                "FROM dividend t2 WHERE t2.COMPANY_NAME = t1.COMPANY_NAME) ORDER BY t1.PAYOUT DESC;")

    data = cur.fetchall()
    return render_template('index.html', data=data)


@app.route("/company/<ticker>", methods=["GET"])
def get_company(ticker):
    cur.execute("SELECT * FROM dividend WHERE TICKER = %s;", (ticker,))
    company_data = cur.fetchall()

    return render_template('company.html', company_data=company_data)


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
