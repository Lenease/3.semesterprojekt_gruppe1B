from flask import Flask, render_template, send_from_directory


app = Flask(__name__, template_folder="templates")

#statiske sider
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/hjem")
def hjem():
    return render_template("hjem.html")

@app.route("/beboer")
def beboer():
    return render_template("beboer.html")

#dynamisk side, forbindelse til databasen i postgreSQL
@app.route("/skema")
def skema():
    #conn = get_connection()
    #cur = conn.cursor()

    #cur.execute("SELECT * FROM beboer;")
    #rows = cur.fetchall()

    #cur.close()
    #conn.close()

    return render_template("skema.html")

@app.route("/images/<path:filename>")
def images(filename): 
    return send_from_directory("images", filename)


if __name__ == "__main__":
    app.run(debug=True)
