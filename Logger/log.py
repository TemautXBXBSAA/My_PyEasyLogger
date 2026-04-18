import logging
import typing
import os,sys
import functools

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL



class _SysExcInfoFormatter(logging.Formatter):
    def formatException(self, ei) -> str:
        tb_str = super().formatException(ei)

        border = "=" * 60
        formatted = f"{border}\n{tb_str}\n{border}"
        
        return formatted

class _ColorFormatter(logging.Formatter):
    COLOR = {
        'DEBUG': '\033[0m',
        'INFO': '\033[0;32m',
        'WARNING': '\033[1;33m',
        'ERROR': '\033[1;31m',
        'CRITICAL': '\033[1;35m'
    }
    END = '\033[0m'
    
    def format(self, record):
        super().format(record)
        astime = self.formatTime(record,"%Y-%m-%d %H:%M:%S")
        msg = f"{self.COLOR[record.levelname]}{astime} | {record.levelname:<8} | {record.name}:{record.lineno} -> {record.message}{self.END}"
        if record.exc_info:
            error=self.formatException(record.exc_info)
            msg = msg + '\n\n' + error + '\n'
        return msg
    
    def formatException(self, ei) -> str:
        color = self.COLOR["ERROR"]
        tb_str = super().formatException(ei)
        border = "=" * 60
        formatted = f"{color}{border}\n{tb_str}\n{border}{self.END}"
        
        return formatted

class Logger:
    '''
    Logger:
        Basced on logging module. Improved by color and exc_info.
        For a symple start, just use `logger = Logger()` to create a logger, and use `logger.info("message")` to log.
        You can remove defuault log handler by using `self.removeHandler(self.file_handler / self.stream_handler)` and using `self.addHandler(handler)` to use your own handler.
        If you want to DIY your own Logger, use self.logger.function to modify log style.

    Remember:
        If you want to use your own handler:
          Firstly, using `self.removeHandler(self.file_handler / self.stream_handler)` to remove the default handler.
          Secondly, using `self.addHandler(handler)` to add your own handler.
    '''
    def __init__(self,logger_name = __name__,save_path = "", encoding = "utf-8"):
        self.encoding = encoding
        self.logger = logging.getLogger(logger_name)
        if self.logger.handlers:
            return
        self.logger.setLevel(logging.WARNING)

        if save_path != "":
            if not os.path.exists(os.path.dirname(os.path.abspath(save_path))): 
                os.makedirs(os.path.dirname(os.path.abspath(save_path)))
        
            self.file_handler = logging.FileHandler(save_path,encoding=self.encoding)
            self.file_format = _SysExcInfoFormatter(
                fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d -> %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')

            self.file_handler.setFormatter(self.file_format)
            self.logger.addHandler(self.file_handler)

        self.stream_handler = logging.StreamHandler()
        if sys.stderr.isatty():
            self.stream_format = _ColorFormatter()
        else:
            self.stream_format = logging.Formatter(
                fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d -> %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')
        self.stream_handler.setFormatter(self.stream_format)
        self.logger.addHandler(self.stream_handler)
    
    def set_log_path(self,save_path,encoding = "utf-8"):
        '''
        set_log_path:
            Set log path for logger. if empty, FileHandler will be removed.
        
        :param save_path: Log path.
        '''
        self.encoding = encoding
        if save_path:
            if not os.path.exists(os.path.dirname(os.path.abspath(save_path))): 
                #I think it's bettter to not use try...except. Just let developer know what's wrong.
                os.makedirs(os.path.dirname(os.path.abspath(save_path)))

            if hasattr(self, 'file_handler') and self.file_handler in self.logger.handlers:
                self.logger.removeHandler(self.file_handler)
                self.file_handler.close()

            self.file_handler = logging.FileHandler(save_path,encoding=self.encoding)
            self.file_format = _SysExcInfoFormatter(
                fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d -> %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')
            self.file_handler.setFormatter(self.file_format)
            self.logger.addHandler(self.file_handler)
        else:
            if hasattr(self, 'file_handler') and self.file_handler in self.logger.handlers:
                self.logger.removeHandler(self.file_handler)
                self.file_handler.close()
            else:
                print("[-] FileHandler is not exist.")
    def addHandler(self,handler):
        self.logger.addHandler(handler)
    def removeHandler(self,handler):
        self.logger.removeHandler(handler)
    def addFilter(self,filter_):
        self.logger.addFilter(filter_)
    def removeFilter(self,filter_):
        self.logger.removeFilter(filter_)
    def setLevel(self,level):
        self.logger.setLevel(level)
    def info(self,msg,*args):
        self.logger.info(msg,*args)
    def debug(self,msg,*args):
        self.logger.debug(msg,*args)
    def warning(self,msg,*args):
        self.logger.warning(msg,*args)
    def error(self,msg,*args):
        self.logger.error(msg,*args)
    def critical(self,msg,*args):
        self.logger.critical(msg,*args)
    def log(self,level,msg,*args):
        self.logger.log(level,msg,*args)
    def exception(self,msg,*args):
        self.logger.exception(msg,*args)
    def isEnabledFor(self,level):
        return self.logger.isEnabledFor(level)

auto_logger = Logger()
def add_auto_log(func:typing.Callable):
    '''
    add_auto_log: 
        This is a decorator, will add log for function automatically.
        The Logger is auto created in the module, name `model.auto_logger`, defult log level is `logging.WARNING`.
        If you want to change log leavel, before using this decorator, use `modle.auto_logger.setLevel(level)` to change log level.
        If you want to add/change log path, before using this decorator, use `modle.auto_logger.set_log_path(path)` to change log path.
        But if you want to use your own logger, you can use `modle.auto_logger = YourOwnLogger` to overwrite the auto logger.

    '''
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        auto_logger.info(f"'{func.__name__}' is called.")
        try:
            result = func(*args, **kwargs)
            auto_logger.info(f"'{func.__name__}' is done.")
        except Exception as e:
            auto_logger.exception(f"'{func.__name__}': An error occurred.")
            raise
        return result
    return wrapper
