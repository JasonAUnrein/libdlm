#!/usr/bin/env python
'''
Synopsis
########

Libdlm is a library and application for managing downloads.  The intent is to
provide a simple API that allows developers to quickly add a concurrent and
restartable download manager to an application.  There should be hooks to not
only start/stop/restart downloads but also receive download status updates such
as complete and X% done.

Future versions enhancements could include support for different download
methods such as jigdo and torrents.

This is package will provide a minimalistic CLI interface as a proof of concept
and for testing purposes.  It should remain a small and light weight package
that makes it easy to incorporate into other projects

*Note*: The basis of this was forked/lifted from ade@pipe-devnull.com
http://pipe-devnull.com/2012/09/13/queued-threaded-http-downloader-in-python.html

Code Example
############


'''

__version__ = '0.0.3'  # project version

# Imports #####################################################################
import threading
import time
import logging
from libdlm.file_downloader import FileDownloader


DEBUG = False
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
LOG.propagate = False
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
LOG.addHandler(console_handler)


###############################################################################
def debugger(func):
    '''decorator to add/remove wrapper debug prints'''
    def func_wrapper(*args, **kwargs):
        global DEBUG, LOG
        rtn = None
        if DEBUG:
            LOG.debug('Entered %s' % func.__name__)
        try:
            rtn = func(*args, **kwargs)
        except Exception as err:
            LOG.debug('Exception %s' % err, exc_info=True)
            raise
        if DEBUG:
            LOG.debug('Left %s' % func.__name__)
        return rtn

    return func_wrapper


###############################################################################
class States(object):
    STOPPED = 0
    DOWNLOADING = 1
    RUNNING = 2
    PAUSED = 3
    INIT = 4
    STOPPING = 5


###############################################################################
class DownloadFile(object):
    '''
    Represents the file being downloaded and maintains the information for
    both the user and the library
    '''

    @debugger
    def __init__(self, src, dst, username=None, password=None, cb=None):
        self.src = src
        self.dst = dst
        self.username = username
        self.password = password
        self.cb = cb
        self.complete = False


###############################################################################
class Downloader(threading.Thread):
    '''
    Threaded File Downloader

    Downloader class - reads queue and downloads each file in succession
    '''

    @debugger
    def __init__(self, id, queue, logger):
        threading.Thread.__init__(self, name=id)
        self.state = States.INIT
        self.id = id
        self.queue = queue
        self.running = True
        self.count = 0
        self.logger_name = "%s.%s" % (logger, 'downloader')
        self.log = logging.getLogger(self.logger_name)
        self.transition_to = States.RUNNING

    @debugger
    def run(self):
        while self.running:
            if self.transition_to == States.PAUSED:
                self.state = States.PAUSED
                while self.transition_to == States.PAUSED:
                    time.sleep(1)

            self.state = States.RUNNING
            # gets the url from the queue
            try:
                dlf = self.queue.pop(0)
            except Exception as err:
                time.sleep(1)
                continue
            if not dlf:
                continue

            # download the file
            self.log.debug('* Thread %d - processing URL: %s to %s' %
                           (threading.current_thread().ident, dlf.src, dlf.dst))
            try:
                self.state = States.DOWNLOADING
                downloader = FileDownloader(dlf.src, dlf.dst,
                                            username=dlf.username,
                                            password=dlf.password,
                                            logger=self.logger_name)
                downloader.download()
                dlf.complete = True
                if dlf.cb:
                    dlf.cb(dlf.src)
                self.log.debug('* Thread %d - download complete' %
                               threading.current_thread().ident)
            except Exception as err:
                self.log.error(str(err))
                if callable(dlf.cb):
                    try:
                        dlf.cb(dlf.src, err)
                    except Exception as err2:
                        self.log.error(str(err2), exc_info=True)
                        raise

        self.state = States.STOPPED

    @debugger
    def stop(self):
        self.running = False
        self.state = States.STOPPING

    @debugger
    def pause(self):
        self.transition_to = States.PAUSED


###############################################################################
class Settings(object):
    thread_count = 5
    short_name = 'dlm'

    @debugger
    def __init__(self, kwargs=None):
        if kwargs:
            for key, value in kwargs.items():
                setattr(self, key, value)


###############################################################################
class DownloadManager(object):
    '''
    Spawns downloader threads and manages the URL download queue
    '''
    __shared_state = {}

    @classmethod
    def reset_borg(cls):
        cls.__shared_state = {}

    @debugger
    def __init__(self, settings=None, logger=None, borg=False):
        global LOG
        self.__dict__ = self.__shared_state
        if borg and self.__shared_state:
            self.__dict__ = self.__shared_state
            return
        elif borg:
            self.__dict__ = self.__shared_state
            self.borg = True

        if settings is None:
            self.settings = Settings()
        else:
            self.settings = settings

        if logger is not None:
            LOG = logging.getLogger("%s.%s" % (logger, self.settings.short_name))
            self.logger_name = "%s.%s" % (logger, self.settings.short_name)
        else:
            LOG = logging.getLogger(self.settings.short_name)
            self.logger_name = self.settings.short_name
            LOG.setLevel(logging.DEBUG)
            LOG.propagate = False
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            LOG.addHandler(console_handler)

        self.ids = range(self.settings.thread_count)
        self.thread_count = self.settings.thread_count
        self.queue = []
        self.threads = []
        for id in self.ids:
            self.threads.append(Downloader(id, self.queue,
                                logger=self.logger_name))
            self.threads[-1].daemon = True
            self.threads[-1].start()

    @debugger
    def append(self, src, dst, cb=None, username=None, password=None):
        dlf = DownloadFile(src, dst, username, password, cb)
        self.queue.append(dlf)
        return dlf

    @debugger
    def pause(self):
        for thread in self.threads:
            thread.pause()

    @debugger
    def stop(self):
        for thread in self.threads:
            thread.running = False
        for thread in self.threads:
            thread.join()

    @debugger
    def start(self):
        for thread in self.threads:
            thread.running = True
            thread.start()

    @debugger
    def marco(self):
        for thread in self.threads:
            if not thread.running:
                raise Exception
        return "polo"

    def is_busy(self):
        if len(self.queue) != 0:
            return True

        for thread in self.threads:
            if thread.state == States.DOWNLOADING:
                return True

        return False
