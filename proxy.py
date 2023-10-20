import os
from flask import Flask, Response
import requests

app = Flask(__name__)

proxies = {
    'http': 'socks5://%YOUR_SOCKS5_ADDRESS%',
    'https': 'socks5://%YOUR_SOCKS5_ADDRESS%'
}

session = requests.Session()
session.proxies = proxies

base_dir = '%YOUR_SAVE_IMAGE_DIR%'

@app.route('/', methods=['GET'])
def root():
    response_text = '<p style="font-family: Arial;">Pixiv Image</p>'
    return Response(response_text, status=200, content_type='text/html;charset=UTF-8')

@app.route('/<path:path>', methods=['GET'])
def proxy(path):
    if 'user-profile' in path:
        target_url = f'https://i.pximg.net/{path}'
        response = session.get(target_url, headers={
            'Referer': 'https://www.pixiv.net/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
        })
        return Response(response.content, status=response.status_code, headers=dict(response.headers))

    local_file_path = os.path.join(base_dir, path)

    if os.path.exists(local_file_path):
        with open(local_file_path, 'rb') as file:
            return Response(file.read(), status=200, content_type='image/jpeg')

    target_url = f'https://i.pximg.net/{path}'

    try:
        response = session.get(target_url, headers={
            'Referer': 'https://www.pixiv.net/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
        }, timeout=10)

        if response.status_code == 200:
            try:
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                with open(local_file_path, 'wb') as file:
                    file.write(response.content)
            except:
                pass

        flask_response = Response(response.content, status=response.status_code, headers=dict(response.headers))
        return flask_response
    except Exception as e:
        print(f"Error: {e}")
        return Response(status=500)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
