import logging
import os
import json
from copy import deepcopy
from pathlib import Path

from logzero import setup_logger

import sys
# sys.path.append(sys.path[0] + "/..")

from settings import COOKIE_DIR
from seleplus.seleplus import LOG_DIR, FirefoxPlus, new_windows_opened


class SeleTask(object):

    name = 'SeleTask'

    def __init__(self, config):
        self._config = deepcopy(config)
        self.task = config['task']
        self.extra = config.get('extra', {})
        self.task_name = self.get_task_name()

        self.logger = self.get_logger()
        self.file_logger = self.get_file_logger()

        self.s_config = {}
        self.s_config['task_name'] = self.task_name
        self.s_config['driver'] = config.get('driver', {})
        self.s_config['prefs'] = config.get('prefs', {})
        self.s = FirefoxPlus(self.s_config)
        self.cookie_path = Path(COOKIE_DIR, self.task_name)

    def get_task_name(self):
        task_name = self.task
        return task_name

    def get_logger(self):
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logger = setup_logger(self.task_name, formatter=formatter)
        logger.setLevel(logging.DEBUG)

        return logger

    def get_file_logger(self):
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
        file_logger = setup_logger(
            self.task_name + '_file',
            logfile=str(Path(LOG_DIR, self.task_name + '.log')),
            level=logging.INFO,
            formatter=formatter,
            fileLoglevel=logging.INFO
        )

        return file_logger

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
        with open(self.cookie_path, 'w') as fp:
            try:
                json.dump(cookies, fp)
            except Exception:
                pass

    def delete_cookie(self):
        try:
            os.remove(self.cookie_path)
        except:
            pass
