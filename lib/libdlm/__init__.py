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
import os
import threading
#from ._json import JSON
from urllib2 import urlopen, URLError, HTTPError
import time
from time import sleep
import logging
import thread
from libdlm.file_downloader import FileDownloader

###############################################################################
class Downloader(threading.Thread):
    '''
    Threaded File Downloader
    
    Downloader class - reads queue and downloads each file in succession
    '''

    def __init__(self, id, queue, logger):
        threading.Thread.__init__(self,name=id)
        self._log = logger
        self.id = id
        self.queue = queue
        self.running = True

    def run(self):
        while self.running:
            # gets the url from the queue
            try:
                src, dst = self.queue.pop(0)
            except:
                sleep(1)
                continue
            if not src:
                continue

            # download the file
            self._log.info('* Thread %d - processing URL: %s' % (thread.get_ident(), src))
            try:
                downloader = FileDownloader(src, dst)
                downloader.download()
                self._log.info('* Thread %d - download complete' % thread.get_ident())
            except Exception as err:
                self._log.error(err)
            # self.download_file(src, dst)

    def stop(self):
        self.running = False

    def download_file(self, src, dst):
        t_start = time.clock()

        try:
            src_file = urlopen(src)
            dst_name = os.path.join(dst, os.path.basename(src))
            with open(dst_name, 'wb') as dst_file:
                dst_file.write(src_file.read())
            t_elapsed = time.clock() - t_start
            self._log.info('* Thread %d: Downloaded %s in %d seconds' % (thread.get_ident(), src, t_elapsed))
        except HTTPError, e:
            self._log.info('* Thread %d - HTTP Error: %d - %s' % (thread.get_ident(), e.code, src))
        except URLError, e:
            self._log.info('* Thread %d - URL Error: %s - %s' % (thread.get_ident(), e.reason, src))


###############################################################################
class DownloadManager():
    '''
    Spawns dowloader threads and manages URL downloads queue
    '''

    def __init__(self, thread_count=10, logger=None):
        # allow one to specify a logging facility or create a new one
        if logger is None:
            self._log = configure_logging('dlm')
        else:
            self._log = logger
            
        self._log.info('starting')
        self.ids = range(thread_count)
        self.thread_count = thread_count
        self.queue = []
        for id in self.ids:
            thread = Downloader(id, self.queue, logger=self._log)
            thread.daemon = True
            thread.start()

    def append(self, src, dest):
        self.queue.append((src, dest))


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

    sleep(60000)