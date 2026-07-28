import os


class StaticFileService():
    def __init__(self, web_dir: str):
        self._web_dir = web_dir


    def serve_index(self):
        index_path = os.path.join(self._web_dir, "index.html")
        if not os.path.exists(index_path):
            raise Exception(f"{index_path} does not exist")
        return open(index_path, "rb")

    def serve_css(self):
        css_path = os.path.join(self._web_dir, "style.css")
        if not os.path.exists(css_path):
            raise Exception(f"{css_path} does not exist")
        return open(css_path, "rb")

    def serve_js(self):
        js_path = os.path.join(self._web_dir, "app.js")
        if not os.path.exists(js_path):
            raise Exception(f"{js_path} does not exist")
        return open(js_path, "rb")


class RAGService():
    def __init__(self, db_conn):
        self.conn = db_conn
