import sqlite3

def initialize_database():
    conn = sqlite3.connect('sizes.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS sizes
             (name TEXT PRIMARY KEY, size INTEGER)''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    initialize_database()
    print("Size dataBase initialize in succes.")
