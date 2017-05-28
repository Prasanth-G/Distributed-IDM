from urllib.parse import urlparse
import os
import json as json
import http.server
import IDM as IDM

class Handler(http.server.BaseHTTPRequestHandler):
    '''Serve part of a file resquested by the server -by downloading it from the internet
    '''
    askMeEveryRequest = False
    allowNeighDevices = True
    neighbourDevices = {}
    if not os.path.exists("neighbourDevices.dict"):
        open("neighbourDevices.dict", 'w').close()
    else:
        file = open('neighbourDevices.dict')
        data = file.read()
        if data:
            neighbourDevices = json.loads(data)

    def do_GET(self):
        '''To handle GET requests from a server
        '''
        permission = self.ask_permission()
        if permission:
            self.download_file()
        else:
            self.send_response(503)
            self.end_headers()

    def download_file(self):
        '''download the file and send it to master
        '''
        file_name = urlparse(self.path).path.split('/')[-1]
        saveas = self.headers['Range'] + file_name
        folder = str(self.client_address[0])
        if not os.path.exists(str(self.client_address[0])):
            os.mkdir(str(self.client_address[0]))

        idm = IDM.IDM()
        http_headers = {'Range': self.headers['Range']}
        idm.start_download(self.path, headers=http_headers, saveas=saveas, saveto=folder)

        self.send_response(202)
        #sent content-type
        #self.send_header('Content-type', 'jpeg')
        self.end_headers()

        #sent the downloaded file to master
        with open(folder + '\\' + saveas, 'rb') as file:
            self.wfile.write(file.read())

    def ask_permission(self):
        '''Ask the permission from user before download the file (if necessary)
        '''
        #Neighbour client
        if self.client_address[0] in self.neighbourDevices:
            if self.allowNeighDevices:
                return True
            else:
                print("Neighbour         : %s"%self.client_address[0],\
                      "Want to download  : %s"%self.path,\
                      "Headers           : %s"%self.headers,\
                      "\nAllow ? [Y / n]:", sep='\n', end='\t')
                if input().lower() in ['yes', 'y', 'ye']:
                    return True
        #New client
        else:
            print("???????????????????",\
                  "New Device        : %s"%self.client_address[0],\
                  "Want to download  : %s"%self.path,\
                  "Headers           : %s"%self.headers,\
                  "\n1. Allow always ",\
                  "2. Just Once", sep='\n', end='\t')
            result = input()
            if result == '1':
                self.add_neighbour(self.client_address)
                return True
            elif result == '2':
                return True
            else:
                return False

    def add_neighbour(self, address):
        '''Add a Neighbour (so, that the server doesn't ask permission each time for neighbours)
        '''
        self.neighbourDevices[address[0]] = ''
        with open('neighbourDevices.dict', 'w') as file:
            file.write(json.dumps(self.neighbourDevices))

if __name__ == '__main__':
    slave = http.server.HTTPServer(("", 8080), Handler)
    print("Serve On")
    slave.serve_forever()
