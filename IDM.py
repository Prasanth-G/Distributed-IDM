'''IDM  - Internet Download manager
            - to download files by parts(if server supports)
'''
import math
import os
import threading
import shutil
import re
from random import choice
from string import ascii_letters
from urllib.parse import urlparse
import requests

class IDM():
    '''example:
            import IDM
            i = IDM.idm()             #create an idm object
            i.httpRequest = {'GET':'//download.mp4','Host': 'http://www.example.com'\'Range': 'bytes=0-10'} #set httpRequest
            i.no_of_parts = 12          #set number of parts, the file has to be splited
            i.startDownload()        #start download
    '''
    def __init__(self, no_of_parts=8):
        '''create an idm object
        '''
        self.no_of_parts = no_of_parts
        self.url = None
        self.http_headers = None
        self.response = None
        self._dthreads = []
        self._sthreads = []
        self.file_name = None
        self.folder_name = None

    def start_download(self, url, headers=None, saveas=None, saveto=None):
        '''Start downloading the file from httpRequest
                headers - Optional http Headers
                saveas  - Full path including the file_name
        '''
        self.url = url
        self.response = [None]*self.no_of_parts
        #folder name
        if saveto:
            if not os.path.exists(saveto):
                raise Exception("Folder Specified Not Found", saveto)
            self.folder_name = saveto
        else:
            self.folder_name = ''

        temp_folder = self._randomword()
        while os.path.exists(self.folder_name + temp_folder):
            temp_folder = self._randomword()

        self.folder_name = self.folder_name + "\\" + temp_folder
        os.mkdir(self.folder_name)

        #file name
        if saveas is None:
            self.file_name = urlparse(self.url)[2].split('/')[-1]
        else:
            if os.path.exists(self.folder_name + saveas):
                raise Exception("Invalid File Path")
            self.file_name = saveas

        if headers is None:
            self.http_headers = requests.head(self.url).headers
            from_byte, to_byte = 0, int(self.http_headers['Content-Length'])
        else:
            self.http_headers = headers
            if 'Range' in self.http_headers:
                from_byte, to_byte = list(map(int, re.findall(r'bytes=(\d+)-(\d+)', self.http_headers['Range'])[0]))
            else:
                headers = requests.head(self.url).headers
                from_byte, to_byte = 0, int(self.http_headers['Content-Length'])
        total_size = to_byte - from_byte + 1
        chunk_size = math.ceil(total_size / self.no_of_parts)
        part = 0
        for i in range(from_byte, to_byte+1, chunk_size):
            end = i+chunk_size-1
            if end > to_byte + 1:
                end = to_byte
            headers = {"Range":'bytes=%d-%d'%(i, end)}
            #download file
            thread = threading.Thread(target=self._download, args=(headers, part))
            self._dthreads.append(thread)
            thread.start()
            part = part + 1

        self._wait()
        self._merge()
        self._delete()

    def _randomword(self):
        '''generate random folder name
        '''
        return ''.join(choice(ascii_letters) for i in range(6))

    def _download(self, headers, part):
        '''download the file
        '''
        print(self.url, "Downloading - %s\n"%headers, end='')
        self.response[part] = requests.get(self.url, headers=headers, stream=True)
        with open(self.folder_name + "\\Part_%d"%part, 'wb') as file:
            file.write(self.response[part].content)

    def _wait(self):
        '''wait for threads to complete
        '''
        for dthread in self._dthreads:
            dthread.join()

    def _merge(self):
        '''Merge all the parts into one
        '''
        with open(self.folder_name + "\\" + self.file_name, 'ab') as wfile:
            for i in range(0, self.no_of_parts):
                rfile = open(self.folder_name + "\\Part_%d"%i, 'rb')
                wfile.write(rfile.read())

    def _delete(self):
        '''Cleanup all the junk(temporary) files created
        '''
        saveto = "\\".join(self.folder_name.split("\\")[:-1])
        shutil.copyfile(self.folder_name + "\\" + self.file_name, saveto + "\\" + self.file_name)
        if os.path.exists(self.folder_name):
            shutil.rmtree(self.folder_name)

if __name__ == '__main__':
    idm = IDM()
    idm.start_download(input("URL : "))
