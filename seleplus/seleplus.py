import random
import os
import socket
import sys
import time
import uuid
from copy import deepcopy
from pathlib import Path

import psutil

from selenium import webdriver
from selenium.common.exceptions import (NoSuchWindowException, WebDriverException, NoAlertPresentException)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# sys.path.append(sys.path[0] + "/..")
from utils.utils import retry
from settings import LOG_DIR

try:
    import http.client as http_client
except ImportError:
    import httplib as http_client


class FirefoxPlus(object):

    def __init__(self, config=None):
        self._config = deepcopy(config)
        self.config = None
        self.driver, self.profile, self.process, self.browser, self.processes = self.init_attrs()

    def init_attrs(self):
        return None, None, None, None, None

    def get_default_driver_args(self):
        return {
            'firefox_profile': None,
            'firefox_binary': None,
            'timeout': 30,
            'capabilities': None,
            'proxy': None,
            'executable_path': "geckodriver",
            'firefox_options': None,
            'log_path': str(Path(LOG_DIR, "geckodriver.log")),
        }

    def get_default_fp_args(self):
        return {
            'browser.link.open_newwindow': 3,
            # 'privacy.history.custom': True,
            'browser.privatebrowsing.autostart': True,
            'dom.disable_open_during_load': False,
            'network.IDN_show_punycode': True,
            'extensions.pocket.enabled': False,
            'extensions.screenshots.disabled': True,
            'extensions.screenshots.system-disabled': True,
            'media.block-autoplay-until-in-foreground': True,
            'media.autoplay.enabled': False,
            'browser.tabs.insertRelatedAfterCurrent': True,
            'browser.tabs.closeWindowWithLastTab': False,
            'browser.sessionstore.restore_pinned_tabs_on_demand': False,
            'toolkit.cosmeticAnimations.enabled': False,
            'full-screen-api.transition-duration.enter': '0 0',
            'full-screen-api.transition-duration.leave': '0 0',
            'browser.sessionhistory.max_entries': 1,
            'browser.sessionhistory.max_total_viewers': 1,
            'browser.sessionstore.resume_from_crash': False,
            'memory.free_dirty_pages': True,
            'dom.allow_scripts_to_close_windows': True,
            'dom.disable_beforeunload': True,
            'xpinstall.signatures.required': False,
            'browser.cache.disk.enable': False,
            'browser.cache.memory.enable': False,
            'dom.webnotifications.enabled': False,
            'dom.push.enabled': False,
            'browser.cache.memory.capacity': 0,
            'browser.cache.disk.capacity': 0,
            'dom.max_script_run_time': 0,
            'dom.max_chrome_script_run_time': 0,
            'privacy.trackingprotection.pbmode.enabled': False,
            # "media.peerconnection.enabled": False,
        }

    def update_config(self):
        if self.config is None:
            self.config = {}
            self.config['driver'] = self.get_default_driver_args()
            self.config['prefs'] = self.get_default_fp_args()
            if self._config is not None:
                temp = self._config['driver']
                if 'log_path' not in temp.keys():
                    temp['log_path'] = str(Path(LOG_DIR, 'gechodriver-' + self._config['task_name'] + '.log'))
                self.config['driver'].update(temp)

                temp = self._config['prefs']
                self.config['prefs'].update(temp)

        if not isinstance(self.profile, FirefoxProfile):
            self.set_prefs(self.config['prefs'])

        self.config['driver']['firefox_profile'] = self.profile

    def start(self):
        self.update_config()
        self.driver = webdriver.Firefox(**self.config['driver'])
        self.driver.set_window_size(1024, 768)
        # self.driver.maximize_window()
        self.driver.implicitly_wait(10)
        self.profile = self.driver.profile
        self.process = psutil.Process(self.driver.service.process.pid)
        self.browser, self.processes = self.get_processes()

    def restart(self):
        self.kill(profile_persist=True)
        time.sleep(5)
        self.start()

    def get_processes(self):
        ps_children = self.process.children()
        browser = None
        for p in ps_children:
            if 'firefox' in p.name():
                browser = p
                break
        if browser is None:
            raise WebDriverException('No browser exists')
        ps_children.append(self.process)
        return browser, ps_children

    def set_prefs(self, prefs):
        if not isinstance(prefs, dict):
            raise TypeError('Prefs must be dict.')
        if self.driver is not None:
            ac = ActionChains(self.driver)
            ac.key_down(Keys.SHIFT).send_keys(Keys.F2).key_up(Keys.SHIFT).perform()
            time.sleep(0.1)  # this seems to be necessary
            for name, value in prefs.items():
                pref = 'pref set {name} {value}'.format(name=name, value=value)
                ac.send_keys(pref).perform()
                ac.send_keys(Keys.ENTER).perform()
            ac.key_down(Keys.SHIFT).send_keys(Keys.F2).key_up(Keys.SHIFT).perform()
        elif self.driver is None:
            if self.profile is None:
                self.profile = webdriver.FirefoxProfile()
            self.profile.DEFAULT_PREFERENCES['frozen'].update(prefs)

    def set_pref(self, name, value):
        if self.driver is not None:
            ac = ActionChains(self.driver)
            ac.key_down(Keys.SHIFT).send_keys(Keys.F2).key_up(Keys.SHIFT).perform()
            time.sleep(0.1)  # this seems to be necessary
            pref = 'pref set {name} {value}'.format(name=name, value=value)
            ac.send_keys(pref).perform()
            ac.send_keys(Keys.ENTER).perform()
            ac.key_down(Keys.SHIFT).send_keys(Keys.F2).key_up(Keys.SHIFT).perform()
        elif self.driver is None:
            if self.profile is None:
                self.profile = webdriver.FirefoxProfile()
            self.profile.DEFAULT_PREFERENCES['frozen'][name] = value

    # def setProxyWithAuth(self, proxy):
    #     # The addon does not work with the latest firefox
    #     # proxy = {'host': HOST, 'port': PORT, 'usr': USER, 'pwd': PASSWD}
    #     self.profile.add_extension('https://addons.mozilla.org/firefox/downloads/latest/close-proxy-authentication/addon-427702-latest.xpi')
    #     self.set_pref('network.proxy.type', 1)
    #     self.set_pref('network.proxy.http', proxy['host'])
    #     self.set_pref('network.proxy.http_port', int(proxy['port']))
    #     # ... ssl, socks, ftp ...
    #     self.set_pref('network.proxy.no_proxies_on', 'localhost, 127.0.0.1')

    #     credentials = '{usr}:{pwd}'.format(**proxy)
    #     credentials = b64encode(credentials.encode('ascii')).decode('utf-8')
    #     self.set_pref('extensions.closeproxyauth.authtoken', credentials)

    def wait(self, timeout=0):
        if timeout == 0:
            timeout = random.randint(25, 30)
        return WebDriverWait(self.driver, timeout)

    def close_alert(self):
        toggle = True
        while True:
            try:
                if toggle:
                    self.driver.switch_to.alert.dismiss()
                else:
                    self.driver.switch_to.alert.accept()
            except NoAlertPresentException:
                break
            time.sleep(5)
            toggle = not toggle
            self.driver.switch_to_default_content()
        self.driver.switch_to_default_content()

    def close_handles(self, handles, exclude=None):
        if exclude is None:
            exclude = set()
        elif isinstance(exclude, (list, set, tuple)):
            exclude = set(exclude)
        else:
            raise TypeError('exclude must be list, set or tuple.')
        for w in set(handles).difference(exclude):
            if w in exclude:
                continue
            try:
                self.driver.switch_to.window(w)
                self.driver.close()
                time.sleep(2)
            except NoSuchWindowException:
                pass

    def get_new_window(self, switch_to=True):
        _windows = self.driver.window_handles
        _handle = None
        self.driver.execute_script('window.open("", "blank");')
        _new_open_windows = self.wait().until(new_windows_opened(_windows))
        if _new_open_windows:
            for w in _new_open_windows:
                self.driver.switch_to.window(w)
                if self.driver.current_url == 'about:blank':
                    _handle = self.driver.current_window_handle
                    break
        if _handle is not None and switch_to:
            self.driver.switch_to.window(_handle)
        return _handle

    def get(self, url, retry_=0, max_retry=3):
        try:
            self.driver.implicitly_wait(10)
            self.driver.get(url)
        except Exception:
            if retry_ > max_retry:
                retry_ = 0
                raise
            else:
                retry_ += 1
                time.sleep(1)
                self.get(url, retry_=retry_)

    def clickx(self, element):
        self.driver.execute_script("arguments[0].click();", element)

    @retry()
    def click(self, element, by=0, check=None):
        '''Click with retry.

        :param check
        :type check: int
        :example check: lambda: self.wait().util(EC.new_window_is_opened())
        '''
        self.click_by(element, by=by)
        # if check is None or not callable(check):
        #     raise TypeError('check must be callable.')
        if callable(check):
            check()
        # self.wait().util(EC.new_window_is_opened())

    def click_by(self, element, by=0):
        bys = list(range(0, 3))
        if by not in bys:
            by = random.choice(bys)

        if by == 0:
            element.click()
        elif by == 1:
            element.send_keys(Keys.RETURN)
        elif by == 2:
            element.send_keys(Keys.ENTER)
        else:
            element.click()

    def find_element(self, locator):
        return self.wait().until(EC.presence_of_element_located(locator))

    def clear(self, element):
        value = element.get_attribute('value')
        if len(value) > 0:
            for _ in value:
                element.send_keys(Keys.BACK_SPACE)

    def kill(self, profile_persist=False):
        try:
            if profile_persist:
                try:
                    RemoteWebDriver.quit(self.profile)
                except (http_client.BadStatusLine, socket.error):
                    pass

                if self.profile.w3c:
                    self.profile.service.stop()
                else:
                    self.profile.binary.kill()
            else:
                self.driver.quit()
        except Exception:
            pass
        finally:
            if self.processes:
                for p in self.processes:
                    try:
                        p.kill()
                    except psutil.NoSuchProcess:
                        pass
            try:
                os.remove(self.config['driver']['log_path'])
            except Exception:
                pass
            if profile_persist:
                self.driver, self.process, self.browser, self.processes = None, None, None, None
            else:
                self.driver, self.profile, self.process, self.browser, self.processes = self.init_attrs()


class new_windows_opened(object):

    def __init__(self, current_handles):
        self.current_handles = current_handles

    def __call__(self, driver):
        return list(set(driver.window_handles) - set(self.current_handles))
