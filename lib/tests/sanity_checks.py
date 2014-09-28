#!/usr/bin/env python

# Imports #####################################################################
from os import path, remove
import unittest
from libdlm import DownloadManager, Settings


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
        
    def test_dl(self):
        '''Verify successful downloads'''
        dlm = DownloadManager()
        dlm.append('http://www.gutenberg.org/cache/epub/16328/pg16328.txt', '.')
        
        
###############################################################################
if __name__ == "__main__":
    unittest.main()
