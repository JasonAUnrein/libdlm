'''
Downloads a standard file from http or ftp locations.

Original Author: Joshua Banton
Original GitHub: https://github.com/bantonj/fileDownloader
'''

import ftplib
import logging
import os
import urllib
import urllib2
import urlparse
import socket
from furl import furl


class FileDownloader(object):
    '''
    This class is used for downloading files from the internet via http or ftp.
    It supports basic http authentication and ftp accounts, and supports
    resuming downloads.  It does not support https or sftp at this time.

    The main advantage of this class is it's ease of use, and pure pythoness.

    #####
    If a non-standard port is needed just include it in the url
    (http://example.com:7632).

    Basic usage:
    >>> downloader = FileDownloader('http://example.com/file.zip')
    >>> downloader.download()

    Use full path to download
    >>> downloader = FileDownloader('http://example.com/file.zip',
        "C:/Users/username/Downloads/newfilename.zip")
    >>> downloader.download()

    Basic Authentication protected download
    >>> downloader = FileDownloader('http://example.com/file.zip',
        "C:/Users/username/Downloads/newfilename.zip", ('username','password'))
    >>> downloader.download()

    Resume
    >>> downloader = FileDownloader('http://example.com/file.zip')
    >>> downloader.resume()
    '''

    def __init__(self, url, local_file_dir=None, local_file_name=None, username=None, password=None,
                 timeout=120.0, retries=5, logger=None, max_segments=10):
        '''Note that auth argument expects a tuple, ('username','password')'''
        if not logger:
            self._log = logging.getLogger('FileDownloader')
        self.url = furl(url)
        self.url_file_name = None
        self.progress = 0
        self.file_size = None
        if not (username is None and password is None):
            raise ValueError("Both username and password must be set or "
                             "neither can be set: username=%s, password=%s" %
                             (username, password))
        self.username = username
        self.password = password
        self.timeout = timeout
        self.retries = retries
        self.curretry = 0
        self.cur = 0
        try:
            self.url_file_size = self.get_url_file_size()
        except urllib2.HTTPError:
            self.url_file_size = None
        
        if not local_file_dir:
            self.local_file_dir = os.getcwd()
        else:
            self.local_file_dir = local_file_dir
            
        # if no filename given pulls filename from the url
        if not local_file_name:
            self.local_file_name = os.path.join(self.local_file_dir, self.get_url_file_name(self.url))
        else:
            self.local_file_name = os.path.join(self.local_file_dir, local_file_name)

    def _download_file(self, url_obj, file_obj, callback=None):
        '''starts the download loop'''
        self.file_size = self.get_url_file_size()
        while 1:
            try:
                data = url_obj.read(8192)
            except (socket.timeout, socket.error) as err:
                print "caught ", err
                self._retry()
                break
            if not data:
                file_obj.close()
                break
            file_obj.write(data)
            self.cur += 8192
            if callback:
                callback(cur_size=self.cur)

    def _retry(self):
        '''auto-resumes up to self.retries'''
        if self.retries > self.curretry:
            self.curretry += 1
            if self.get_local_file_size() != self.url_file_size:
                self.resume()
        else:
            print 'retries all used up'
            return False, "Retries Exhausted"

    def _auth_http(self):
        '''handles http basic authentication'''
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        # this creates a password manager
        passman.add_password(None, str(self.url), self.username, self.password)
        # because we have put None at the start it will always
        # use this username/password combination for  urls
        authhandler = urllib2.HTTPBasicAuthHandler(passman)
        # create the AuthHandler
        opener = urllib2.build_opener(authhandler)
        urllib2.install_opener(opener)

    def _auth_ftp(self):
        '''handles ftp authentication'''
        self.url.username = self.username
        self.url.password = self.password
        
        req = urllib2.Request(str(self.url))
        req.timeout = self.timeout

        ftped = urllib2.FTPHandler()
        ftp_obj = ftped.ftp_open(req)
        
        return ftp_obj

    def _start_http_resume(self, restart=None, callback=None):
        '''starts to resume HTTP'''
        cur_size = self.get_local_file_size()
        if cur_size >= self.url_file_size:
            return False
        self.cur = cur_size
        if restart:
            file_hndl = open(self.local_file_name, "wb")
        else:
            file_hndl = open(self.local_file_name, "ab")
        if self.username:
            self._auth_http()
        req = urllib2.Request(str(self.url))
        req.headers['Range'] = 'bytes=%s-%s' % (cur_size,
                                                self.get_url_file_size())
        urllib2_obj = urllib2.urlopen(req, timeout=self.timeout)
        self._download_file(urllib2_obj, file_hndl, callback=callback)

    def _start_ftp_resume(self, restart=None):
        '''starts to resume FTP'''
        cur_size = self.get_local_file_size()
        if cur_size >= self.url_file_size:
            return False
        if restart:
            file_hndl = open(self.local_file_name, "wb")
        else:
            file_hndl = open(self.local_file_name, "ab")
        ftper = ftplib.FTP(timeout=60)
        parse_obj = urlparse.urlparse(str(self.url))
        base_url = parse_obj.hostname
        url_port = parse_obj.port
        b_ath = os.path.basename(parse_obj.path)
        g_path = parse_obj.path.replace(b_ath, "")
        un_encg_path = urllib.unquote(g_path)
        file_name = urllib.unquote(os.path.basename(str(self.url)))
        ftper.connect(base_url, url_port)
        ftper.login(self.username, self.password)
        if len(g_path) > 1:
            ftper.cwd(un_encg_path)
        ftper.sendcmd("TYPE I")
        ftper.sendcmd("REST " + str(cur_size))
        down_cmd = "RETR " + file_name
        ftper.retrbinary(down_cmd, file_hndl.write)

    def get_url_file_name(self, url):
        '''returns filename from url'''
        return urllib.unquote(os.path.basename(str(url)))

    def get_url_file_size(self):
        '''gets filesize of remote file from ftp or http server'''
        if self.url.scheme == 'http':
            if self.username:
                self._auth_http()
            urllib2_obj = urllib2.urlopen(str(self.url), timeout=self.timeout)
            size = urllib2_obj.headers.get('content-length')
            return size

    def get_local_file_size(self):
        '''gets filesize of local file'''
        size = os.stat(self.local_file_name).st_size
        return size

    def check_exists(self):
        '''Checks to see if the file in the url in self.url exists'''
        if self.username:
            if self.url.scheme == 'http':
                self._auth_http()
                try:
                    urllib2.urlopen(str(self.url), timeout=self.timeout)
                except urllib2.HTTPError:
                    return False
                return True
            elif self.url.scheme == 'ftp':
                return "not yet supported"
        else:
            urllib2.urlopen(str(self.url), timeout=self.timeout)
            try:
                urllib2.urlopen(str(self.url), timeout=self.timeout)
            except urllib2.HTTPError:
                return False
            return True

    def download(self, callback=None):
        '''starts the file download'''
        self.curretry = 0
        self.cur = 0
        file_hndl = open(self.local_file_name, "wb")
        if self.username:
            if self.url.scheme == 'http':
                self._auth_http()
                urllib2_obj = urllib2.urlopen(str(self.url), timeout=self.timeout)
                self._download_file(urllib2_obj, file_hndl, callback=callback)
            elif self.url.scheme == 'ftp':
                auth_obj = self._auth_ftp()
                self._download_file(auth_obj, file_hndl, callback=callback)
        else:
            urllib2_obj = urllib2.urlopen(str(self.url), timeout=self.timeout)
            self._download_file(urllib2_obj, file_hndl, callback=callback)
        return True

    def resume(self, callback=None):
        '''attempts to resume file download'''
        if self.url.scheme == 'http':
            self._start_http_resume(callback=callback)
        elif self.url.scheme == 'ftp':
            self._start_ftp_resume()