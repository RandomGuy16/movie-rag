import os


class StaticFileService:
    """Service responsible for serving the page static files."""

    def __init__(self, web_dir: str):
        self._web_dir = web_dir

    def serve_index(self) -> str:
        index_path = os.path.join(self._web_dir, "index.html")
        if not os.path.exists(index_path):
            raise Exception(f"{index_path} does not exist")
        return index_path

    def serve_css(self) -> str:
        css_path = os.path.join(self._web_dir, "style.css")
        if not os.path.exists(css_path):
            raise Exception(f"{css_path} does not exist")
        return css_path

    def serve_js(self) -> str:
        js_path = os.path.join(self._web_dir, "app.js")
        if not os.path.exists(js_path):
            raise Exception(f"{js_path} does not exist")
        return js_path
