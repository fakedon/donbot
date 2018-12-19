import time

from apps.seletask import SeleTask


class EmptyTask(SeleTask):

    def get_task_name(self):
        task_name = []
        task_name.append(self.task)
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

    def run(self):

        while True:
            try:
                if self.s.driver is None:
                    self.s.start()
                time.sleep(30)
            except KeyboardInterrupt:
                self.s.kill()
                raise
            except Exception:
                continue
