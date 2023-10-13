import os
from flask import Flask, Response
import requests

app = Flask(__name__)

proxies = {
    'http': 'socks5://127.0.0.1:7890',
    'https': 'socks5://127.0.0.1:7890'
}

# 创建持久的Session对象，共享连接池
session = requests.Session()
session.proxies = proxies

# 存储图片的根目录
base_dir = 'your directory'

@app.route('/', methods=['GET'])
def root():
    # 如果URL是根目录，返回指定的字符串，设置Content-Type为text/html
    response_text = '<p style="font-family: Arial;">Pixiv图片反代服务器</p>'
    return Response(response_text, status=200, content_type='text/html;charset=UTF-8')

@app.route('/<path:path>', methods=['GET'])
def proxy(path):
    # 获取本地文件路径
    local_file_path = os.path.join(base_dir, path)

    if os.path.exists(local_file_path):
        # 如果本地文件存在，直接返回本地文件内容
        with open(local_file_path, 'rb') as file:
            return Response(file.read(), status=200, content_type='image/jpeg')  # 请根据实际文件类型设置Content-Type

    # 本地文件不存在，从i.pximg.net获取文件
    target_url = f'https://i.pximg.net/{path}'  # 拼接目标URL，根据请求路径生成目标URL

    try:
        # 发送代理请求，使用共享的Session对象
        response = session.get(target_url, headers={
            'Referer': 'https://www.pixiv.net/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
        }, timeout=10)

        if response.status_code == 200:
            # 保存文件到本地
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            with open(local_file_path, 'wb') as file:
                file.write(response.content)

        # 构建响应对象
        flask_response = Response(response.content, status=response.status_code, headers=dict(response.headers))
        return flask_response
    except Exception as e:
        # 处理异常情况，例如超时等
        print(f"Error: {e}")
        return Response(status=500)

if __name__ == '__main__':
    app.run(debug=True)
