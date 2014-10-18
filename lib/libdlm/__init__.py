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


Motivation
##########


Installation
############


'''

__author__ = 'Jason Unrein'
__copyright__ = 'Copyright 2014'
__credits__ = ['Jason Unrein']
__license__ = 'GPL'
__version__ = '0.0.1'  # project version
__maintainer__ = 'Jason Unrein'
__email__ = 'JasonAUnrein@gmail.com'
__status__ = 'Development'

# Imports #####################################################################
import threading
import time
import logging
from libdlm.file_downloader import FileDownloader


LOG = logging.getLogger(__name__)


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

    def __init__(self, src, dst, cb=None):
        self.src = src
        self.dst = dst
        self.cb = cb
        self.complete = False


###############################################################################
class Downloader(threading.Thread):
    '''
    Threaded File Downloader

    Downloader class - reads queue and downloads each file in succession
    '''

    def __init__(self, id, queue, logger):
        threading.Thread.__init__(self, name=id)
        self.state = States.INIT
        self.id = id
        self.queue = queue
        self.running = True
        self.count = 0
        self.logger = logger

    def run(self):
        self.state = States.RUNNING
        while self.running:
            # gets the url from the queue
            try:
                dlf = self.queue.pop(0)
                self.state = States.DOWNLOADING
            except Exception as err:
                time.sleep(1)
                continue

            # download the file
            LOG.debug('* Thread %d - processing URL: %s to %s' %
                      (threading.current_thread().ident, dlf.src, dlf.dst))
            try:
                downloader = FileDownloader(dlf.src, dlf.dst,
                                            logger=self.logger)
                downloader.download()
                dlf.complete = True
                if dlf.cb:
                    dlf.cb(dlf.src)
                LOG.debug('* Thread %d - download complete' %
                          threading.current_thread().ident)
            except Exception as err:
                LOG.error(err, exc_info=True)
                if dlf.cb:
                    dlf.cb(dlf.src, err)
            self.state = States.RUNNING

        self.state = States.STOPPED

    def pause(self):
        self.running = False
        self.state = States.STOPPING

    def resume(self):
        self.running = True
        self.state = States.RUNNING


###############################################################################
class Settings(object):
    thread_count = 5
    short_name = 'dlm'

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

    def __init__(self, settings=None, logger=None, borg=False):
        global LOG

        self.__dict__ = self.__shared_state
        if borg and self.__shared_state:
            self.__dict__ = self.__shared_state
            return
        elif borg:
            self.__dict__ = self.__shared_state

        self.borg = True
        self.logger_name = logger

        if settings is None:
            self.settings = Settings()
        else:
            self.settings = settings

        # allow one to specify a logging facility or create a new one
        if logger is None:
            LOG = configure_logging(self.settings.short_name)
        else:
            LOG = configure_logging(logger)

        self.ids = range(self.settings.thread_count)
        self.thread_count = self.settings.thread_count
        self.queue = []
        self.threads = []
        for id in self.ids:
            dlt = Downloader(id, self.queue,
                             logger="%s.dlm" % self.logger_name)
            self.threads.append(dlt)
            self.threads[-1].daemon = True
            self.threads[-1].start()

    def append(self, src, dst, cb=None):
        dlf = DownloadFile(src, dst, cb)
        self.queue.append(dlf)
        return dlf

    def pause(self):
        for thread in self.threads:
            thread.pause()

    def resume(self):
        for thread in self.threads:
            thread.resume()

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


def configure_logging(name):
    log = logging.getLogger("%s.dlm" % name)
    return log
