import logging
from logging import handlers
from datetime import datetime
import os


class Logger(object):

    def __init__(self, logname, level='info', fmt='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s'):
        self.level_relations = {'debug': logging.DEBUG, 'info': logging.INFO, 'warning': logging.WARNING, 'error': logging.ERROR, 'crit': logging.CRITICAL}  #日志级别关系映射

        self.logger = logging.getLogger(logname)
        now = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        format_str = logging.Formatter(fmt)
        self.logger.setLevel(self.level_relations[level])

        self.console = logging.StreamHandler()  # console out
        self.console.setFormatter(format_str)

        self.filehandler = logging.FileHandler(f'./Logs/{logname}.log', encoding='utf-8')
        self.filehandler.setFormatter(format_str)

        self.logger.addHandler(self.filehandler)
        self.logger.addHandler(self.console)
    