import math
import urllib.parse
import threading
import os
import requests
import http.client
from queue import Queue

class Master():
    '''Distributes the work among other devices and helps us to download a file concurrently
    '''

    def __init__(self, url):
        self.url = url
        self.jobs = Queue()
        self.no_of_workers = 0
        self.no_of_segments = 8
        self.threads = []
        self.free_workers = set()
        self.chunk_size = 0

    def add_device(self, address):
        '''add devices to share the workload
        '''
        self.free_workers.add(address)
        self.no_of_workers = self.no_of_workers + 1

    def start(self):
        '''start the work
        '''
        headers = requests.head(self.url).headers
        #print(headers)
        total_size = int(headers['Content-Length'])
        self.chunk_size = math.ceil(total_size / self.no_of_segments)

        for i in range(self.no_of_workers):
            thread = threading.Thread(target=self._work)
            thread.start()
            self.threads.append(thread)
        for i in range(0, total_size, self.chunk_size):
            self.jobs.put((i, i+self.chunk_size-1))

        self.jobs.join()
        for i in range(self.no_of_workers):
            self.jobs.put(None)
        for thread in self.threads:
            thread.join()

        self._merge()

    def get_filename(self):
        '''choose where to store the downloaded file
        '''
        p_url = urllib.parse.urlsplit(self.url)
        filename = p_url.path.split('/')[-1]
        if os.path.exists(filename):
            print("\nFilename already Exists !!!\n\n1.Replace file\n2.Rename as (1)%s\n"%filename, end='')
            inp = input()
            if inp == '1':
                open(filename, 'w').close()
            else:
                count = 1
                tempname = '(' + str(count) + ')' + filename
                while os.path.exists(tempname):
                    tempname = '(' + str(count) + ')' + filename
                    count = count + 1
                filename = tempname
        return filename

    def _work(self):
        print("Work started", end='')
        while True:
            job = self.jobs.get()
            if job is None:
                break
            worker = self.free_workers.pop()
            #send request to slave, wait for response
            #if response is negetive task is not done
            connection = http.client.HTTPConnection(worker[0], worker[1])
            headers = {'Range': 'bytes=%d-%d'%job}
            connection.request("GET", self.url, headers=headers)
            response = connection.getresponse()
            #print(response)
            print("STATUS : ", response.status)
            if response.status == 202:
                with open("offset_%d"% (job[0]/self.chunk_size), 'wb') as wfile:
                    while not response.closed:
                        buffer = response.read()
                        if not buffer:
                            break
                        wfile.write(buffer)
                self.jobs.task_done()
                self.free_workers.add(worker)
            else:
                print("Slave %s refused to accept your request")

    def _merge(self):
        filename = self.get_filename()
        with open(filename, 'ab') as wfile:
            for i in range(0, self.no_of_segments):
                rfile = open("offset_%d"%i, 'rb')
                wfile.write(rfile.read())
                rfile.close()
        self._del()

    def _del(self):
        for i in range(0, self.no_of_segments + 1):
            if os.path.exists("offset_%d"%i):
                os.remove("offset_%d"%i)

if __name__ == '__main__':
    download_link = "https://maggiemcneill.files.wordpress.com/2012/04/the-complete-sherlock-holmes.pdf"
    master = Master(download_link)
    master.add_device(("127.0.0.1",8080))
    master.start()
