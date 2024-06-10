import mysql.connector

class SQLUpdate(object):

    def __init__(self):
        self.hi = "HI"
        
    def connect_db(self):
        mydb = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="Aung9htet.ah"
        )

        print(mydb.is_connected())