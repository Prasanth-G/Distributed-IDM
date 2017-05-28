
import threading
import re
import http.server
#user defined modules
import slave
import master
class DIDM(object):
    '''Acts both as a server and a client program
       server - always runs on background (helps others to make download request).
       client - send multiple download requests to servers (in other DIDMs) connected to it.
    '''
    def __init__(self):
        self.slave_thread = threading.Thread(target=self.start_slave)
        self.slave_thread.start()
        self.master = None
        self.slave = None

    def create_master(self, url):
        '''Create a master (client side)
        '''
        self.master = master.Master(url)
        self.master.add_device(("127.0.0.1", 8080))

    def start_slave(self):
        '''Create server side
        '''
        self.slave = http.server.HTTPServer(("", 8080), slave.Handler)
        #print("Server On\n")
        self.slave.serve_forever()

    def download(self):
        '''Start downloading file from url
        '''
        self.master.start()

    def wait(self):
        '''wait for a thread
        '''
        self.slave_thread.join()

    def add_device(self, address):
        '''Add a device to which client will send download request
        '''
        self.master.add_device(address)

if __name__ == "__main__":
    print("If u don't want to download wait ...\n")
    didm = DIDM()
    cont = True
    while cont:
        try:
            url = ''
            inp = True
            while not url:
                print("Download link : ", end='')
                url = input()
            didm.create_master(url)
            print("\nEnter addresses of your Neighbour devices (connected to the same network) one by one \nPress ENTER to skip entering address and start download\n")
            while inp:
                while True:
                    inp = input("address ( eg 127.0.0.1:8080 ) : ")
                    ip = re.findall(r"\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}:\d{0,5}", inp)
                    if ip or not inp:
                        break
                    else:
                        print("\n Invalid Input...\n")
                if inp:
                    print(ip)
                    ip = ip[0]
                    ip = ip.split(':')
                    ip = tuple([ip[0], ip[1]])
                    didm.add_device(inp)
            didm.download()
        except:
            print("SOME ERROR OCCURED !!!    TRY AGAIN...\n")

    didm.wait()

#test download links :
#https://maggiemcneill.files.wordpress.com/2012/04/the-complete-sherlock-holmes.pdf"
#"https://www.python.org/ftp/python/3.5.0/python-3.5.0.exe"
