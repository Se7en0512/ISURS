import threading
import os
import webview
from app import app

flask_url = 'http://127.0.0.1:5000'
icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'icon.ico')


def start_flask():
    try:
        from waitress import serve
        serve(app, host='127.0.0.1', port=5000, threads=8)
    except ImportError:
        app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)


class Api:
    def export(self, endpoint, filename):
        with app.test_client() as c:
            resp = c.get(endpoint)
            if resp.status_code != 200:
                return False
            dl_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
            os.makedirs(dl_dir, exist_ok=True)
            path = os.path.join(dl_dir, filename)
            with open(path, 'wb') as f:
                f.write(resp.data)
            os.startfile(path)
            return True


if __name__ == '__main__':
    api = Api()
    t = threading.Thread(target=start_flask, daemon=True)
    t.start()
    webview.create_window(
        'PULSE - Hospital Asset & Supply Management System',
        flask_url,
        width=1280,
        height=800,
        resizable=True,
        min_size=(960, 600),
        js_api=api,
    )
    webview.start(gui='edgechromium', icon=icon_path)
