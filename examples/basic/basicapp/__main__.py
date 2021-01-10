from wsgiref.simple_server import make_server

from . import configure

config = configure()
with make_server("", 8000, config.make_wsgi_app()) as httpd:
    print("Serving on port 8000...")
    httpd.serve_forever()
