import sqlite3

def initialize_database():
    conn = sqlite3.connect('votes.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            name TEXT PRIMARY KEY,
            vote_count INTEGER NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS user_votes (
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            PRIMARY KEY (user_id, name)
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    initialize_database()
    print("DataBase initialize in succes.")
