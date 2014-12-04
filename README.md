[![travis ci build state](https://travis-ci.org/JasonAUnrein/libdlm.svg?branch=master)](https://travis-ci.org/JasonAUnrein/libdlm)
[![rtd state](https://readthedocs.org/projects/libdlm/badge/?version=latest)](https://readthedocs.org/projects/libdlm/?badge=latest)
[![Coverage Status](https://img.shields.io/coveralls/JasonAUnrein/libdlm.svg)](https://coveralls.io/r/JasonAUnrein/libdlm)
[![Version](https://pypip.in/v/libdlm/badge.png)](https://pypi.python.org/pypi/libdlm)
[![Downloads](https://pypip.in/d/libdlm/badge.png)](https://pypi.python.org/pypi/libdlm)


## Introduction

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

## Documentation
Documentation is hosted on [persistetpineapple.readthedocs.org](http://persistetpineapple.readthedocs.org/en/latest/)

## Install
Download the tarball and install with `pip install <package>`.

## Usage
See the unit tests for more in-depth examples. Here are the basics:

