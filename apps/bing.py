import json
import random
import time
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from apps.seletask import SeleTask
from settings import BASE_DIR, COOKIE_DIR, MESS_DIR

BING_KEYWORD_DIR = Path(MESS_DIR, 'bingkeywords')
if not BING_KEYWORD_DIR.exists():
    BING_KEYWORD_DIR.mkdir()


class BingTask(SeleTask):
    name = 'BingTask'
    # cookie_file = Path(COOKIE_DIR, self.task_name)

    bing_urls = {
        'domain': 'bing.com',
        'home': 'https://www.bing.com/',
    }

    def get_task_name(self):
        task_name = []
        task_name.append(self.task)
        task_name.append(self.extra.get('username'))
        _config = self.extra.get('config')
        if _config:
            task_name.append(_config)
        if self._config.get('prefs'):
            _proxy = self._config['prefs'].get('network.proxy.socks')
            if _proxy:
                task_name.append(_proxy)
            else:
                task_name.append('noproxy')
        else:
            task_name.append('noproxy')
        task_name = '-'.join(task_name)
        return task_name

    def load_cookie(self):
        cookie_file = Path(COOKIE_DIR, self.task_name)
        if cookie_file.exists():
            with open(cookie_file, mode='r') as fp:
                cookie = json.load(fp)
                for c in cookie:
                    if c.get('domain').startswith('.'):
                        c['domain'] = c['domain'].split('.', 1)[-1]
                    # if c.get('domain') == '.' + self.bing_urls['domain']:
                    #     c['domain'] == self.bing_urls['domain']
                    self.s.driver.add_cookie(c)

    def dump_cookie(self):
        cookie_file = Path(COOKIE_DIR, self.task_name)
        cookie = self.s.driver.get_cookies()
        print(cookie)
        # cookie = [c for c in cookie if self.bing_urls['domain'] in c.get('domain')]
        with open(cookie_file, mode='w') as fp:
            json.dump(cookie, fp)

    def login(self):
        r = 2
        status = 0
        domain = self.bing_urls['domain']
        home = self.bing_urls['home']

        username = self.extra.get('username')
        password = self.extra.get('password')

        if username and password:
            while True:
                try:
                    if domain not in self.s.driver.current_url:
                        self.s.get(home)
                    # id_s = self.s.driver.find_element(By.ID, 'id_s')
                    id_s = self.s.find_element((By.ID, 'id_s'))
                    # if id_s.get_attribute('style') == 'display: none;':
                    if 'none' in id_s.get_attribute('style'):
                        status = 1
                        self.dump_cookie()
                        break
                    self.load_cookie()
                    self.s.get(home)
                    # id_s = self.s.driver.find_element(By.ID, 'id_s')
                    id_s = self.s.find_element((By.ID, 'id_s'))
                    # if id_s.get_attribute('style') == 'display: none;':
                    if 'none' in id_s.get_attribute('style'):
                        status = 1
                        self.dump_cookie()
                        break

                    if r == 0:
                        self.logger.debug('Login error')
                        break
                    id_l = WebDriverWait(self.s.driver, 30).until(EC.element_to_be_clickable((By.ID, 'id_l')))
                    # id_l = self.s.driver.find_element(By.ID, 'id_l')
                    id_l.click()
                    # id_l.send_keys(Keys.RETURN)
                    self.s.clickx(id_l)
                    time.sleep(8)
                    un_input = self.s.find_element((By.NAME, 'loginfmt'))
                    # un_input = self.s.driver.find_element(By.NAME, "loginfmt")
                    self.s.clear(un_input)
                    un_input.send_keys(username)
                    time.sleep(3)
                    # self.s.driver.find_element(By.ID, "idSIButton9").click()
                    self.s.clickx(self.s.driver.find_element(By.ID, "idSIButton9"))
                    time.sleep(5)
                    pw_input = self.s.find_element((By.ID, 'i0118'))
                    # pw_input = self.s.driver.find_element(By.ID, 'i0118')
                    self.s.clear(pw_input)
                    pw_input.send_keys(password)
                    time.sleep(3)
                    # self.s.driver.find_element(By.ID, "idSIButton9").click()
                    self.s.clickx(self.s.driver.find_element(By.ID, "idSIButton9"))
                    r -= 1
                    time.sleep(8)
                except:
                    raise

        return status

    def search(self, query):
        try:
            input_q = self.s.driver.find_element(By.NAME, 'q')
            input_q.clear()
            input_q.send_keys(query)
            time.sleep(1)
            input_q.submit()
        except:
            raise

    def get_queries(self, qs=None, src=None):
        queries = []
        try:
            if qs is None:
                if src is None:
                    src_files = BING_KEYWORD_DIR.rglob('*')
                    src_files = [_ for _ in src_files if _.is_file()]
                    src = random.choice(src_files)
                if src:
                    with open(src, mode='r') as fp:
                        queries = fp.readlines()
            else:
                queries = list(qs)
        except:
            pass
        return queries

    def run(self, close=True):
        # num = 170 / 5 + random.randint(1, 10)
        while True:
            num = random.randint(5, 30)
            try:
                if self.s.driver is None:
                    self.s.start()
                if not self.login():
                    if close:
                        self.s.kill()
                    break

                queries = self.get_queries()
                if not queries:
                    if close:
                        self.s.kill()
                    break
                queries_len = len(queries)
                while True:
                    # for query in queries:
                    if num == 0:
                        break
                    query = queries[random.randint(1, queries_len)]
                    self.search(query)
                    time.sleep(random.randint(10, 60))
                    num -= 1

                duration = random.randint(60 * 60 * 5, 60 * 60 * 18)
                self.logger.debug('Finish, wait %s minutes to continue...', duration / 60)

                # if close:
                #     self.s.kill()
                time.sleep(duration)

            except KeyboardInterrupt:
                if close:
                    self.s.kill()
                self.logger.debug('Exit')
                raise
            except Exception as e:
                self.logger.exception(e)
                self.s.kill()
                time.sleep(360)
