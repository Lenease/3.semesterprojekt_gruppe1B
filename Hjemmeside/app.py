from flask import Flask, render_template



app = Flask(__name__)

#statiske sider
@app.route("/")
def hjem():
    return render_template("hjem.html")

@app.route("/beboer")
def beboer():
    return render_template("beboer.html")

#dynamisk side, forbindelse til databasen i postgreSQL
@app.route("/skema")
def skema():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT .......")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("skema.html", skema=rows)

if __name__ == "__main__":
    app.run(debug=True)
