import base64
import os
from flask import Flask, abort, render_template, Response
import psycopg
from psycopg.rows import dict_row

app = Flask(__name__)
DATABASE_URL = os.environ.get('DATABASE_URL')


if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL environment variable is required.')


def get_db_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                CREATE TABLE IF NOT EXISTS rankings (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    affiliation TEXT DEFAULT '',
                    career TEXT DEFAULT '',
                    incident TEXT DEFAULT '',
                    status INTEGER NOT NULL UNIQUE CHECK (status IN (1, 2, 3)),
                    photo_data BYTEA,
                    photo_mime_type TEXT DEFAULT 'image/jpeg'
                )
                '''
            )

            cur.execute('SELECT COUNT(*) AS count FROM rankings')
            existing_count = cur.fetchone()['count']

            if existing_count == 0:
                demo_rows = [
                    ('1등 예시', '예시 소속', '예시 경력', '대표 사건 예시', 1, None, 'image/jpeg'),
                    ('2등 예시', '예시 소속', '예시 경력', '대표 사건 예시', 2, None, 'image/jpeg'),
                    ('3등 예시', '예시 소속', '예시 경력', '대표 사건 예시', 3, None, 'image/jpeg'),
                ]
                cur.executemany(
                    '''
                    INSERT INTO rankings (
                        name, affiliation, career, incident, status, photo_data, photo_mime_type
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (status) DO NOTHING
                    ''',
                    demo_rows,
                )

        conn.commit()


def get_rankings():
    ranking_map = {
        1: {
            'name': '1등 데이터 없음',
            'affiliation': '소속 없음',
            'career': '경력 없음',
            'incident': '대표 사건 없음',
            'has_photo': False,
        },
        2: {
            'name': '2등 데이터 없음',
            'affiliation': '소속 없음',
            'career': '경력 없음',
            'incident': '대표 사건 없음',
            'has_photo': False,
        },
        3: {
            'name': '3등 데이터 없음',
            'affiliation': '소속 없음',
            'career': '경력 없음',
            'incident': '대표 사건 없음',
            'has_photo': False,
        },
    }

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT name, affiliation, career, incident, status,
                       photo_data IS NOT NULL AS has_photo
                FROM rankings
                WHERE status IN (1, 2, 3)
                ORDER BY status ASC
                '''
            )
            rows = cur.fetchall()

    for row in rows:
        ranking_map[row['status']] = {
            'name': row['name'],
            'affiliation': row['affiliation'],
            'career': row['career'],
            'incident': row['incident'],
            'has_photo': row['has_photo'],
        }

    return ranking_map


@app.route('/')
def index():
    ranking_map = get_rankings()
    return render_template(
        'index.html',
        first=ranking_map[1],
        second=ranking_map[2],
        third=ranking_map[3],
    )


@app.route('/photo/<int:status>')
def photo(status):
    if status not in (1, 2, 3):
        abort(404)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT photo_data, photo_mime_type
                FROM rankings
                WHERE status = %s
                ''',
                (status,)
            )
            row = cur.fetchone()

    if not row or not row['photo_data']:
        abort(404)

    return Response(row['photo_data'], mimetype=row['photo_mime_type'] or 'image/jpeg')


@app.route('/admin/seed-base64')
def admin_seed_base64_example():
    example_message = (
        '이 경로는 예시 안내용입니다. 자동 수정 로직에서는 base64 문자열을 받아 '\
        'rankings.photo_data(BYTEA)에 저장하면 됩니다.'
    )
    return {'message': example_message}


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
else:
    init_db()
