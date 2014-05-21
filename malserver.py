import sys
import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

import os
import cgi
import logging
import mimetypes

logging.basicConfig(level=logging.DEBUG)

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
	
	def __init__(self, request, client_address, server):
		SimpleHTTPRequestHandler.__init__(self, request, client_address, server)
		
		
	def setup(self):	
		SimpleHTTPRequestHandler.setup(self)
		self.webroot = os.getcwd()
		logging.debug('webroot:%s' % self.webroot)
		
	def do_GET(self):
		if self.path.startswith('/res'):
			try:
				resource = self.get_resource(self.path)
				if resource:
					self.send_file(resource)
				else:
					self.send_error(404,'File Not Found: %s' % self.path)
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
		
		resource = self.get_resource('/res/baby.mp4')
		if resource:
			self.send_file(resource)
		return 
		
		self.send_response(200)
		self.send_header('Content-type','application/xm')
		self.end_headers()
		self.wfile.write("<root><port value='1'/>test</root>")		
	
	def get_resource(self, rpath):
		if rpath[0] == '/' or rpath[0] == '\\':
			rpath = rpath[1:]
		fpath = os.path.join(self.webroot,  rpath)
		fpath = os.path.abspath(fpath)
		if fpath.startswith(self.webroot):
			return fpath
		else:
			return None
			
	@staticmethod
	def get_content_type(filename):
		return mimetypes.guess_type(filename)[0] or 'application/octet-stream'
	
	def send_file(self, file):
		statinfo = os.stat(file)
		size = statinfo.st_size
		f = open(file, 'rb') 
		self.send_response(200)
		self.send_header('Content-type', MalServerHandler.get_content_type(file))
		self.send_header('Content-Length', size)

		self.end_headers()
		self.wfile.write(f.read())
		f.close()	
		
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
		print "Serving HTTP on", sa[0], "port", sa[1], "...\nWebroot:", os.getcwd()
		
		#Wait forever for incoming htto requests
		httpd.serve_forever()

	except KeyboardInterrupt:
		print '^C received, shutting down the web server'
		httpd.socket.close()	
	
if __name__ == '__main__':
	dirname = os.path.dirname(__file__)
	if dirname == "":
		dirname = os.path.dirname(os.path.abspath(__file__))
	#print dirname
	os.chdir(os.path.join(dirname, 'www'))
	main()
	
	
	
	


	