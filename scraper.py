from requests import get
from bs4 import BeautifulSoup as bs 

import threading, queue

q = queue.Queue()

class Scraper:
    def __init__(self, size=None, protocol=None, country=None):
        self.size  = size
        self.protocol = protocol
        self.country  = country
        self.proxies  = queue.Queue()

    def parse(self, proxy):
        ip = proxy[0].string
        port = proxy[1].string
        country = proxy[3].string

        if self.country: 
            if country == self.country:
                return ip+':'+port
        else:
            return ip+':'+port

    def fetch(self, url):
        try:
            proxies = bs(get(url).text, 'html.parser').find('tbody').findAll('tr')
        except:
            return
 
        for proxy in proxies:
            data = self.parse(proxy.findAll('td'))
            if data:
                if self.size:
                    if self.proxies.qsize() < self.size:
                        self.proxies.put(data)
                    else:
                        break
                else:
                    self.proxies.put(data)
 
    def get(self):
        if self.protocol :
            if self.protocol.lower() == 'ssl':
                url = 'https://sslproxies.org'
            elif self.protocol.lower() == 'socks':
                url = 'https://socks-proxy.net'
        else:
            url = 'https://free-proxy-list.net'

        self.fetch(url)

        proxies = self.proxies
        self.proxies = queue.Queue()
        return proxies

if __name__ == '__main__':
    q = Scraper().get()
    
    while not q.empty():
        print(q.get())