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

    postgres_insert_query = """ INSERT INTO beboer (ID, CPR_NR, BEBOER, PILLE, DOSIS, TIDSPUNKT) VALUES (%s,%s,%s,%s,%s,%s)"""
    record_to_insert = (15, '11121942', 'Niels', 'Simvastin', '1', 'Aften') # denne skal man ændre i, hvis der skal tilføjes i databasen
    cursor.execute(postgres_insert_query, record_to_insert)

    connection.commit()
    count = cursor.rowcount
    print(count, "Record inserted successfully into beboer table")

except(Exception, psycopg2.Error) as error:
    print("Failed to insert record into beboer table", error)

finally:
    # closing database connection.
    if connection:
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")