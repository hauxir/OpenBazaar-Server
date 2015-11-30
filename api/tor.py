import requests
import os
import socket
import select
import random
from threading import Thread

##################################################################################################

bazaar_server = "127.0.0.1"
api_port = "18469"

hidden_service_interface = '0.0.0.0'
hidden_service_port = 5000

tor_server = '127.0.0.1'
tor_server_control_port = 9051
tor_server_socks_port = 9050

address = "http://127.0.0.1:18469/api/v1/"

##################################################################################################

class torConnection:
    def connect(self, addr='127.0.0.1', comPort=9051):
        try:
            from stem.control import Controller
        except:
            print "[ERROR] Stem module not installed. Please install stem"
            exit(0)
        self.controller = Controller.from_port(address=addr, port=comPort)
        self.controller.authenticate()
        hidden_service_dir = os.path.join(self.controller.get_conf('DataDirectory', '/tmp'), 'openBazaar')
        self.origConfmap = self.controller.get_conf_map("HiddenServiceOptions")
        self.controller.set_options([
            ('HiddenServiceDir', self.origConfmap["HiddenServiceDir"]),
            ('HiddenServicePort', self.origConfmap["HiddenServicePort"]),
            ('HiddenServiceDir', hidden_service_dir),
            ('HiddenServicePort', "%d %s:%d" % (hidden_service_port, hidden_service_interface, hidden_service_port))
        ])
        result = self.controller.create_hidden_service(hidden_service_dir, 80, target_port=hidden_service_port)
        self.hostname = result.hostname
        if not result.hostname:
            print("[ERROR] Unable to create hidden service")

    def disconnect(self):
        self.controller.set_options([
            ('HiddenServiceDir', self.origConfmap["HiddenServiceDir"]),
            ('HiddenServicePort', self.origConfmap["HiddenServicePort"])
        ])

##################################################################################################

def handleRequest(req):
    type, site, data = req.split("|",3)
    if type == "GET":
        r = requests.get(address + site, params=data)
        return r.json()
    if type == "POST":
        r = requests.post(address + site, params=data)
        return r.json()
    if type == "DELETE":
        r = requests.delete(address + site, params=data)
        return r.json()


##################################################################################################

def startTor():
    torCon = torConnection()
    torCon.connect(tor_server, tor_server_control_port)

    def serverThread(cID, conn, addr, data):
       conn.setblocking(0)
       while True:
           try:
               ready = select.select([conn], [], [], 1.0)
               if ready[0]:
                   data=conn.recv(512)
                   toReturn = handleRequest(data)
                   conn.sendall(str(toReturn))
                   break
           except:
               conn.close()
               print "[ERROR] Error while receiving data"
               raise

    def listenerThread(sock):
        while True:
            try:
               conn, addr = sock.accept()
               cID = random.randint(0, 10000)
               t = Thread(target=serverThread, args=(cID, conn, addr, ""))
               t.daemon = True
               t.start()
            except KeyboardInterrupt:
               exit(0)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.settimeout(None)
    s.bind((hidden_service_interface, hidden_service_port))

    s.listen(1)
    t = Thread(target=listenerThread, args=(s,))
    t.daemon = True
    t.start()

    return torCon.hostname
