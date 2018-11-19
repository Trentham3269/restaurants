from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Restaurant, Base, MenuItem
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs


# Create db session
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


class webserverHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path.endswith('/restaurants'):
                restaurants = session.query(Restaurant.name).all()
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                output = ''
                output += '<html><body>'
                output += '''
                    <a href='/restaurants/new'>
                    <h3>Create a new restaurant</h3>
                    </a>
                    '''
                for restaurant in restaurants:
                    output += restaurant.name
                    output += '</br>'
                    output += '<a href=#>Edit</a>'
                    output += '</br>'
                    output += '<a href=#>Delete</a>'
                    output += '</br></br>'
                output += '</body></html>'
                self.wfile.write(output.encode())
                return

            if self.path.endswith('/restaurants/new'):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                output = ''
                output += '<html><body>'
                output += '''
                    <h3>Create a new restaurant</h3>
                    <form method="POST" action="/restaurants">
                    <textarea name="message"></textarea>
                    <br>
                    <button type="submit">Create</button>
                    </form>'''
                output += '</body></html>'
                self.wfile.write(output.encode())
                return

        except IOError:
            self.send_error(404, 'File not found {}'.format(self.path))

    def do_POST(self):
        try:
            # Parse form input
            length = int(self.headers.get('Content-length', 0))
            data = self.rfile.read(length).decode()
            message = parse_qs(data)["message"][0]
            message = message.replace("<", "&lt;")
            # Insert row in db
            new_restaurant = Restaurant(name=message)
            session.add(new_restaurant)
            session.commit()
            # Redirect to restaurants page
            self.send_response(303)
            self.send_header('Content-type', 'text/html')
            self.send_header('Location', '/restaurants')
            self.end_headers()
            return

        except IOError:
            pass


def main():
    try:
        port = 8080
        server = HTTPServer(('', port), webserverHandler)
        print('Web server running on port {}'.format(port))
        server.serve_forever()

    except KeyboardInterrupt:
        print(' entered, stopping web server...')
        server.socket.close()


if __name__ == '__main__':
    main()
