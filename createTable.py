import sqlite3

conn = sqlite3.connect('hours.db')
cur = conn.cursor()
print("Opened database successfully")

# Modify the HOURS column to use REAL instead of INT to allow for decimal values
conn.execute('''CREATE TABLE hours
        (DATE       DATE    NOT NULL,
        CATEGORY    TEXT    NOT NULL,
        HOURS       REAL     NOT NULL);''')
print("Table created successfully")

conn.close()
