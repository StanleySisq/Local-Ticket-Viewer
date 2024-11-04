import sqlite3
from datetime import datetime

def get_db_connection():
    conn = sqlite3.connect('Database.db', timeout=5)  
    conn.row_factory = sqlite3.Row
    return conn

def create_base():
    with get_db_connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            contact TEXT NOT NULL,
            client TEXT NOT NULL,
            gid TEXT NOT NULL,
            visible TEXT NOT NULL,
            mrygacz TEXT NOT NULL,
            uploaded TEXT NOT NULL
        );''')
        conn.commit()

def add_ticket(title, contact, client, gid):
    if not gid:
        gid = "XX1234"

    month_map = {
        "01": "sty", "02": "lut", "03": "mar", "04": "kwi",
        "05": "maj", "06": "cze", "07": "lip", "08": "sie",
        "09": "wrz", "10": "paź", "11": "lis", "12": "gru"
    }

    now = datetime.now()
    hour_minute = now.strftime("%H:%M")  
    day = now.strftime("%d")             
    month_number = now.strftime("%m")    

    month_name = month_map[month_number]

    time = f"{day} {month_name}. {hour_minute}"

    visible = "True"
    mrygacz = "True"

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO tickets (title, contact, client, gid, visible, mrygacz, uploaded) VALUES (?, ?, ?, ?, ?, ?, ?)', 
            (title, contact, client, gid, visible, mrygacz, time)
        )
        conn.commit()
        ticket_id = cursor.lastrowid
        return ticket_id

def update_ticket(ticket_id, title, contact, client, gid, visible):
    if not gid:  
        gid = "XX1234"

    with get_db_connection() as conn:
        conn.execute('''UPDATE tickets SET title = ?, contact = ?, client = ?, gid = ?, visible = ? WHERE id = ?''', 
                     (title, contact, client, gid, visible, ticket_id))
        conn.commit()

def update_ticket_mrygacz(ticket_id, mrygacz_value):
    with get_db_connection() as conn:
        conn.execute('UPDATE tickets SET mrygacz = ? WHERE id = ?', (mrygacz_value, ticket_id))
        conn.commit()

def delete_ticket(ticket_id):
    with get_db_connection() as conn:
        conn.execute('DELETE FROM tickets WHERE id = ?', (ticket_id,))
        conn.commit()

def get_all_tickets():
    with get_db_connection() as conn:
        tickets = conn.execute('SELECT * FROM tickets ORDER BY id ASC').fetchall()
        return tickets

def get_ticket_by_id(ticket_id):
    with get_db_connection() as conn:
        ticket = conn.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,)).fetchone()
        return ticket

def start_log():
    time = datetime.now()
    try:
        with open("logs.txt", "a") as file:
            file.write(f"\n--------------------------------------\nStart {time}")
    except:
        with open("logs.txt", "w") as file:
            file.write(f"\n--------------------------------------\nStart {time}")

def write_log(content):
    time = datetime.now()
    with open("logs.txt", "a") as file:
        file.write(f"\n{time} --- {content}")