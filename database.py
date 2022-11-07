from json import loads, dumps
import sqlite3 as sl
from datetime import datetime
import sys

class DatabaseManager:
    def __init__(self, site) -> None:
        self.settings = loads(open("./db/database_settings.json", "r").read())
        self.connection = sl.connect(f'./db/{site}_database.db')  
        self.check_and_create()
    
    def check_and_create(self) -> None:  
        for key in list(self.settings):
            elements = ", ".join([f"{k} {v}" for k, v in self.settings[key].items()]) 
            self.connection.execute(f"""
                CREATE TABLE IF NOT EXISTS {key} ( 
                    {elements}
                );
            """)
    
    def add_kws(self, kws) -> None: 
        cur = self.connection.cursor()   
        cur.execute(f'INSERT INTO kws_db (kws, add_date, data) values("{kws}", "{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}", "{dumps({})}")')
        self.connection.commit() 

    def add_pid(self, pid) -> None:
        cur = self.connection.cursor()   
        cur.execute(f'INSERT INTO restocks (pid, add_date) values("{pid}", "{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}")')
        self.connection.commit()
    
    def delete_kws(self, kws) -> None: 
        cur = self.connection.cursor()   
        cur.execute(f'DELETE FROM kws_db kws pid="{kws}"') 
        self.connection.commit() 

    def delete_pid(self, pid) -> None:
        cur = self.connection.cursor()    
        cur.execute(f'DELETE FROM restocks WHERE pid="{pid}"')
        self.connection.commit()
        


if __name__ == '__main__': 
    try:
        site = 'Saturn' if sys.argv[1].lower() == "saturn" else "Media"
        mode = sys.argv[2].lower()
        arg = sys.argv[3].split(',')
        remove = "--remove" in sys.argv
    except:
        print("""invalid arguments. Syntax 'py saturn kws "play station 5,iphone 12" """)
    if remove:
        if mode == "kws":
            for k in arg: DatabaseManager(site).delete_kws(k)
        elif mode in ["pid", "pids"]:
            for k in arg: DatabaseManager(site).delete_pid(k)
        else:
            print(f"Invalid mode '{mode}' please select beween pids and kws")
    else:
        if mode == "kws":
            for k in arg: DatabaseManager(site).add_kws(k)
        elif mode in ["pid", "pids"]:
            for k in arg: DatabaseManager(site).add_pid(k)
        else:
            print(f"Invalid mode '{mode}' please select beween pids and kws")