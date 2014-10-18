#!/usr/bin/env python

# Imports #####################################################################
# from os import path, remove
import unittest
from libdlm import DownloadFile, DownloadManager, Settings
from time import sleep
import logging


###############################################################################
class SanityTest(unittest.TestCase):

    def test_start_dlm(self):
        '''Verify DownloadManager correctly starts dlm'''
        settings_list = (Settings(),
                         Settings({'thread_count': 1}),
                         Settings({'thread_count': 25}))

        for settings in settings_list:
            dlm = DownloadManager(settings)
            self.assertEqual(dlm.marco(), "polo")
            self.assertEqual(len(dlm.threads), settings.thread_count)

        dlm1 = DownloadManager(settings=settings_list[2], borg=True)
        dlm2 = DownloadManager(borg=True)

        self.assertEqual(dlm1.settings.thread_count,
                         dlm2.settings.thread_count)

        logging.getLogger("dlmtest")
        DownloadManager(logger="dlmtest")

        del(dlm)
        del(dlm1)
        del(dlm2)
        DownloadManager.reset_borg()

        dlm = DownloadManager(borg=True)
        self.assertNotEqual(dlm.logger_name, "dlmtest")

    def test_dl(self):
        '''Verify successful downloads'''
        dlm = DownloadManager()

        # test valid url
        dlm.append('http://kernel.org',
                   '.')

        # test valid url with callback
        dlm.append('http://kernel.org',
                   '.', self.dl_assert_noerr_callback)

        # test invalid url with callback
        dlm.append('https://www.kernel.org/invalid.html',
                   '.', self.dl_assert_err_callback)

        # test invalid url with no callback
        dlm.append('https://www.kernel.org/invalid.html',
                   '.')
        self.assertEqual(dlm.is_busy(), True)

        while dlm.is_busy():
            sleep(.1)

        # verify we are stopped and we respond appropriately
        dlm.pause()
        sleep(2)
        self.assertRaises(Exception, dlm.marco)
        self.assertEqual(dlm.is_busy(), False)

        # verify we are running and we respond appropriately
        dlm.resume()
        sleep(2)
        self.assertEqual(dlm.is_busy(), False)
        self.assertEqual(dlm.marco(), "polo")

    def test_dlf(self):
        '''Quick check fo the DownloadFile class'''
        self.assertRaises(TypeError, DownloadFile)
        self.assertEqual(type(DownloadFile(1, 2)), DownloadFile)

    def dl_assert_err_callback(self, url, err=None):
        '''callback from DownloadManager to verify an exception is raised'''
        self.assertEqual(isinstance(err, Exception), True)

    def dl_assert_noerr_callback(self, url, err=None):
        '''callback from DownloadManager to verify no exception is raised'''
        self.assertEqual(isinstance(err, Exception), False)


###############################################################################
if __name__ == "__main__":
    unittest.main()
