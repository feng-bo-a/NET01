import logging
import os.path
import time

import colorlog

# AP(absolute path)绝对路径
# os.path.realpath(__file__)  # 获取当前.py脚本的绝对完整路径
# os.path.dirname()  # 去掉脚本的文件名返回目录
# os.path.dirname(os.path.realpath(__file__))  # 获取当前.py脚本的绝对路径,并去掉脚本的文件名
# AP = os.path.dirname(os.path.realpath(__file__))  # 创建出保存log的路径 ↓
log_path = os.path.join(os.path.dirname(r'D:\PythonTools\Workspace\Neta_obj\class_tools\log_record'), 'logs')
if not os.path.exists(log_path):  # 判断这个路径是否存在,若不存在则创建一个,
    os.mkdir(log_path)
log_colors_config = {
    'DEBUG': 'white',
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red'
}


class Log:
    def __init__(self):
        # 文件的命名
        self.log_name = os.path.join(log_path, '%s.log' % time.strftime('%Y_%m_%d'))
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        # 日志输出格式
        self.format_console = colorlog.ColoredFormatter(
            '%(log_color)s[%(asctime)s] - %(filename)s]- %(levelname)s: %(message)s', log_colors=log_colors_config)
        self.format_file = logging.Formatter('[%(asctime)s] - %(filename)s] - %(levelname)s: %(message)s')

    def __console(self, level, message):
        # 创建一个FileHandler,用于写到本地
        fh = logging.FileHandler(self.log_name, 'a', encoding='utf-8')  # 这个是PYTHON3,追加模式写法
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(self.format_file)
        self.logger.addHandler(fh)
        # 创建一个StreamHandler,用于输出控制台,
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(self.format_console)
        self.logger.addHandler(ch)
        # 输出到控制台的日志颜色
        if level == 'info':
            self.logger.info(message)
        elif level == 'debug':
            self.logger.debug(message)
        elif level == 'warning':
            self.logger.warning(message)
        elif level == 'error':
            self.logger.error(message)
        # 避免日志重复输出
        self.logger.removeHandler(fh)
        self.logger.removeHandler(ch)
        # 关闭打开的文件
        fh.close()

    def debug(self, message):
        self.__console('debug', message)

    def info(self, message):
        self.__console('info', message)

    def warning(self, message):
        self.__console('warning', message)

    def error(self, message):
        self.__console('error', message)


if __name__ == '__main__':
    log = Log()
    log.info("---测试开始----")
    log.error("测试出现错误")
    log.debug("测试详细情况记录")
    log.warning("这是一条警告信息")
