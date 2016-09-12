#!/usr/bin/python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi


class WebServerHandler(BaseHTTPRequestHandler):

    @classmethod
    def test_Function(self, dbsession):
        print "calling test_Function"
        self.session = dbsession

    def do_GET(self):
        try:
            if self.path.endswith("/hello"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                message = ""
                message += "<html><body>Hello!<form action='/hola' enctype='multipart/form-data' \
                    method=POST><h1>Type something<input name='message' type='text'><input type='submit' value='Submit'/></h1></form></body></html>"
                self.wfile.write(message)
                print message
                self.test_Function()
                return
            if self.path.endswith("/hola"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                message = ""
                message += "<html><body>&#161;Hola! <a href=\"/hello\">Hello again</a></body></html>"
                self.wfile.write(message)
                print message
                return
            if self.path.endswith("/restaurants"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html;charset=utf-8')
                self.end_headers()
                message = ""
                message += "<html><body><h1>List of Restaurants</h1><br><br>"
                message += "<h3><a href='/restaurants/new'>Create new restaurant</a></h3><br><br>"
                restaurants = self.session.query(Restaurant).order_by('Name')
                message += "<form action='/modify' enctype='multipart/form-data' \
                        method=POST>"
                for r in restaurants:
                    #message += "<li>"
                    message += r.name.encode('utf-8')
                    #message += "</li>"
                    message += "<br><button type='submit' name='rename' value='Rename" + str(r.id) + "'>Rename</button><button type='submit' name='delete' value='Delete" + str(r.id) + "'>Delete</button><br>"
                    print r.name
                message += "</form>"
                message += "</body></html>"
                self.wfile.write(message)
                return
            if self.path.endswith("/restaurants/new"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                message = ""
                message += "<html><body><h3>Create new restaurant</h3><br><br>"
                message += "<form action='/restaurants/new' enctype='multipart/form-data' \
                        method=POST>Restaurant name<input name='name' type='text'><input type='submit' value='Submit'/></form></body></html>"
                self.wfile.write(message)
                return
            else:
                raise IOError
        except IOError as error:
            self.send_error(404, 'File Not Found: %s' % self.path)
    def do_POST(self):
        try:
            print "Trying " + str(self.path)
            if self.path.endswith("/hola"):
                self.send_response(301)
                self.end_headers()
                ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    print "Processing form" 
                    fields=cgi.parse_multipart(self.rfile, pdict)
                    messagecontent = fields.get('message')
                output = ""
                output += "<html><body><h2>And here is the response: </h2>" 
                output += "<h1> %s </h1>"  % messagecontent[0]
                self.wfile.write(output)
                return
            if self.path.endswith("/modify"):
                print "Processing button action"
                self.send_response(301)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    print "Processing form"
                    fields=cgi.parse_multipart(self.rfile, pdict)
                    action = str(fields.items()[0][0])
                    print "Processing action: " + action 
                    message =""
                    if action == "rename":
                        messagecontent = fields.get('rename')
                        print "Processing action for " + messagecontent[0]
                        message += "<html><body><h1>Rename a restaurant</h1><br><br>"
                        # trim restaurant id from button value
                        rest_id = messagecontent[0][6:]
                        result = self.session.query(Restaurant).filter(Restaurant.id==rest_id)
                        restaurant = result[0]
                        print "Modifying record for restaurant " + restaurant.name
                        message += "<h3>Renaming " + restaurant.name + "</h3><br>"
                        message += "<form action='/restaurants/renamed' enctype='multipart/form-data' method=POST>\
                                Enter new restaurant name<input name='newName' type='text' value='" + restaurant.name + "'/>\
                                <input type='hidden' name='restaurantId' value='" + rest_id + "'/>\
                                <input type='submit' value='Submit'/></form>"
                    if action == "delete":
                        messagecontent = fields.get('delete')
                        print "Processing action for " + messagecontent[0]
                        message += "<html><body><h1>Delete a restaurant</h1><br><br>"
                        # trim restaurant id from button value
                        rest_id = messagecontent[0][6:]
                        result = self.session.query(Restaurant).filter(Restaurant.id==rest_id)
                        restaurant = result[0]
                        print "Going to delete restaurant " + restaurant.name
                        message += "<h3>Deleting " + restaurant.name + "</h3><br>"
                        message += "<form action='/restaurants/delete' enctype='multipart/form-data' method=POST>\
                                <input type='hidden' name='restaurantId' value='" + rest_id + "' />\
                                Confirm restaurant deletion<input type='submit' value='Confirm' />\
                                </form>"
                        message += "<a href='/restaurants'><button>Cancel and go back</button></a>"
                message += "</body></html>"
                self.wfile.write(message.encode('utf-8'))
                return
            if self.path.endswith("/restaurants/new"):
                self.send_response(301)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                message = ""
                ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields=cgi.parse_multipart(self.rfile, pdict)
                    restaurant_name = fields.get('name')[0]
                    print "Adding " + restaurant_name.decode('utf-8')
                    r = Restaurant(name=restaurant_name.decode('utf-8')) #.encode('utf8'))
                    self.session.add(r)
                    self.session.commit()
                    message+= "<html><body>Restaurant added: " + r.name + "<br><br>"
                    message+= "<a href='/restaurants'><button>Return to restaurant list</button></a></body></html>"
                    self.wfile.write(message.encode('utf-8'))
                return
            if self.path.endswith("/restaurants/renamed"):
                print "Renamed restaurant"
                self.send_response(301)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
                message = ""
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    newRestaurantName = fields.get('newName')[0]
                    rest_id = fields.get('restaurantId')[0]
                    restaurant = self.session.query(Restaurant).filter(Restaurant.id==rest_id)[0]
                    restaurant.name = newRestaurantName.decode('utf-8')
                    self.session.commit()
                    message+= "<html><body>Restaurant name updated to " + restaurant.name + "<br><br>"
                    message+= "<a href='/restaurants'><button>Return to restaurant list</button></a></body></html>"
                    self.wfile.write(message.encode('utf-8'))
                return
            if self.path.endswith("/restaurants/delete"):
                print "Confirm deletion of restaurant"
                self.send_response(301)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
                message = ""
                if ctype == 'multipart/form-data':
                    fields=cgi.parse_multipart(self.rfile, pdict)
                    restaurant_id = fields.get('restaurantId')[0]
                    print "Confirmed deletion for restaurant with id " + restaurant_id
                    restaurant = self.session.query(Restaurant).filter(Restaurant.id==restaurant_id)[0]
                    self.session.delete(restaurant)
                    self.session.commit()
                    print "Restaurant deleted"
                    message+= "<html><body>Restaurant deleted.<br><br>"
                    message+= "<a href='/restaurants'><button>Return to restaurant list</button></a></body></html>"
                    self.wfile.write(message.encode('utf-8'))
                return
        except IOError as error:
            print error.strerror
            self.send_error(404, 'File Not Found: %s' % self.path)
    
def main():

    # setup database
    engine = create_engine('sqlite:///restaurantmenu.db')
    engine.raw_connection().connection.text_factory = str
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    print "Database is ready."

    try:
        port = 8080
        myHandler = WebServerHandler
        myHandler.test_Function(session)
        #customHandler.test_Function(customHandler, session)
   
        server = HTTPServer(('', port), myHandler)
        print "Web Server running on port %s" % port
        server.serve_forever()
    except KeyboardInterrupt:
        print " ^C entered, stopping web server...."
        server.socket.close()
        #print " Closing database connection ..."
        #session.close()

if __name__ == '__main__':
    main()
