import datetime
import json
import os
import random
import re
import sys
import time
from pathlib import Path

import arrow
from selenium.common.exceptions import (ElementNotInteractableException,
                                        NoSuchElementException,
                                        NoSuchFrameException,
                                        NoSuchWindowException,
                                        StaleElementReferenceException,
                                        TimeoutException,
                                        UnexpectedAlertPresentException,
                                        WebDriverException)
from selenium.webdriver.common.action_chains import ActionChains as AC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

# sys.path.append(sys.path[0] + "/..")
from apps.seletask import SeleTask, new_windows_opened
from settings import LOG_DIR
from utils.utils import retry


class SkipAdsException(WebDriverException):
    pass


class Ameb(SeleTask):

    am_locators = {
        # 'login': (By.LINK_TEXT, 'Login'),
        'login': (By.XPATH, "//a[@href='sec/login.php']"),
        'username': (By.XPATH, '//input[contains(@placeholder, "Your Email")]'),
        'password': (By.XPATH, '//input[@type="password"]'),
        'go': (By.NAME, 'go'),
        'account': (By.LINK_TEXT, 'Go to my account!'),
        'profile': (By.LINK_TEXT, 'My Profile'),
        'earn': (By.LINK_TEXT, 'Earn Points'),
        'pay': (By.LINK_TEXT, 'Withdraw Money'),
        'request': (By.XPATH, "//a[@href='payout_add.php']"),
        'fall': (By.ID, 'fall'),
        'ads': (By.XPATH, "./li[.//div/a[contains(@onclick, 'open')]]"),
        'ads_sib': (By.XPATH, "./following-sibling::li[.//div/a[contains(@onclick, 'open')]]"),
        'open': (By.XPATH, ".//div[@class='ad adtxt ad-with-border']/div/a[contains(@onclick, 'open')]"),
        'confirm': (By.CLASS_NAME, 'swal2-confirm'),
        'cancel': (By.CLASS_NAME, 'swal2-cancel'),
        'dip': (By.XPATH, "//a[@onclick='dipBabe()']"),
    }

    am_urls = {
        'home': 'https://www.alexamaster.net/',
        'login': 'https://www.alexamaster.net/sec/login.php',
        'account': 'https://www.alexamaster.net/a',
        'profile': 'https://www.alexamaster.net/a/my_profile.php',
        'earn': 'https://www.alexamaster.net/a/earn_points.php',
        'pay': 'https://www.alexamaster.net/a/payout_list.php',
        'surf': 'https://www.alexamaster.net/Master/',
        'register': 'https://www.alexamaster.net/sec/register.php',
        'captcha': 'https://www.alexamaster.net/sec/image.php',
    }

    eb_locators = {
        'username': (By.ID, 'LoginForm_login_name'),
        'password': (By.ID, 'LoginForm_login_password'),
    }

    eb_urls = {
        'login': 'https://www.ebesucher.com/login.html',
        'dashboard': 'https://www.ebesucher.com/login.html',
        'inbox': 'https://www.ebesucher.com/mailviewer.html',
        'surf': 'http://www.ebesucher.com/surfbar/',
        'monitor': 'http://www.ebesucher.com/c/earn-money-mlm?surfForUser=',
    }

    errors = {
        'a': (
            "Can't find ads",
            'Refresh page',
        ),
        'b': (
            'connection refused',
            'Failed to decode response from marionette',
            'Failed to write response to stream',
            'Tried to run command without establishing a connection',
            'No browser exists',
            'Reached error page',
        ),
    }

    def get_task_name(self):
        task_name = []
        task_name.append(self.task)
        if self.task == 'ameb':
            if self.extra.get('eb_url'):
                task_name.append('eb_' + self.extra.get('eb_url'))
            if self.extra.get('am_url'):
                task_name.append('am_' + self.extra.get('am_url'))
        elif self.task == 'am_emu':
            task_name.append(self.extra.get('am_un'))
        elif self.task == 'eb_emu':
            task_name.append(self.extra.get('eb_un'))

        _config = self._config.get('config')
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

    def ameb(self, cron=False, duration=None, wait=None):
        am_url = self.extra.get('am_url')
        if am_url:
            if am_url.startswith(self.am_urls['surf']):
                pass
            else:
                am_url = self.am_urls['surf'] + am_url
        eb_url = self.extra.get('eb_url')
        if eb_url:
            if eb_url.startswith(self.eb_urls['surf']):
                pass
            else:
                eb_url = self.eb_urls['surf'] + eb_url

        if not am_url and not eb_url:
            self.logger.debug('Please set at least one, am_url and eb_url')
            self.logger.debug('Exit')
            self.s.kill()
            sys.exit()
        else:
            _duration = duration
            wait = wait or 180
            eb_handle, am_handle = (None, None)
            r_handles, l_handles = set(), set()
            start_time = datetime.datetime.now()
            _alert_exist = False

            while True:
                try:
                    if _alert_exist:
                        _alert_exist = False
                        self.s.close_alert()
                        continue

                    if self.s.driver is None:
                        self.s.start()
                        start_time = datetime.datetime.now()
                        if _duration is None:
                            duration = random.randint(2 * 60 * 60, 4 * 60 * 60)
                        continue

                    if l_handles:
                        s_handles = l_handles.intersection(set(self.s.driver.window_handles))
                        self.s.close_handles(s_handles, r_handles)
                        self.s.driver.switch_to.window(self.s.driver.window_handles[0])
                    l_handles = set(self.s.driver.window_handles)

                    check_time = datetime.datetime.now()
                    time_passed = check_time - start_time
                    if time_passed.total_seconds() > duration:
                        if cron:
                            self.s.kill()
                            time.sleep(5)
                            break
                        else:
                            self.s.kill()
                            eb_handle, am_handle = (None, None)
                            r_handles, l_handles = set(), set()
                            time.sleep(5)
                            continue

                    try:
                        eb_e = None
                        if eb_url:
                            if eb_handle is None:
                                eb_handle = self.s.driver.current_window_handle

                            if eb_handle:
                                r_handles.add(eb_handle)
                                self.eb_check(eb_url, eb_handle)
                    except Exception as e:
                        eb_e = e

                    try:
                        am_e = None
                        if am_url:
                            if am_handle is None:
                                if eb_url is None:
                                    am_handle = self.s.driver.current_window_handle
                                else:
                                    am_handle = self.s.get_new_window()

                            if am_handle:
                                r_handles.add(am_handle)
                                self.am_check(am_url, am_handle)
                    except Exception as e:
                        am_e = e

                    if eb_e:
                        raise eb_e
                    if am_e:
                        raise am_e

                except KeyboardInterrupt:
                    self.s.kill()
                    self.logger.debug('Exit')
                    raise
                except (ConnectionRefusedError) as e:
                    self.logger.exception(e)
                    time.sleep(5)
                    self.s.kill()
                    eb_handle, am_handle = (None, None)
                    r_handles, l_handles = set(), set()
                    time.sleep(5)
                except UnexpectedAlertPresentException as e:
                    _alert_exist = True
                except (TimeoutException, NoSuchWindowException, WebDriverException) as e:
                    if e.msg in self.errors['b']:
                        self.logger.exception(e)
                        time.sleep(5)
                        self.s.kill()
                        eb_handle, am_handle = (None, None)
                        r_handles, l_handles = set(), set()
                        time.sleep(5)
                        continue
                    else:
                        self.logger.exception(e)
                        time.sleep(5)
                except Exception as e:
                    self.logger.exception(e)
                    time.sleep(5)

                self.logger.debug('wait %s seconds to recheck...', wait)
                time.sleep(wait)

    def ameb2(self, cron=False, duration=None, wait=None):
        am_url = self.extra.get('am_url')
        if am_url:
            if am_url.startswith(self.am_urls['surf']):
                pass
            else:
                am_url = self.am_urls['surf'] + am_url
        eb_url = self.extra.get('eb_url')
        if eb_url:
            m = re.match(r'.*www.ebesucher.com/surfbar/([a-zA-Z0-9_-]+)', eb_url)
            if m:
                eb_monitor = self.eb_urls['monitor'] + m.group(1)
            else:
                eb_monitor = self.eb_urls['monitor'] + eb_url
        if not am_url and not eb_url:
            self.logger.debug('Please set at least one, am_url and eb_url')
            self.logger.debug('Exit')
            self.s.kill()
            sys.exit()
        else:
            _duration = duration
            wait = wait or 180
            eb_handle, am_handle = (None, None)
            r_handles, l_handles = set(), set()
            start_time = datetime.datetime.now()
            _alert_exist = False

            while True:
                try:
                    if _alert_exist:
                        _alert_exist = False
                        self.s.close_alert()
                        continue

                    if self.s.driver is None:
                        self.s.start()
                        start_time = datetime.datetime.now()
                        if _duration is None:
                            duration = random.randint(2 * 60 * 60, 4 * 60 * 60)
                        continue

                    if l_handles:
                        s_handles = l_handles.intersection(set(self.s.driver.window_handles))
                        self.s.close_handles(s_handles, r_handles)
                        self.s.driver.switch_to.window(self.s.driver.window_handles[0])
                    l_handles = set(self.s.driver.window_handles)

                    check_time = datetime.datetime.now()
                    time_passed = check_time - start_time
                    if time_passed.total_seconds() > duration:
                        if cron:
                            self.s.kill()
                            time.sleep(5)
                            break
                        else:
                            self.s.kill()
                            eb_handle, am_handle = (None, None)
                            r_handles, l_handles = set(), set()
                            time.sleep(5)
                            continue
                    try:
                        eb_e = None
                        if eb_url:
                            if eb_handle is None:
                                eb_handle = self.s.driver.current_window_handle

                            if eb_handle:
                                r_handles.add(eb_handle)
                                self.eb_check2(eb_monitor, eb_handle)
                                for h in self.s.driver.window_handles:
                                    self.s.driver.switch_to.window(h)
                                    if 'ebesucher.com' in self.s.driver.current_url:
                                        r_handles.add(h)
                    except Exception as e:
                        eb_e = e

                    try:
                        am_e = None
                        if am_url:
                            if am_handle is None:
                                if eb_url is None:
                                    am_handle = self.s.driver.current_window_handle
                                else:
                                    am_handle = self.s.get_new_window()

                            if am_handle:
                                r_handles.add(am_handle)
                                self.am_check(am_url, am_handle)
                    except Exception as e:
                        am_e = e

                    if eb_e:
                        raise eb_e
                    if am_e:
                        raise am_e

                except KeyboardInterrupt:
                    self.s.kill()
                    self.logger.debug('Exit')
                    raise
                except (ConnectionRefusedError) as e:
                    self.logger.exception(e)
                    time.sleep(5)
                    self.s.kill()
                    eb_handle, am_handle = (None, None)
                    r_handles, l_handles = set(), set()
                    time.sleep(5)
                except UnexpectedAlertPresentException as e:
                    _alert_exist = True
                except (TimeoutException, NoSuchWindowException, WebDriverException) as e:
                    if e.msg in self.errors['b']:
                        self.logger.exception(e)
                        time.sleep(5)
                        self.s.kill()
                        eb_handle, am_handle = (None, None)
                        r_handles, l_handles = set(), set()
                        time.sleep(5)
                        continue
                    else:
                        self.logger.exception(e)
                        time.sleep(5)
                except Exception as e:
                    self.logger.exception(e)
                    time.sleep(5)

                self.logger.debug('wait %s seconds to recheck...', wait)
                time.sleep(wait)

    def eb_check(self, eb_url, eb_handle):
        if eb_handle is None:
            self.logger.debug('eb_handle is None')
            return
        self.s.driver.switch_to.window(eb_handle)
        if eb_url == self.s.driver.current_url:
            retry = 3
            while retry > 0:
                try:
                    self.s.driver.find_element(By.ID, 'surflinkBox')
                    self.logger.debug('Check: eb has surflinkBox')
                    _eb_has_slb = True
                    retry = 0
                except (NoSuchElementException, StaleElementReferenceException, WebDriverException) as e:
                    self.logger.exception(e)
                    retry -= 1
                    time.sleep(10)
                    if retry == 0:
                        self.s.get(eb_url)
                        _eb_has_slb = False
            if _eb_has_slb:
                try:
                    _frame = self.s.driver.find_element(By.ID, 'frame0')
                    self.s.driver.switch_to.frame(_frame)
                    title = self.s.driver.find_element(By.TAG_NAME, 'title')
                    self.logger.debug(title.get_attribute('innerText'))
                    _human = self.s.driver.find_element(By.XPATH, '//input[@value="I am a human!"]')
                    self.logger.debug('Check: eb has robot check!!!')
                    # _human.click()
                    self.s.driver.execute_script("arguments[0].click();", _human)
                    time.sleep(5)
                    self.s.driver.switch_to.default_content()
                    _next = self.s.wait().until(EC.presence_of_element_located((By.XPATH, '//span[@id="skip"]/a')))
                    # _next.click()
                    self.s.driver.execute_script("arguments[0].click();", _next)
                except (NoSuchElementException, TimeoutException, WebDriverException) as e:
                    self.s.driver.switch_to.default_content()
                    self.logger.debug('Check: eb has no robot check')
        else:
            self.logger.debug('Check: eb_url not match, refresh')
            self.s.get(eb_url)
        self.logger.debug('Check: eb_check done')

    def eb_check2(self, eb_monitor, eb_handle):
        if eb_handle is None:
            self.logger.debug('eb_handle is None')
            return
        self.s.driver.switch_to.window(eb_handle)
        if eb_monitor != self.s.driver.current_url:
            self.logger.debug('Check: eb_monitor not match, visit eb_monitor')
            self.s.get(eb_monitor)
            time.sleep(3)
        try:
            surfbar_status_element = self.s.driver.find_element(By.ID, 'surfbar_status')
            if surfbar_status_element.is_displayed():
                surfbar_status = surfbar_status_element.get_attribute('innerText')
                self.logger.debug('surfbar_status: %s', surfbar_status)
            else:
                try:
                    surf_now_button = self.s.driver.find_element(By.ID, 'surf_now_button')
                    self.s.driver.execute_script("arguments[0].click();", surf_now_button)
                except (NoSuchElementException, StaleElementReferenceException) as e:
                    pass
        except (NoSuchElementException, StaleElementReferenceException) as e:
            pass
        self.logger.debug('Check: eb_check done')

    def am_check(self, am_url, am_handle):
        if am_handle is None:
            self.logger.debug('am_handle is None')
            return
        while True:
            self.s.driver.switch_to.window(am_handle)
            if am_url == self.s.driver.current_url:
                if 'alexamaster' not in self.s.driver.page_source:
                    self.logger.debug('Check: am find wait page, refresh in 25 seconds')
                    time.sleep(25)
                    self.s.driver.refresh()
                    continue

                try:
                    self.s.driver.find_element(By.CLASS_NAME, 'swal2-container')
                    self.logger.debug('Check: am find block notice')
                    self.s.get(am_url)
                    continue
                except NoSuchElementException:
                    self.logger.debug('Check: am has no block notice')
                    break
            else:
                self.logger.debug('Check: am_url not match, refresh')
                self.s.get(am_url)
                continue
        self.logger.debug('Check: am_check done')

    def am_register(self):
        self.s.get(self.am_urls['register'])
        first_name = self.s.find_element(By.XPATH, '//input[contains(@placeholder, "Your first name")]')
        surname = self.s.find_element(By.XPATH, '//input[contains(@placeholder, "Your surname")]')
        username = self.s.find_element(By.XPATH, '//input[contains(@placeholder, "Your email address")]')
        password = self.s.find_element(*self.am_lacators['password'])
        self.s.clear(first_name)
        first_name.send_keys(self.extra['am_fn'])
        time.sleep(1)
        self.s.clear(surname)
        surname.send_keys(self.extra['am_sn'])
        time.sleep(1)
        self.s.clear(username)
        username.send_keys(self.extra['am_un'])
        time.sleep(1)
        self.s.clear(password)
        password.send_keys(self.extra['am_pw'])
        checkbox = self.s.find_element(By.XPATH, '//input[@type="password"]')
        checkbox.click()
        time.sleep(3)
        _go = self.s.driver.find_element(*self.am_locators['go'])
        self.s.click(_go)

    def am_login(self):
        self.s.get(self.am_urls['home'])
        try:
            # _login = self.s.find_element(self.am_locators['login'])
            _login = self.s.driver.find_element(*self.am_locators['login'])
            self.s.click(_login)
        except NoSuchElementException:
            self.s.get(self.am_urls['login'])
            time.sleep(2)

        un_input = self.s.find_element(self.am_locators['username'])
        pw_input = self.s.driver.find_element(*self.am_locators['password'])
        self.s.clear(un_input)
        un_input.send_keys(self.extra['am_un'])
        self.s.clear(pw_input)
        pw_input.send_keys(self.extra['am_pw'])
        # pw_input.submit()
        _go = self.s.driver.find_element(*self.am_locators['go'])
        self.s.click(_go)
        time.sleep(3)
        if self.s.driver.current_url == 'https://www.alexamaster.net/sec/loginvalidate.php':
            self.send_tg_msg('please solve login captcha: ' + self.task_name)
            while True:
                # _input = input('Login(Please enter "y" "yes" "ok" "n" "no" or "retry")?')
                # if _input.isalpha():
                #     if _input.lower() in ['y', 'yes', 'ok']:
                #         self.logger.debug('Login success')
                #         break
                #     elif _input.lower() in ['n', 'no']:
                #         self.logger.debug('Login failed')
                #         raise WebDriverException('login failed')
                #     elif _input.lower() in ['retry']:
                #         self.logger.debug('Retry')
                #         time.sleep(10)
                time.sleep(5)
                if self.s.driver.current_url == 'https://www.alexamaster.net/sec/loginconfirm.php':
                    self.logger.debug('Login success')
                    break
        self.s.get(self.am_urls['account'])

    def add_cookie(self):
        cookies = None
        if self.cookie_path.exists():
            with open(self.cookie_path, 'r') as fp:
                try:
                    cookies = json.load(fp)
                except json.JSONDecodeError:
                    self.delete_cookie()
        if cookies:
            for c in cookies:
                if c.get('domain').startswith('.'):
                    c['domain'] = c['domain'].split('.', 1)[-1]
                self.s.driver.add_cookie(c)

    def save_cookie(self):
        cookies = self.s.driver.get_cookies()
        # cookies = [c for c in cookies if 'alexamaster.net' in c.get('domain')]
        with open(self.cookie_path, 'w') as fp:
            try:
                json.dump(cookies, fp)
            except Exception:
                pass

    def am_visite_earn_page(self):
        self.s.get(self.am_urls['earn'])
        time.sleep(5)
        logged = False
        login_action = False
        while not logged:
            if self.s.driver.current_url == self.am_urls['earn']:
                logged = True
                if login_action:
                    self.save_cookie()
            else:
                login_action = False
                self.add_cookie()
                self.s.get(self.am_urls['earn'])
                time.sleep(5)
            if self.s.driver.current_url == self.am_urls['earn']:
                logged = True
            else:
                self.delete_cookie()
                self.am_login()
                login_action = True
                self.s.get(self.am_urls['earn'])
                time.sleep(5)

    def am_get_next_ads(self, ads):
        _tries = 3
        while _tries > 0:
            _tries -= 1
            try:
                self.am_clean_swal2()
                if ads is None:
                    self.am_scroll()
                    time.sleep(5)
                    fall = self.s.driver.find_element(*self.am_locators['fall'])
                    ads = fall.find_element(*self.am_locators['ads'])
                else:
                    ads = ads.find_element(*self.am_locators['ads_sib'])
                ads.location_once_scrolled_into_view
                time.sleep(1)
                break
            except NoSuchElementException:
                if _tries == 0:
                    ads = None
                else:
                    self.am_scroll()

        return ads

    def am_scroll(self):
        self.s.driver.execute_script(
            'var toe = document.getElementById("toe");toe.scrollIntoView({block: "end", behavior: "smooth"});'
        )
        time.sleep(random.randint(5, 8))

    def am_daily_check(self):
        now = datetime.datetime.today()
        check_file_p = Path(LOG_DIR, self.task_name + '_check.json')
        check_file = str(check_file_p)
        date_format = '%Y-%m-%d %H:%M:%S.%f'
        if check_file_p.exists():
            with open(check_file, 'r') as fp:
                last_check = fp.read()
            if not last_check:
                last_check = datetime.datetime(1970, 1, 1)
            else:
                last_check = datetime.datetime.strptime(last_check, date_format)
        else:
            last_check = datetime.datetime(1970, 1, 1)
            with open(check_file, 'w') as fp:
                fp.write(last_check.strftime(date_format))

        if now.date() == last_check.date():
            self.logger.debug('Has checked, try tomorrow.')
            time.sleep(random.randint(1, 5))
        else:
            while True:
                try:
                    if self.am_urls['earn'] not in self.s.driver.current_url:
                        self.am_visite_earn_page()

                    time.sleep(random.randint(3, 5))
                    daily = self.s.driver.find_element(By.XPATH, '//a[contains(@onclick, "dailyBonus")]')
                    daily.location_once_scrolled_into_view
                    self.s.driver.execute_script('dailyBonus(this);')
                    time.sleep(random.randint(3, 5))
                    try_tomorrow = self.s.driver.find_element(By.XPATH, '//h2[@class="swal2-title"]')
                    if 'Wow Amazing!' in try_tomorrow.get_attribute('innerText'):
                        self.s.driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                        last_check = datetime.datetime.today()
                        with open(check_file, 'w') as fp:
                            fp.write(last_check.strftime(date_format))
                        break
                    elif 'Please try again tomorrow!' in try_tomorrow.get_attribute('innerText'):
                        self.s.driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                        self.logger.debug('Please try again tomorrow!')
                        break
                    else:
                        self.am_clean_swal2()
                        break
                except Exception:
                    continue

    def am_get_total_points(self):
        try:
            points = self.s.driver.find_element(By.ID, 'pts-left').get_attribute('innerText')
        except NoSuchElementException:
            points = '0'
        return points

    def am_get_points(self, points):
        plist = points.split('.')[0].split(',')
        plength = len(plist)
        pint = 0
        for i, p in enumerate(plist):
            pint = pint + int(p) * 1000 ** (plength - i - 1)
        return pint

    def am_cashout(self):
        if self.am_urls['earn'] not in self.s.driver.current_url:
            self.am_visite_earn_page()
        points = self.am_get_total_points()
        if self.am_get_points(points) >= 30000:
            self.logger.debug('Request money')
            self.s.driver.find_element(*self.am_locators['pay']).click()
            time.sleep(3)
            try:
                last_pay = self.s.driver.find_element(By.XPATH, '//tbody/tr[1]').get_attribute('innerText')
                self.send_tg_msg('Last pay: %s' % last_pay)
            except Exception:
                pass
            _request = self.s.find_element(self.am_locators['request'])
            _request.click()
            # self.s.driver.find_element_by_link_text('Request').click()
            # card = self.s.driver.find_element(By.CLASS_NAME, 'card')
            card = self.s.find_element((By.CLASS_NAME, 'card'))
            card_head = card.find_element(By.CLASS_NAME, 'card-header')
            if card_head.get_attribute('innerText') == 'You have to satisfy our requirements':
                fail_infos = card.find_elements(
                    By.XPATH, './div[@class="card-content"]//tbody/tr[./td/b[@class="text-danger"]]/td[1]'
                )
                fail_text = [info.get_attribute('innerText') for info in fail_infos]
                self.logger.debug(fail_text)
            elif card_head.get_attribute('innerText') == 'Fill the form carefully':
                _amount = self.am_get_points(points) // 30000
                if _amount > 10:
                    _amount = '10'
                else:
                    _amount = str(_amount)
                newpay1 = card.find_element(By.ID, 'newpay1')
                if self.extra.get('paypal'):
                    newpay1.send_keys(self.extra.get('paypal'))
                newpay2 = Select(card.find_element(By.ID, 'newpay2'))
                newpay2.select_by_value(_amount)
                newpay3 = Select(card.find_element(By.ID, 'newpay3'))
                newpay3.select_by_value('PP')
                newpay4 = card.find_element(By.ID, 'newpay4')
                if not newpay4.is_selected():
                    # newpay4.click()
                    self.s.driver.execute_script("arguments[0].click();", newpay4)
                submit = card.find_element(By.LINK_TEXT, 'Request Now')
                submit.click()
                try:
                    success = self.s.wait().until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'swal2-content'))
                    )
                    if success.get_attribute('innerText') == 'Processed Successfully !!!':
                        self.s.driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                        self.logger.debug('Cash out success.')
                        _date = arrow.now('Asia/Shanghai').date()
                        _msg = '{} {} {} alexamaster.net'.format(_date, self.extra['am_un'], _amount)
                        self.send_tg_msg(_msg)
                    else:
                        self.logger.debug('Cash out failure.')
                except TimeoutException:
                    self.logger.debug('Cash out failure.')
            time.sleep(5)

    def am_clean_swal2(self):
        while True:
            confirm_checked = False
            cancel_checked = False
            try:
                confirm = self.s.driver.find_element(*self.am_locators['confirm'])
            except NoSuchElementException:
                confirm = None
            try:
                cancel = self.s.driver.find_element(*self.am_locators['cancel'])
            except NoSuchElementException:
                cancel = None

            if confirm and confirm.is_displayed() and confirm.is_enabled():
                if confirm.get_attribute('innerText') in ['Quit', 'Good', 'OK']:
                    confirm.click()
            else:
                confirm_checked = True
            if cancel and cancel.is_displayed() and cancel.is_enabled():
                if cancel.get_attribute('innerText') in ['Quit']:
                    cancel.click()
            else:
                cancel_checked = True

            if confirm_checked and cancel_checked:
                break

    def get_color(self, s):
        if s.startswith('#'):
            # s starts with a #.
            r, g, b = int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16)
        elif s.startswith('rgba') or s.startswith('RGBA'):
            rgb = s.split('(')[1].split(')')[0].split(',')[:-1]
            r, g, b = [int(c) for c in rgb]
            # r, g, b, a = [int(c) for c in s.split('(')[1].split(')')[0].split(',')]
        elif s.startswith('rgb') or s.startswith('RGB'):
            r, g, b = [int(c) for c in s.split('(')[1].split(')')[0].split(',')]
        else:
            r, g, b = 255, 255, 255
        return r, g, b

    def get_right_color(self, color, colors):
        mindiff = None
        R, G, B = self.get_color(color)
        for d in colors:
            r, g, b = self.get_color(d)
            diff = abs(R - r) * 256 + abs(G - g) * 256 + abs(B - b) * 256
            if mindiff is None or diff < mindiff:
                mindiff = diff
                mincolorname = d
        return mincolorname[1:]

    def get_ytb_length(self):
        length_element = self.s.driver.find_element(By.CLASS_NAME, 'ytp-time-duration')
        # length = length_element.text
        length = length_element.get_attribute('innerText')
        return length

    def get_right_length(self, length, no=1):
        if no == 1:
            length = length.split(':')
            if len(length) >= 2:
                length = int(length[-2])
            else:
                length = -1
            if length < 0:
                return '6'
            elif length < 5:
                return '0'
            elif length < 10:
                return '1'
            elif length < 15:
                return '2'
            elif length < 25:
                return '3'
            elif length < 45:
                return '4'
            else:
                return '5'
        elif no == 2:
            format_length = ['00', '00', '00']
            split_length = length.split(':')
            r_length = reversed(split_length)
            for i, l in enumerate(r_length):
                if len(l) == 1:
                    l = '0' + l
                format_length[i] = l
            return ':'.join(reversed(format_length))

    def get_right_length_with_options(self, length, options):
        length = self.get_right_length(length, no=2)
        length_t = arrow.get(length, 'HH:mm:ss')
        for i in range(5):
            for option in options:
                value = option.get_attribute("value")
                value_t = arrow.get(value, 'HH:mm:ss')
                if length_t == value_t.shift(seconds=+i):
                    return value
                if length_t == value_t.shift(seconds=-i):
                    return value
        return length

    def get_bgcolor(self):
        # try:
        #     body = self.s.driver.find_element(By.TAG_NAME, 'body')
        # except NoSuchElementException:
        #     try:
        #         _frame = self.s.driver.find_element(By.TAG_NAME, 'frame')
        #         self.s.driver.switch_to.frame(_frame)
        #     except NoSuchElementException:
        #         pass
        # except UnexpectedAlertPresentException:
        #     self.s.driver.switch_to.alert.dismiss()
        #     self.s.driver.switch_to_default_content()

        try:
            body = self.s.driver.find_element(By.TAG_NAME, 'body')
            bgcolor = body.value_of_css_property('background-color')
        except Exception:
            bgcolor = 'rgb(255, 255, 255)'

        return bgcolor

    def login_facebook(self, username, password):
        # fb_un = self.extra.get('fb_un')
        # fb_pw = self.extra.get('fb_pw')
        # if fb_un is None or fb_pw is None:
        #     self.logger.debug('No facebook account login info, please supply them.')
        #     return False
        if not self.s.driver.current_url.startswith('https://www.facebook.com'):
            self.s.get('https://www.facebook.com')
        try:
            un_element = self.s.wait().until(EC.presence_of_element_located((By.ID, 'email')))
            un_element.clear()
            un_element.send_keys(username)
            pw_element = self.s.driver.find_element_by_id('pass')
            pw_element.clear()
            pw_element.send_keys(password)
            pw_element.submit()
            time.sleep(10)
            if 'login_attempt' in self.s.driver.current_url:
                self.logger.debug('Facebook login failed')
                return False
            else:
                self.logger.debug('Facebook login success')
                return True
        except NoSuchElementException:
            self.logger.debug('Already login facebook')
            return True
        except TimeoutException:
            return False

    def am_process_ads(self, ads, skip):
        c_handle = self.s.driver.current_window_handle
        ads_inner = ads.find_element(*self.am_locators['open'])
        _onclick = ads_inner.get_attribute('onclick')
        self.logger.debug(_onclick)

        _handles = [c_handle]
        if 'openSite' in _onclick:
            if 's' in skip:
                self.logger.debug('Skip this site page')
                raise SkipAdsException('Skip ads')
            _tries = 3
            while _tries > 0:
                _tries -= 1
                try:
                    self.s.driver.switch_to.window(c_handle)
                    self.logger.debug('Check swal pop and clean it')
                    self.am_clean_swal2()
                    ads_inner.click()
                    if self.s.wait().until(new_windows_opened(_handles)):
                        _new_open_handles = [h for h in self.s.driver.window_handles if h not in _handles]
                        if len(_new_open_handles) == 0:
                            continue
                        else:
                            _new_handle = _new_open_handles[0]
                    else:
                        continue
                    time.sleep(random.randint(3, 6))
                    self.logger.debug('Switch to new window')
                    while True:
                        try:
                            self.s.driver.switch_to.window(_new_handle)
                            time.sleep(random.randint(20, 30))
                            bgcolor = self.get_bgcolor()
                            break
                        except UnexpectedAlertPresentException:
                            self.s.close_alert()
                    self.logger.debug('Get bgcolor %s, and back to c_handle', bgcolor)
                    self.s.driver.switch_to.window(c_handle)
                    time.sleep(random.randint(3, 6))
                    good = self.s.wait().until(EC.presence_of_element_located(self.am_locators['confirm']))
                    time.sleep(random.randint(3, 6))
                    self.s.wait().until(EC.text_to_be_present_in_element(self.am_locators['confirm'], 'Good'))
                    time.sleep(2)
                    good.click()
                    time.sleep(random.randint(3, 6))
                    color_select = self.s.wait().until(EC.presence_of_element_located((By.ID, 'backcol')))
                    color_select = Select(color_select)
                    color_values = ['#' + c.get_attribute('value') for c in color_select.options]
                    right_color = self.get_right_color(bgcolor, color_values)
                    time.sleep(2)
                    color_select.select_by_value(right_color)
                    time.sleep(1)
                    submit = self.s.driver.find_element(*self.am_locators['confirm'])
                    submit.click()
                    self.logger.debug('Ok, clean mess')
                    self.s.close_handles(self.s.driver.window_handles, exclude=[c_handle])
                    time.sleep(1)
                    self.logger.debug('go to c_handle')
                    self.s.driver.switch_to.window(c_handle)
                except SkipAdsException:
                    raise
                except Exception as e:
                    if _tries == 0:
                        self.logger.debug('Skip this site page')
                        self.s.close_handles(self.s.driver.window_handles, exclude=[c_handle])
                        raise SkipAdsException('Skip ads')
                    self.logger.exception(e)
                    continue
                _tries = 0
        elif 'openVideo' in _onclick:
            if 'v' in skip:
                self.logger.debug('Skip this video page')
                raise SkipAdsException('Skip ads')
            _tries = 3
            while _tries > 0:
                _tries -= 1
                try:
                    self.s.driver.switch_to.window(c_handle)
                    self.logger.debug('Check swal pop and clean it')
                    self.am_clean_swal2()
                    self.s.close_handles(self.s.driver.window_handles, exclude=[c_handle])
                    ads_inner.click()
                    if self.s.wait().until(new_windows_opened(_handles)):
                        _new_open_handles = [h for h in self.s.driver.window_handles if h not in _handles]
                        if len(_new_open_handles) == 0:
                            continue
                        else:
                            _new_handle = _new_open_handles[0]
                    else:
                        continue
                    time.sleep(random.randint(3, 6))
                    self.logger.debug('Switch to new window')
                    self.s.driver.switch_to.window(_new_handle)
                    length = self.get_ytb_length()
                    time.sleep(random.randint(20, 30))
                    self.logger.debug('Get video length %s, and back to c_handle', length)
                    self.s.driver.switch_to.window(c_handle)
                    time.sleep(random.randint(3, 6))
                    length_select = self.s.wait().until(EC.presence_of_element_located((By.ID, 'vlen')))
                    length_select = Select(length_select)
                    try:
                        right_length = self.get_right_length(length, no=1)
                        time.sleep(2)
                        length_select.select_by_value(right_length)
                    except NoSuchElementException:
                        try:
                            right_length = self.get_right_length_with_options(length, length_select.options)
                            time.sleep(2)
                            length_select.select_by_value(right_length)
                        except NoSuchElementException:
                            self.logger.debug('Can\'t get right length.')
                            continue
                    time.sleep(1)
                    length_submit = self.s.driver.find_element(*self.am_locators['confirm'])
                    # length_submit.click()
                    self.s.driver.execute_script("arguments[0].click();", length_submit)
                    time.sleep(random.randint(3, 6))
                    self.logger.debug('Ok, clean mess')
                    self.s.close_handles(self.s.driver.window_handles, exclude=[c_handle])
                    time.sleep(random.randint(2, 4))
                    self.logger.debug('go to c_handle')
                    self.s.driver.switch_to.window(c_handle)
                except SkipAdsException:
                    raise
                except Exception as e:
                    if _tries == 0:
                        self.logger.debug('Skip this video page')
                        self.s.close_handles(self.s.driver.window_handles, exclude=[c_handle])
                        raise SkipAdsException('Skip ads')
                    self.logger.exception(e)
                    continue
                _tries = 0
        elif 'openFanPage' in _onclick:
            if 'f' in skip:
                self.logger.debug('Skip this fan page')
                raise SkipAdsException('Skip ads')
            _tries = 3
            while _tries > 0:
                _tries -= 1
                try:
                    self.s.driver.switch_to.window(c_handle)
                    self.logger.debug('Check swal pop and clean it')
                    self.am_clean_swal2()
                    # ads_inner.click()
                    self.s.driver.execute_script("arguments[0].click();", ads_inner)
                    if self.s.wait().until(new_windows_opened(_handles)):
                        _new_open_handles = [h for h in self.s.driver.window_handles if h not in _handles]
                        if len(_new_open_handles) == 0:
                            continue
                        else:
                            _new_handle = _new_open_handles[0]
                    else:
                        continue
                    self.logger.debug('Switch to new window')
                    self.s.driver.switch_to.window(_new_handle)
                    time.sleep(random.randint(10, 15))
                    self.s.driver.switch_to.window(c_handle)
                    try:
                        fb_frame = self.s.wait().until(
                            EC.frame_to_be_available_and_switch_to_it(
                                (By.XPATH, '//iframe[contains(@title, "fb:like Facebook Social Plugin")]')
                            )
                        )
                    except TimeoutException:
                        self.logger.debug('Skip this fan page')
                        raise SkipAdsException('Skip ads')
                    current_handles = self.s.driver.window_handles

                    try:
                        button = self.s.wait().until(
                            EC.element_to_be_clickable((By.XPATH, '//button[contains(@title, "Page on Facebook")]'))
                        )
                    except NoSuchElementException:
                        self.logger.debug('Skip this fan page')
                        raise SkipAdsException('Skip ads')
                    # self.s.click(button, check=self.s.wait().until(new_windows_opened(current_handles)))
                    button.submit()
                    time.sleep(1)
                    fb_windows_2 = self.s.driver.window_handles
                    self.s.driver.switch_to_window(fb_windows_2[-1])
                    button2 = self.s.wait().until(
                        EC.presence_of_element_located((By.XPATH, '//form//button'))
                    )
                    self.s.click(button2)
                    self.logger.debug('Ok, clean mess')
                    self.s.close_handles(self.s.driver.window_handles, exclude=[c_handle])
                    time.sleep(1)
                    self.logger.debug('go to c_handle')
                    self.s.driver.switch_to.window(c_handle)
                except SkipAdsException:
                    raise
                except Exception as e:
                    if _tries == 0:
                        self.logger.debug('Skip this fan page')
                        self.s.close_handles(self.s.driver.window_handles, exclude=[c_handle])
                        raise SkipAdsException('Skip ads')
                    self.logger.exception(e)
                    continue
                _tries = 0

    def am_raise_webdriver(self, msg):
        raise WebDriverException(msg)

    def br_logger(self):
        _br = '-' * 10
        self.logger.debug(_br)

    def am_emu(self, max_click=None, duration=None, skip=None, close=False, cashout=True):
        click = 0
        c_handle = None
        ads = None
        skip = skip or ''
        new = True
        start = True
        newargs = None
        _refresh = False
        default_args = [click, max_click, c_handle, ads, skip]

        def kill_f():
            self.s.kill()
            c_handle, ads = None, None
            time.sleep(10)
        while True:
            try:
                if self.s.driver is None:
                    self.logger.debug('No browser')
                    self.s.start()

                if start:
                    click, max_click, c_handle, ads, skip = default_args

                if c_handle is None:
                    c_handle = self.s.driver.window_handles[0]
                self.s.driver.switch_to.window(c_handle)

                if start and 'f' not in skip:
                    fb_un = self.extra.get('fb_un')
                    fb_pw = self.extra.get('fb_pw')
                    if fb_un and fb_pw:
                        _fb = self.login_facebook(fb_un, fb_pw)
                        if not _fb:
                            skip = skip + 'f'
                    else:
                        self.logger.debug('No facebook account login info, please supply them.')
                        skip = skip + 'f'

                if duration is None:
                    duration = (3 * 60 * 60) + random.randint(1, 60) * 60

                if max_click is None:
                    # max_click = random.randint(30, 50)
                    max_click = 999
                elif max_click == -1:
                    max_click = random.randint(30, 50)

                if start:
                    if cashout:
                        try:
                            self.am_cashout()
                        except Exception as e:
                            self.logger.exception(e)
                    self.am_daily_check()

                    self.logger.debug(
                        'Task: %s, Click: %s, Max_click: %s, Duration: %s',
                        self.task_name,
                        click,
                        max_click,
                        duration / 60
                    )
                    self.br_logger()

                start = False

                if click == max_click:
                    if close:
                        self.s.kill()
                    start = True
                    self.logger.debug('Finish, wait %s minutes to continue...', duration / 60)
                    time.sleep(duration)
                    continue
                elif click != 0 and click % 20 == 0:
                    time.sleep(random.randint(3, 5))
                    self.logger.debug('Refresh page')
                    _refresh = True
                    ads = None

                if _refresh:
                    self.am_visite_earn_page()
                    _refresh = False

                if self.am_urls['earn'] not in self.s.driver.current_url:
                    self.am_visite_earn_page()

                ads = self.am_get_next_ads(ads)
                if ads is None:
                    self.am_raise_webdriver("Can't find ads")
                ads_point = ads.find_element(By.XPATH, './/h4').get_attribute('innerText')
                if ads_point != '1 Points':
                    self.am_process_ads(ads, skip=skip)
                    click += 1
                    current_points = self.am_get_total_points()
                    self.logger.debug('Click: %s, Points: %s', click, current_points)
                    self.file_logger.info('Points: %s', current_points)
                else:
                    click = max_click

            except (ConnectionRefusedError):
                self.logger.debug('Connection refused error, retry')
                self.s.kill()
                c_handle, ads = None, None
                time.sleep(10)
            except SkipAdsException:
                time.sleep(random.randint(3, 5))
            except StaleElementReferenceException as e:
                self.logger.exception(e)
                ads = None
            except WebDriverException as e:
                if e.msg in self.errors['a']:
                    self.logger.debug('Retry in 5 minutes.')
                    time.sleep(5 * 60)
                    _refresh = True
                    ads = None
                elif e.msg in self.errors['b']:
                    self.logger.debug('Error: %s, retry', e.msg)
                    time.sleep(10)
                    self.s.kill()
                    c_handle, ads = None, None
                    time.sleep(10)
                else:
                    self.logger.exception(e)
                    self.s.kill()
                    c_handle, ads = None, None
                    time.sleep(10)
                    raise
            except KeyboardInterrupt:
                self.logger.debug('quit')
                self.s.kill()
                raise
            except Exception as e:
                self.logger.exception(e)
                self.s.kill()
                c_handle, ads = None, None
                time.sleep(10)
                raise

            self.br_logger()

    def eb_get_info(self):
        try:
            if self.s.driver.current_url != self.eb_urls['login']:
                self.s.get(self.eb_urls['login'])
            info = self.s.driver.find_element(By.ID, 'bonusguthaben')
            if info:
                amount = info.get_attribute('innerText')
                self.logger.debug('!!!Cash: %s', amount)
                _match = re.match('\d+\.\d+', amount)
                if _match:
                    _amount = float(_match.group())
                    if _amount >= 2:
                        _date = arrow.now('Asia/Shanghai').date()
                        _msg = '{} eb_{} {}'.format(_date, self.extra['eb_un'], amount)
                        self.send_tg_msg(_msg)
        except NoSuchElementException:
            pass

    def eb_login(self):
        r = 2
        status = 0
        while True:
            if self.extra['eb_un'] in self.s.driver.page_source:
                status = 1
                break
            try:
                if r == 0:
                    self.logger.debug('Ebesucher login error')
                    break
                self.s.get(self.eb_urls['login'])
                un_input = self.s.driver.find_element(*self.eb_locators['username'])
                pw_input = self.s.driver.find_element(*self.eb_locators['password'])
                self.s.clear(un_input)
                un_input.send_keys(self.extra['eb_un'])
                self.s.clear(pw_input)
                pw_input.send_keys(self.extra['eb_pw'])
                pw_input.submit()
                r -= 1
                time.sleep(5)
            except NoSuchElementException:
                status = 1
                break
        return status

    def eb_get_mails(self):
        mails = None
        while True:
            self.s.get(self.eb_urls['inbox'])
            if not self.eb_login():
                break
            self.s.get(self.eb_urls['inbox'])
            time.sleep(5)

            try:
                hide_button = self.s.driver.find_element(By.ID, 'hide_button')
                if hide_button.get_attribute('innerText') == 'Hide all read emails':
                    # hide_button.click()
                    self.s.driver.execute_script("arguments[0].click();", hide_button)
                    time.sleep(5)
                    continue
                elif hide_button.get_attribute('innerText') == 'Show all read emails':
                    try:
                        entries_select = self.s.driver.find_element(By.NAME, 'example_length')
                        entries_select = Select(entries_select)
                        entries_select.select_by_value('100')
                    except NoSuchElementException:
                        pass
                    except ElementNotInteractableException:
                        break
                    time.sleep(5)
            except NoSuchElementException:
                break

            try:
                example = self.s.find_element((By.ID, 'example'))
                if example.is_displayed():
                    # examples = example.find_elements(By.XPATH, '//tr/td[1]//a')
                    # mails = [mail.get_attribute('href') for mail in examples]
                    mails = example.find_elements(By.XPATH, '//tr/td[1]//a')
                break
            except NoSuchElementException:
                break

        return mails

    def eb_check_mail(self, eb_handle, mail):
        default_handles = self.s.driver.window_handles
        mail_handle = None
        while True:
            try:
                self.s.driver.switch_to.window(eb_handle)
                _windows = self.s.driver.window_handles
                # mail.click()
                self.s.driver.execute_script("arguments[0].click();", mail)
                _new_open_windows = self.s.wait().until(new_windows_opened(_windows))
                time.sleep(5)
                if _new_open_windows:
                    for w in _new_open_windows:
                        self.s.driver.switch_to.window(w)
                        if 'ebesucher.com/showmail.html' in self.s.driver.current_url:
                            mail_handle = self.s.driver.current_window_handle
                            break
                self.s.driver.switch_to.window(mail_handle)
                mail_element = self.s.driver.find_element(By.ID, 'ebesuchermailtextcontainer')
                if 'read and stay on the site for at least' in mail_element.get_attribute('innerText'):
                    self.logger.debug('read and stay on the site')
                    first_link = self.s.find_element((By.XPATH, '//a[contains(@href, "ebesucher.com/mailcheck.php")]'))
                    first_link_target = first_link.get_attribute('target')
                    _windows = self.s.driver.window_handles
                    # first_link.click()
                    self.s.driver.execute_script("arguments[0].click();", first_link)
                    ad_handle = mail_handle
                    if first_link_target == '_blank':
                        _new_open_windows = self.s.wait().until(new_windows_opened(_windows))
                        if _new_open_windows:
                            for w in _new_open_windows:
                                self.s.driver.switch_to.window(w)
                                if 'ebesucher.com/?link=showmail' in self.s.driver.current_url:
                                    ad_handle = self.s.driver.current_window_handle
                                    break
                    self.s.driver.switch_to.window(ad_handle)
                    time.sleep(120)
                elif 'only reading' in mail_element.get_attribute('innerText'):
                    self.logger.debug('only reading')
                    time.sleep(20)

                self.logger.debug('go to deal next mail')
                break

            except Exception as e:
                self.logger.exception(e)
                time.sleep(5)
                break
            finally:
                self.s.close_handles(self.s.driver.window_handles, exclude=default_handles)

    def eb_delete_mail(self):
        style = 'font-weight: bold;'

    def eb_emu(self, solo=True, close=False, cron=False, duration=None):
        if self.extra.get('eb_un') is None or self.extra.get('eb_pw') is None:
            self.logger.debug('Please set eb_un and eb_pw')
            self.logger.debug('eb_emu exit')
            return

        eb_handle = None
        mails = None
        _alert_exist = False
        while True:
            try:
                if _alert_exist:
                        _alert_exist = False
                        self.s.close_alert()
                        continue

                if self.s.driver is None:
                    self.logger.debug('No browser')
                    self.s.start()
                    time.sleep(5)
                    eb_handle = self.s.driver.current_window_handle
                    continue

                if eb_handle is None:
                    eb_handle = self.s.get_new_window()
                    continue

                if mails is None:
                    mails = self.eb_get_mails()

                if mails is None:
                    self.logger.debug('Ebsucher no mails available')
                else:
                    for mail in mails:
                        self.eb_check_mail(eb_handle, mail)
                        time.sleep(5)
                    mails = None
                    self.logger.debug('Ebsucher mail check done')
                if solo:
                    if cron:
                        self.s.kill()
                        eb_handle, mails = (None, None)
                        sys.exit()
                    else:
                        if duration is None:
                            duration = 24 * 60 * 60
                        self.logger.debug('Ebsucher finish, wait %s hours to continue...', duration / 3600)
                        if close:
                            self.s.kill()
                            eb_handle, mails = (None, None)
                        time.sleep(duration)
                else:
                    time.sleep(10)
                    break
            except KeyboardInterrupt:
                if solo:
                    if self.s.driver is None:
                        pass
                    else:
                        self.s.kill()
                        eb_handle, mails = (None, None)
                    self.logger.debug('Exit')
                    raise
                else:
                    raise
            except (ConnectionRefusedError) as e:
                self.logger.exception(e)
                time.sleep(5)
                self.s.kill()
                eb_handle, mails = (None, None)
                time.sleep(5)
            except UnexpectedAlertPresentException as e:
                _alert_exist = True
                time.sleep(5)
            except (TimeoutException, NoSuchWindowException, WebDriverException) as e:
                if e.msg in self.errors['b']:
                    self.logger.exception(e)
                    time.sleep(5)
                    self.s.kill()
                    eb_handle, mails = (None, None)
                    time.sleep(5)
                    continue
                else:
                    self.logger.exception(e)
                    time.sleep(5)
            except Exception as e:
                self.logger.exception(e)
                if solo:
                    time.sleep(5)
                    self.s.kill()
                    eb_handle, mails = (None, None)
                    time.sleep(5)
                continue

    def ameb_emu(self, max_click=None, duration=None, skip=None, close=False, cashout=True):
        click = 0
        c_handle = None
        ads = None
        skip = skip or ''
        new = True
        start = True
        newargs = None
        _refresh = False
        while True:
            try:
                if new:
                    newargs = [click, max_click, c_handle, ads, skip]
                    new = False

                if self.s.driver is None:
                    self.logger.debug('No browser')
                    self.s.start()

                if start:
                    click, max_click, c_handle, ads, skip = newargs

                if c_handle is None:
                    c_handle = self.s.driver.window_handles[0]
                self.s.driver.switch_to.window(c_handle)

                if start and 'f' not in skip:
                    fb_un = self.extra.get('fb_un')
                    fb_pw = self.extra.get('fb_pw')
                    if fb_un and fb_pw:
                        _fb = self.login_facebook(fb_un, fb_pw)
                        if not _fb:
                            skip = skip + 'f'
                    else:
                        self.logger.debug('No facebook account login info, please supply them.')
                        skip = skip + 'f'

                if duration is None:
                    duration = (3 * 60 * 60) + random.randint(1, 60) * 60

                if max_click is None:
                    # max_click = random.randint(30, 50)
                    max_click = 999
                elif max_click == -1:
                    max_click = random.randint(30, 50)

                if start:
                    if cashout:
                        self.am_cashout()
                    self.am_daily_check()

                    self.logger.debug(
                        'Task: %s, Click: %s, Max_click: %s, Duration: %s',
                        self.task_name,
                        click,
                        max_click,
                        duration / 60
                    )
                    self.br_logger()

                start = False

                if click == max_click:
                    try:
                        self.eb_emu(solo=False, close=False, cron=False, duration=None)
                    except Exception:
                        pass
                    if close:
                        self.s.kill()
                    start = True
                    self.logger.debug('Finish, wait %s minutes to continue...', duration / 60)
                    time.sleep(duration)
                    # time.sleep(10)
                elif click % 20 == 0:
                    time.sleep(random.randint(3, 5))
                    self.logger.debug('Refresh page')
                    _refresh = True
                    ads = None

                if _refresh:
                    self.am_visite_earn_page()
                    _refresh = False

                if self.am_urls['earn'] not in self.s.driver.current_url:
                    self.am_visite_earn_page()

                ads = self.am_get_next_ads(ads)
                if ads is None:
                    self.am_raise_webdriver("Can't find ads")
                ads_point = ads.find_element(By.XPATH, './/h4').get_attribute('innerText')
                if ads_point != '1 Points':
                    self.am_process_ads(ads, skip=skip)
                    click += 1
                    current_points = self.am_get_total_points()
                    self.logger.debug('Click: %s, Points: %s', click, current_points)
                    self.file_logger.info('Points: %s', current_points)
                else:
                    click = max_click

            except KeyboardInterrupt:
                self.s.kill()
                raise
            except (ConnectionRefusedError):
                self.logger.debug('Connection refused error, retry')
                time.sleep(10)
                self.s.kill()
                c_handle, ads = None, None
                time.sleep(10)
            except SkipAdsException:
                time.sleep(random.randint(3, 5))
            except StaleElementReferenceException as e:
                self.logger.exception(e)
                ads = None
            except WebDriverException as e:
                if e.msg in self.errors['a']:
                    self.logger.debug('Retry in 5 minutes.')
                    time.sleep(5 * 60)
                    _refresh = True
                    ads = None
                elif e.msg in self.errors['b']:
                    self.logger.debug('Error: %s, retry', e.msg)
                    time.sleep(10)
                    self.s.kill()
                    c_handle, ads = None, None
                    time.sleep(10)
                else:
                    self.logger.exception(e)
                    raise
            except Exception as e:
                self.logger.exception(e)
                raise

            self.br_logger()
