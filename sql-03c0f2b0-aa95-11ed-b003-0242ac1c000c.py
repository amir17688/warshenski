#!/usr/bin/env python
# -*- coding: utf-8 -*-
# DiskCache.py

import  os
import  sys
import  zlib
import  time
import  logging as logger
import  urlparse
from  datetime import  datetime, timedelta
try:
    import cPickle as pickle
except ImportError:
    logger.info ("cPickle module not available")
    import pickle
sys.setrecursionlimit(10000)

class  DiskCache:
    """
    Dictionary interface that stores cached
    values in the file system rather than in memory.
    The file path is formed from an md5 hash of the key.
    """

    def  __init__ (self, cache_dir='cache', expires=timedelta(days=30), compress=True):
        """
        cache_dir: the root level folder for the cache
        expires: timedelta of amount of time before a cache entry is considered expired
        compress: whether to compress data in the cache
        """
        self.cache_dir = cache_dir
        self.expires = expires
        self.compress = compress


    def  __getitem__ (self, url):
        """Load data from disk for this URL
        """
        path = self.url_to_path (url)
        if  os.path.exists (path):
            with open (path, 'rb') as fp:
                data = fp.read()
                if  self.compress:
                    logger.info ('Loading...')
                    data = zlib.decompress (data)
                result = pickle.loads (data)
                #if  self.has_expired (timestamp):
                #    self.__delitem__ (url)
                #    raise  KeyError (url + ' has expired')
                return  result
        else:
            # URL has not yet been cached
            raise KeyError(url + ' does not exist')


    def  __setitem__ (self, url, result):
        """Save data to disk for this url
        """
        path = self.url_to_path (url)
        folder = os.path.dirname (path)
        if not os.path.exists (folder):
            os.makedirs (folder)

        data = pickle.dumps (result) # saves the current timestamp in the pickled data
        if  self.compress:
            logger.info ('Saving...')
            data = zlib.compress (data)
        with  open(path, 'wb') as fp:
            fp.write (data)


    def  __delitem__ (self, url):
        """Remove the value at this key and any empty parent sub-directories
        """
        path = self.url_to_path (url)
        try:
            os.remove (path)
            os.removedirs (os.path.dirname(path))
        except OSError:
            pass


    def  url_to_path (self, url):
        """Create file system path for this URL
        """
        components = urlparse.urlsplit (url)
        # when empty path set to /index.html
        path = components.path
        if not  path:
            path = '/index.html'
        elif  path.endswith('/'):
            path += 'index.html'
        filename = components.netloc + path + components.query
        # replace invalid characters
        # filename = re.sub('[^/0-9a-zA-Z\-.,;_ ]', '_', filename)
        # restrict maximum number of characters
        filename = '/'.join(segment[:255] for segment in filename.split('/'))
        return  os.path.join(self.cache_dir, filename)


    def  has_expired (self, timestamp):
        """Return whether this timestamp has expired
        """
        return  datetime.utcnow() > timestamp + self.expires


    def  clear (self):
        """Remove all the cached values
        """
        if  os.path.exists (self.cache_dir):
            shutil.rmtree (self.cache_dir)
