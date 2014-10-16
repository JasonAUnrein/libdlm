#!/usr/bin/env python

# Imports #####################################################################
# from os import path, remove
import unittest
from libdlm import DownloadFile, DownloadManager, Settings


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

    def test_dl(self):
        '''Verify successful downloads'''
        dlm = DownloadManager()
        dlm.append('http://www.gutenberg.org/cache/epub/16328/pg16328.txt',
                   '.')
        dlm.append('http://www.gutenberg.org/cache/epub/invalid_url',
                   '.', self.dl_assert_err_callback)
        dlm.append('http://www.gutenberg.org/cache/epub/16328/pg16328.txt',
                   '.', self.dl_assert_noerr_callback)

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
