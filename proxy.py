import os
from flask import Flask, Response
import requests

app = Flask(__name__)

proxies = {
    'http': 'socks5://127.0.0.1:7890',
    'https': 'socks5://127.0.0.1:7890'
}

# 根目录
base_directory = 'your directory'

@app.route('/', methods=['GET'])
def root():
    # 如果URL是根目录，返回指定的字符串，设置Content-Type为text/html
    response_text = '<p style="font-family: Arial;">Pixiv图片反代服务器</p>'
    return Response(response_text, status=200, content_type='text/html;charset=UTF-8')

@app.route('/<path:subpath>', methods=['GET'])
def proxy(subpath):
    # 构建本地文件路径
    local_filename = os.path.join(base_directory, subpath)

    # 检查本地文件是否存在
    if os.path.exists(local_filename):
        # 如果本地文件存在，直接返回本地文件内容
        with open(local_filename, 'rb') as f:
            content = f.read()
        return Response(content, status=200, content_type='image/jpeg')  # 这里的content_type需要根据实际文件类型设置

    # 如果本地文件不存在，发送代理请求，使用SOCKS5代理（127.0.0.1:7890）
    target_url = f'https://i.pximg.net/{subpath}'
    response = requests.get(target_url, headers={
        'Referer': 'https://www.pixiv.net/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
    }, proxies=proxies)

    # 构建响应对象
    flask_response = Response(response.content, status=response.status_code, headers=dict(response.headers))

    # 如果代理请求成功，保存文件到本地目录
    if response.status_code == 200:
        os.makedirs(os.path.dirname(local_filename), exist_ok=True)
        with open(local_filename, 'wb') as f:
            f.write(response.content)

    return flask_response

if __name__ == '__main__':
    app.run(debug=True, port=5001)
