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
'''
try:
    from urllib2 import urlopen, URLError, HTTPError
except ImportError:
    from urllib.request import urlopen
    from urllib.error import URLError, HTTPError
'''
from time import sleep
import logging
from libdlm.file_downloader import FileDownloader


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

    def __init__(self, src, dest):
        self.src = src
        self.dest = dest
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
        self._log = logger
        self.id = id
        self.queue = queue
        self.running = True

    def run(self):
        while self.running:
            self.state = States.RUNNING
            # gets the url from the queue
            try:
                dlf = self.queue.pop(0)
            except:
                sleep(1)
                continue
            if not dlf:
                continue

            # download the file
            self._log.info('* Thread %d - processing URL: %s' %
                           (self.get_ident(), dlf.src))
            try:
                self.state = States.DOWNLOADING
                downloader = FileDownloader(dlf.src, dlf.dst)
                downloader.download()
                dlf.complete = True
                self._log.info('* Thread %d - download complete' %
                               self.get_ident())
            except Exception as err:
                self._log.error(err)

        self.state = States.STOPPED

    def stop(self):
        self.running = False
        self.state = States.STOPPING


###############################################################################
class Settings(object):
    thread_count = 5
    short_name = 'dlm'

    def __init__(self, kwargs=None):
        if kwargs:
            for key, value in kwargs.items():
                setattr(self, key, value)
    pass


###############################################################################
class DownloadManager(object):
    '''
    Spawns downloader threads and manages the URL download queue
    '''
    _shared_state = {}

    def __init__(self, settings=None, logger=None, borg=False):
        if borg and self._shared_state:
            self.__dict__ = self._shared_state
            return
        elif borg:
            self.__dict__ = self._shared_state

        if settings is None:
            self.settings = Settings()
        else:
            self.settings = settings

        # allow one to specify a logging facility or create a new one
        if logger is None:
            self._log = configure_logging(self.settings.short_name)
        else:
            self._log = logger

        self.ids = range(self.settings.thread_count)
        self.thread_count = self.settings.thread_count
        self.queue = []
        self.threads = []
        for id in self.ids:
            thread = Downloader(id, self.queue, logger=self._log)
            thread.daemon = True
            thread.start()
            self.threads.append(thread)

    def append(self, src, dest):
        dlf = DownloadFile(src, dest)
        self.queue.append(dlf)
        return dlf

    def stop(self):
        for thread in self.threads:
            thread.running = False
        for thread in self.threads:
            thread.join()

    def start(self):
        for thread in self.threads:
            thread.running = True
            thread.start()

    def marco(self):
        for thread in self.threads:
            if not thread.running:
                raise Exception
        return "polo"


def configure_logging(name):
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

    # console
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    log.addHandler(console)
    return log


if __name__ == '__main__':
    dlm = DownloadManager()
    dlm.append('http://en.wikipedia.org/wiki/HTTP_403', '.')
    dlm.append('http://en.wikipedia.org/wiki/HTTP_404', '.')
    dlm.append('http://en.wikipedia.org/wiki/HTTP_400', '.')