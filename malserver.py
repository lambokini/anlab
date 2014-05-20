import sys
import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import BaseHTTPRequestHandler

import os
import cgi
import logging

logging.basicConfig(level=logging.INFO)

HandlerClass = SimpleHTTPRequestHandler
ServerClass  = BaseHTTPServer.HTTPServer
Protocol     = "HTTP/1.0"



__version__  = '0.0.1'

#This class will handles any incoming request from the browser 
#class MalServerHandler(BaseHTTPRequestHandler):
class MalServerHandler(SimpleHTTPRequestHandler):
	#Handler for the GET requests
	server_version = "MalServer/" + __version__
	sys_version = ''
	def do_GET(self):
		if self.path.startswith('/test'):
			curdir = os.getcwd()
			try:
				#Check the file extension required and
				#set the right mime type
				sendReply = False
				if self.path.endswith(".html"):
					mimetype='text/html'
					sendReply = True
				if self.path.endswith(".jpg"):
					mimetype='image/jpg'
					sendReply = True
				if self.path.endswith(".gif"):
					mimetype='image/gif'
					sendReply = True
				if self.path.endswith(".js"):
					mimetype='application/javascript'
					sendReply = True
				if self.path.endswith(".css"):
					mimetype='text/css'
					sendReply = True

				if sendReply == True:
					#Open the static file requested and send it
					f = open(curdir + os.sep + self.path, 'rb') 
					self.send_response(200)
					self.send_header('Content-type',mimetype)
					self.end_headers()
					self.wfile.write(f.read())
					f.close()
				return


			except IOError:
				self.send_error(404,'File Not Found: %s' % self.path)
		else:
			SimpleHTTPRequestHandler.do_GET(self)
		return
		
	def do_POST(self):
		logging.debug("======= POST STARTED =======")
		#logging.warning(self.headers)
		if 'content-type' in self.headers:
			ctype, pdict = cgi.parse_header(self.headers['content-type'])
			if ctype not in ['application/x-www-form-urlencoded', 'multipart/']:
				self.headers['Content-Type'] = 'application/x-www-form-urlencoded'
		else:
			CONTENT_TYPE = "application/x-www-form-urlencoded"
		
		form = cgi.FieldStorage(
			fp=self.rfile,
			headers=self.headers,
			environ={'REQUEST_METHOD':'POST',
					'CONTENT_TYPE':self.headers['Content-Type'],
					})
		logging.debug("======= POST VALUES =======")
		#print form.value
		
		for item in form.list:
			logging.info(item)
		
		self.send_response(200)
		self.send_header('Content-type','application/xm')
		self.end_headers()
		self.wfile.write("<root><port value='1'/>test</root>")		

def main():
	try:
		#Create a web server and define the handler to manage the
		#incoming request
		if sys.argv[1:]:
			port = int(sys.argv[1])
		else:
			port = 8080	
		
		HandlerClass = MalServerHandler
		server_address = ('0.0.0.0', port)
		HandlerClass.protocol_version = Protocol
		httpd = ServerClass(server_address, HandlerClass)

		sa = httpd.socket.getsockname()
		print "Serving HTTP on", sa[0], "port", sa[1], "..."
		
		#Wait forever for incoming htto requests
		httpd.serve_forever()

	except KeyboardInterrupt:
		print '^C received, shutting down the web server'
		httpd.socket.close()	
	
if __name__ == '__main__':
	#print 
	os.chdir(os.path.join(os.path.dirname(__file__), 'www'))
	main()
	
	
	
	


	