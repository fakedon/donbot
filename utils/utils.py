from functools import wraps
import time
import json
from pathlib import Path

from settings import CFG_DIR, CFG_File


def get_config(config=None):
    config_file = None
    config_key = None
    if config is None:
        config_file = CFG_File
    else:
        config_list = config.split('#')
        if len(config_list) < 1:
            raise Exception('config is empty!')

        first = config_list[0]
        if len(config_list) == 1:
            first = Path(first)
            if first.exists():
                config_file = first
            elif Path(CFG_DIR, first).exists():
                config_file = Path(CFG_DIR, first)
            else:
                config_file = CFG_File
                config_key = first
        else:
            first = Path(first)
            if first.exists():
                config_file = first

            elif Path(CFG_DIR, first).exists():
                config_file = Path(CFG_DIR, first)
            else:
                raise Exception('config file not exists')
            config_key = config_list[1]
    with open(str(config_file), 'r') as fp:
        c = json.load(fp)
        
    if config_key:
        try:
            c = c[str(config_key)]
        except (KeyError):
            raise Exception('config not found')
    task = c.get('task')
    if task is None:
        for k, v in c.items():
            task = v.get('task')
            if task is not None:
                config_key = k
                c = v
                break
        if task is None:
            raise Exception('config not found')

    if config_key:
        c['config'] = '%s@%s' % (config_file.name, config_key)
    else:
        c['config'] = config_file.name
    return c


def retry(ExceptionToCheck=Exception, tries=3, delay=2, backoff=2, logger=None, hook=None, allfailcb=None):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param ExceptionToCheck: the exception to check. may be a tuple of
        exceptions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """
    if backoff < 1:
        raise ValueError("backoff must be greater than 0")
    tries = int(tries)
    if tries < 0:
        raise ValueError("tries must be 0 or greater")
    if delay <= 0:
        raise ValueError("delay must be greater than 0")

    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 0:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    if callable(hook):
                        hook()
                    mtries -= 1
                    mdelay *= backoff
                    if mtries == 0:
                        if allfailcb is None:
                            raise
                        if not callable(allfailcb):
                            raise TypeError('check must be callable.')
                        allfailcb()
            # return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry
