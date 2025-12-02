import psycopg2
from psycopg2 import Error

try:
    connection = psycopg2.connect(
        user="postgres",
        password="jonas2011",
        host="10.136.139.236",
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
    print("Table created successfully in PostgreSQL ")

except (Exception, Error) as error:
    print("Error while connecting to PostgreSQL", error)
finally:
    if connection:
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")