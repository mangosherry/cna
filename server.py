import http.server
import socketserver

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        
        self.send_header("Expires", "Wed, 21 Oct 2015 07:28:00 GMT")
        http.server.SimpleHTTPRequestHandler.end_headers(self)

PORT = 8000
Handler = MyHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("Serving at port", PORT)
    httpd.serve_forever()