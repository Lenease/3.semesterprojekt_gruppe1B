import psycopg2
from psycopg2 import Error

try:
    connection = psycopg2.connect(
        user="postgres",
        password="2300",
        host="127.0.0.1",
        port="5432",
        database="postgres")

    cursor = connection.cursor()

    postgres_insert_query = """ INSERT INTO medicin (ID, BEBOER, PILLE, DOSIS, TIDSPUNKT) VALUES (%s,%s,%s,%s,%s)"""
    record_to_insert = (5, 'test', 'test', '1', 'Eftermiddag') # denne skal man ændre i, hvis der skal tilføjes i databasen
    cursor.execute(postgres_insert_query, record_to_insert)

    connection.commit()
    count = cursor.rowcount
    print(count, "Record inserted successfully into medicin table")

except(Exception, psycopg2.Error) as error:
    print("Failed to insert record into medicin table", error)

finally:
    # closing database connection.
    if connection:
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")