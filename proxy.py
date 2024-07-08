import os
import sqlite3
import logging
from flask import Flask, Response
import requests
from threading import Lock

app = Flask(__name__)

proxies = {
    'http': 'REPLACE WITH YOUR PROXY ADDRESS(SOCKS4/5 OR HTTP)',
    'https': 'REPLACE WITH YOUR PROXY ADDRESS(SOCKS4/5 OR HTTPS)'
}

session = requests.Session()
session.proxies = proxies

base_dir = 'REPLACE WITH YOUR STORAGE PATH'

logging.basicConfig(level=logging.INFO)

db_lock = Lock()

def get_db_connection():
    conn = sqlite3.connect('image_paths.db', check_same_thread=False)
    cursor = conn.cursor()
    return conn, cursor

conn, cursor = get_db_connection()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS image_paths (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT UNIQUE NOT NULL,
        local_path TEXT NOT NULL
    )
''')
conn.commit()
conn.close()

@app.route('/', methods=['GET'])
def root():
    response_text = '<p style="font-family: Arial;">Pixiv image proxy & backup v1.0.2</p>'
    return Response(response_text, status=200, content_type='text/html;charset=UTF-8')

@app.route('/<path:path>', methods=['GET'])
def proxy(path):
    conn = None
    try:
        if path == 'favicon.ico':
            return Response("Not Found", status=404)

        conn, cursor = get_db_connection()
        
        if 'user-profile' in path:
            target_url = f'https://i.pximg.net/{path}'
            response = session.get(target_url, headers={
                'Referer': 'https://www.pixiv.net/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
            })
            return Response(response.content, status=response.status_code, headers=dict(response.headers))

        with db_lock:
            cursor.execute('SELECT local_path FROM image_paths WHERE path=?', (path,))
            result = cursor.fetchone()

        if result:
            local_file_path = result[0]
            if os.path.exists(local_file_path):
                with open(local_file_path, 'rb') as file:
                    return Response(file.read(), status=200, content_type='image/jpeg')

        target_url = f'https://i.pximg.net/{path}'

        response = session.get(target_url, headers={
            'Referer': 'https://www.pixiv.net/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
        }, timeout=10)

        if response.status_code == 200:
            file_name = os.path.basename(path)
            local_file_path = os.path.join(base_dir, file_name)
            try:
                with open(local_file_path, 'wb') as file:
                    file.write(response.content)
                with db_lock:
                    cursor.execute('INSERT INTO image_paths (path, local_path) VALUES (?, ?)', (path, local_file_path))
                    conn.commit()
            except Exception as file_error:
                logging.error(f"Failed to save file: {file_error}")

        flask_response = Response(response.content, status=response.status_code, headers=dict(response.headers))
        return flask_response

    except requests.RequestException as request_error:
        logging.error(f"Request error: {request_error}")
        return Response("Error fetching image", status=500)

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return Response("Internal server error", status=500)

    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5181, threaded=True)
