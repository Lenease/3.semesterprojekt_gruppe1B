from flask import Flask, render_template, send_from_directory, request, redirect 
import psycopg2


app = Flask(__name__, template_folder="templates")


def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="jonas2011",
            host="10.136.140.130",
            port="5432"
        )
        return conn
    except Exception as e:
        print("Database connection error:", e)
        return None

#statiske sider
@app.route("/")
def start():
    return render_template("login.html")

@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/hjem")
def hjem():
    return render_template("hjem.html")

@app.route("/beboer")
def beboer():

    conn = get_db_connection()
    if conn is None:
        return "FEJL: Kan ikke forbinde til databasen."

    cur = conn.cursor()

    # Hent alt fra medicinplan
    cur.execute("""
        SELECT pyrusbeboer_id, medicin_id, dosis, tidspunkt 
        FROM medicinplan;
    """)
    rows = cur.fetchall()
    beboere = {}

    for beboer_id, medicin_id, dosis, tidspunkt in rows:

        # Hent beboer-navn
        cur.execute("SELECT navn FROM pyrusbeboer WHERE id = %s;", (beboer_id,))
        b_row = cur.fetchone()
        beboer_navn = b_row[0] if b_row else "Ukendt beboer"

        # Hent medicin-navn
        cur.execute("SELECT navn FROM medicin WHERE id = %s;", (medicin_id,))
        m_row = cur.fetchone()
        medicin_navn = m_row[0] if m_row else "Ukendt medicin"

        # Hvis beboer ikke findes i dict, opret hans/hendes struktur
        if beboer_navn not in beboere:
            beboere[beboer_navn] = {
                "Morgen": [],
                "Formiddag": [],
                "Eftermiddag": [],
                "Aften": []
            }

        # Ensret tidspunkt (første bogstav stort)
        t = tidspunkt.capitalize()

        # Hvis tidspunkt ikke findes, læg i Aften
        if t not in beboere[beboer_navn]:
            t = "Aften"

        # Tilføj medicin under tidspunkt
        beboere[beboer_navn][t].append({
            "medicin": medicin_navn,
            "dosis": dosis
        })

    cur.close()
    conn.close()

    return render_template("beboer.html", beboere=beboere)

#dynamisk side, forbindelse til databasen i postgreSQL
@app.route("/medicinplan", methods=["GET", "POST"])
def medicinplan():

    if request.method == "POST":
        beboer = request.form["beboer"]

        conn = get_db_connection()
        cur = conn.cursor()

        # loop igennem alle medicinrækker
        for key in request.form.keys():
            if key.startswith("medicin_"):
                n = key.split("_")[1]

                medicin = request.form.get(f"medicin_{n}")
                dosis = request.form.get(f"dosis_{n}")
                tidspunkt = request.form.get(f"tidspunkt_{n}")

                cur.execute("""
                    INSERT INTO medicinplan (pyrusbeboer_id, medicin_id, dosis, tidspunkt)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (pyrusbeboer_id, medicin_id, tidspunkt)
                    DO UPDATE SET dosis = EXCLUDED.dosis;
                    """, (beboer, medicin, dosis, tidspunkt))

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/medicinplan")

    return render_template("medicinplan.html")


@app.route("/images/<path:filename>")
def images(filename): 
    return send_from_directory("images", filename)


if __name__ == "__main__":
    app.run(debug=True)


