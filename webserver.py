#!/usr/bin/python3
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
                restaurants = session.query(Restaurant).all()
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
                    edit_path = '/restaurants/{}/edit'.format(restaurant.id)
                    del_path = '/resturants/{}/delete'.format(restaurant.id)
                    output += restaurant.name
                    output += '</br>'
                    output += '<a href={}>Edit</a>'.format(edit_path)
                    output += '</br>'
                    output += '<a href={}>Delete</a>'.format(del_path)
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
                    <form method="POST" action="/restaurants/new">
                    <textarea name="message"></textarea>
                    <br>
                    <button type="submit">Create</button>
                    </form>
                    '''
                output += '</body></html>'
                self.wfile.write(output.encode())
                return

            if self.path.endswith('/edit'):
                # Return restaurant id from url
                restaurant_id = self.path.split('/')[2]
                edit_path = '/restaurants/{}/edit'.format(restaurant_id)
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                output = ''
                output += '<html><body>'
                output += '<h3>Rename a restaurant</h3>'
                output += '<form method="POST" action={}>'.format(edit_path)
                output += '''
                    <textarea name="message"></textarea>
                    <br>
                    <button type="submit">Rename</button>
                    </form>
                    '''
                output += '</body></html>'
                self.wfile.write(output.encode())
                return

            if self.path.endswith('/delete'):
                # Return restaurant id from url
                restaurant_id = self.path.split('/')[2]
                del_path = '/restaurants/{}/delete'.format(restaurant_id)
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                output = ''
                output += '<html><body>'
                output += '<h3>Do you really want to delete?</h3>'
                output += '<form method="POST" action={}>'.format(del_path)
                output += '<button type="submit">Delete</button>'
                output += '</form>'
                output += '</body></html>'
                self.wfile.write(output.encode())
                return

        except IOError:
            self.send_error(404, 'File not found {}'.format(self.path))

    def do_POST(self):
        try:
            if self.path.endswith('/restaurants/new'):
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

            if self.path.endswith('/edit'):
                # Return restaurant id from url
                restaurant_id = self.path.split("/")[2]
                # Parse form input
                length = int(self.headers.get('Content-length', 0))
                data = self.rfile.read(length).decode()
                message = parse_qs(data)["message"][0]
                message = message.replace("<", "&lt;")
                # Update row in db
                update_restaurant = session.query(
                    Restaurant).filter_by(id=restaurant_id).one()
                if update_restaurant != []:
                    update_restaurant.name = message
                    session.add(update_restaurant)
                    session.commit()
                    # Redirect to restaurants page
                    self.send_response(303)
                    self.send_header('Content-type', 'text/html')
                    self.send_header('Location', '/restaurants')
                    self.end_headers()
                    return

            if self.path.endswith('/delete'):
                # Return restaurant id from url
                restaurant_id = self.path.split("/")[2]
                # Delete row in db
                del_restaurant = session.query(
                    Restaurant).filter_by(id=restaurant_id).one()
                if del_restaurant != []:
                    session.delete(del_restaurant)
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
