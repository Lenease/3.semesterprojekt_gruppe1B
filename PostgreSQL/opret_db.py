import psycopg2
from psycopg2 import Error

try:
    connection = psycopg2.connect(
        user="postgres",
        password="jonas2011",
        host="10.136.139.150", #den bliver ændret hvergang Yuhang tilgår den
        port="5432",
        database="postgres")

    cursor = connection.cursor()
    
    # SQL query to create a new table #table 1
    create_beboer_table = '''CREATE TABLE beboer
          (ID SERIAL PRIMARY KEY,
          CPR_NR         TEXT    NOT NULL,
          BEBOER         TEXT    NOT NULL,
          PILLE          TEXT    NOT NULL,
          DOSIS          TEXT,
          TIDSPUNKT      TEXT); '''
    #table 2
    create_medicinplan_table = '''CREATE TABLE medicinplan
          (ID SERIAL PRIMARY KEY,
          PYRUSBEBOER_ID TEXT    NOT NULL,
          MEDICIN_ID     TEXT    NOT NULL,
          DOSIS          TEXT    NOT NULL,
          TIDSPUNKT      TEXT); '''
    
    #table 3
    create_medicin_table = '''CREATE TABLE medicin
          (ID SERIAL PRIMARY KEY,
          NAVN           TEXT    NOT NULL
          ); '''
    
    #Eksever alle tabeller
    cursor.execute(create_beboer_table)
    cursor.execute(create_medicinplan_table)
    cursor.execute(create_medicin_table)
    connection.commit()
    print("Alle tabeller blev oprettet i PostgreSQL ")

except (Exception, Error) as error:
    print("Fejl under oprettelse af forbindelse til PostgreSQL", error)
finally:
    if connection:
        cursor.close()
        connection.close()
        print("PostgreSQL forbindelse er lukket")