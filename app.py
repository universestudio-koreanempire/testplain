import os
import sqlite3
from flask import Flask, render_template

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'ranking.db')


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS rankings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            info TEXT NOT NULL,
            status INTEGER NOT NULL UNIQUE CHECK(status IN (1, 2, 3))
        )
        '''
    )

    existing_count = conn.execute('SELECT COUNT(*) FROM rankings').fetchone()[0]

    if existing_count == 0:
        demo_rows = [
            ('1등 예시', '가장 높은 데이터', 1),
            ('2등 예시', '두 번째 데이터', 2),
            ('3등 예시', '세 번째 데이터', 3),
        ]
        conn.executemany(
            'INSERT INTO rankings (name, info, status) VALUES (?, ?, ?)',
            demo_rows,
        )

    conn.commit()
    conn.close()


@app.route('/')
def index():
    conn = get_db_connection()
    rows = conn.execute(
        'SELECT name, info, status FROM rankings WHERE status IN (1, 2, 3) ORDER BY status ASC'
    ).fetchall()
    conn.close()

    ranking_map = {
        1: {'name': '1등 데이터 없음', 'info': 'status=1 데이터를 넣어주세요'},
        2: {'name': '2등 데이터 없음', 'info': 'status=2 데이터를 넣어주세요'},
        3: {'name': '3등 데이터 없음', 'info': 'status=3 데이터를 넣어주세요'},
    }

    for row in rows:
        ranking_map[row['status']] = {
            'name': row['name'],
            'info': row['info'],
        }

    return render_template(
        'index.html',
        first=ranking_map[1],
        second=ranking_map[2],
        third=ranking_map[3],
    )


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
else:
    init_db()
