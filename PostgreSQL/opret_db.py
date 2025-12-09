import psycopg2
from psycopg2 import Error

try:
    connection = psycopg2.connect(
        user="postgres",
        password="jonas2011",
        host="100.119.141.120", #den bliver ændret hvergang Yuhang tilgår den
        port="5432",
        database="postgres")

    cursor = connection.cursor()
    
    # SQL query to create a new table
    create_table_query = '''CREATE TABLE beboer
          (ID SERIAL PRIMARY KEY,
          CPR_NR         TEXT    NOT NULL,
          BEBOER         TEXT    NOT NULL,
          PILLE          TEXT    NOT NULL,
          DOSIS          TEXT,
          TIDSPUNKT      TEXT); '''
    # Execute a command: this creates a new table
    cursor.execute(create_table_query)
    connection.commit()
    print("Table blev oprettet i PostgreSQL ")

except (Exception, Error) as error:
    print("Fejl under oprettelse af forbindelse til PostgreSQL", error)
finally:
    if connection:
        cursor.close()
        connection.close()
        print("PostgreSQL forbindelse er lukket")