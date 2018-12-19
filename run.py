import time

import click

from utils.utils import get_config


NOINPUT = 'noinput'


class MyIntParamType(click.ParamType):
    name = 'myinteger'

    def convert(self, value, param, ctx):
        if value in (NOINPUT, ):
            return NOINPUT

        try:
            return int(value)
        except (ValueError, UnicodeError):
            self.fail('%s is not a valid integer' % value, param, ctx)

    def __repr__(self):
        return 'MYINT'


class MyBoolParamType(click.ParamType):
    name = 'myboolean'

    def convert(self, value, param, ctx):
        if isinstance(value, bool):
            return bool(value)
        value = value.lower()
        if value in ('true', 't', '1', 'yes', 'y'):
            return True
        elif value in ('false', 'f', '0', 'no', 'n'):
            return False
        elif value in (NOINPUT, ):
            return NOINPUT
        self.fail('%s is not a valid boolean' % value, param, ctx)

    def __repr__(self):
        return 'MYBOOL'

MYINT = MyIntParamType()
MYBOOL = MyBoolParamType()


def get_config_value(value, key, config, _default=None, default=NOINPUT):
    if value != default:
        value = value
    else:
        _value = None
        if config.get('args'):
            _value = config['args'].get(key)
        if _value is None or _value == '':
            value = _default
        else:
            value = _value
    return value


@click.command()
@click.option('-t', '--task', default=None)
@click.option('-c', '--config', help='config format file, num or file#num')
@click.option('-a', '--auto', type=MYBOOL, default=NOINPUT)
@click.option('-d', '--duration', type=MYINT, default=NOINPUT)
@click.option('-w', '--wait', type=MYINT, default=NOINPUT)
@click.option('-m', '--max_click', type=MYINT, default=NOINPUT)
@click.option('-e', '--skip', default=NOINPUT)
@click.option('-q', '--close', type=MYBOOL, default=NOINPUT)
@click.option('-p', '--cashout', type=MYBOOL, default=NOINPUT)
@click.option('-s', '--solo', type=MYBOOL, default=NOINPUT)
@click.option('-b', '--cron', type=MYBOOL, default=NOINPUT)
def cli(task, config, auto, duration, wait, max_click, skip, close, cashout, solo, cron):
    config = get_config(config=config)
    if task is None:
        task = config.get('task')
    while True:
        try:
            if task == 'empty':
                from apps.empty import EmptyTask
                e = EmptyTask(config=config)
                e.run()
            elif task == 'koinme':
                from apps.koinme import Koinme
                auto = get_config_value(auto, 'auto', config, _default=False)
                k = Koinme(config=config)
                k.koinme(auto=auto)
            elif task == 'ameb':
                from apps.ameb import Ameb
                cron = get_config_value(cron, 'cron', config, _default=False)
                duration = get_config_value(duration, 'duration', config, _default=None)
                wait = get_config_value(wait, 'wait', config, _default=None)
                a = Ameb(config=config)
                a.ameb(cron=cron, duration=duration, wait=wait)
            elif task == 'am_emu':
                from apps.ameb import Ameb
                max_click = get_config_value(max_click, 'max_click', config, _default=None)
                duration = get_config_value(duration, 'duration', config, _default=None)
                skip = get_config_value(skip, 'skip', config, _default=None)
                close = get_config_value(close, 'close', config, _default=False)
                cashout = get_config_value(cashout, 'cashout', config, _default=True)
                a = Ameb(config=config)
                a.am_emu(max_click=max_click, duration=duration, skip=skip, close=close, cashout=cashout)
            elif task == 'eb_emu':
                from apps.ameb import Ameb
                solo = get_config_value(solo, 'solo', config, _default=True)
                close = get_config_value(close, 'close', config, _default=False)
                cron = get_config_value(cron, 'cron', config, _default=False)
                duration = get_config_value(duration, 'duration', config, _default=None)
                a = Ameb(config=config)
                a.eb_emu(solo=solo, close=close, cron=cron, duration=duration)
            elif task == 'ameb_emu':
                from apps.ameb import Ameb
                max_click = get_config_value(max_click, 'max_click', config, _default=None)
                duration = get_config_value(duration, 'duration', config, _default=None)
                skip = get_config_value(skip, 'skip', config, _default=None)
                close = get_config_value(close, 'close', config, _default=False)
                cashout = get_config_value(cashout, 'cashout', config, _default=False)
                a = Ameb(config=config)
                a.ameb_emu(max_click=max_click, duration=duration, skip=skip, close=close, cashout=cashout)
            elif task == 'bing':
                from apps.bing import BingTask
                close = get_config_value(close, 'close', config, _default=True)
                a = BingTask(config)
                a.run(close=close)
        except KeyboardInterrupt:
            break
        except Exception as e:
            # print(e)
            # raise
            time.sleep(60 * 10)


if __name__ == '__main__':
    cli()
