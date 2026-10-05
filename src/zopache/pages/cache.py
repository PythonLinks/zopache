from BTrees.OOBTree import OOBTree
from cromlech.browser.exceptions import HTTPFound

from zopache.pages.interfaces import IRecent, IPage
import heapq
import math
import time
from zopache.core.getroot import getPublicationRoot

"""
So what do we have here?
There are six different caches.  3 for categories, 3 for videos. 
They are dictionaires indexed by item key. 
The 2 score caches for videos.   wilson score and most recent.
Noo need to cache creation date.

The 3 for categories cache the __name__ of the top 10 videos in that
branch of the tree. 


The cache disappears everytime the app is restarted.
We only cache the results that someone has asked for. 
Cache is accessible from multiple threads. 
Caches will also be deleted upon edits. 

I do not want to sort huge lists of objects, so I use heapq 
to just keep track of the 10 best items in any category. 
So sorting scales linearly with branch size, not n log (n)

The heapq sort uses a tuple 
(score, __name__, item)
That way two items with the same score can be compared by alphabetic name. 
Comparing the items gave an error. 
"""

import inspect
from functools import wraps


class SiteCache :
    def __init__(self):
            self.resetCache()

    def resetCache(self):
            self.wilsonScoreBest = {}
            self.myScoreBest = {}
            self.mostRecentBest = {}
            self.voteTotalsBest = {}            
            self.wilsonScoreCache = {}
            self.myScoreCache = {}
            self.voteTotalsCache = {}

class Cache:
    def __init__(self):
        self.siteCaches = {}

    def resetCache(self,context):
        siteName = getPublicationRoot(context).__name__
        self.siteCaches[siteName]= SiteCache()
        
    def get(self, name, key, default=None):
            cache = getattr(self, name)
            return cache.get(key, default=default)

    def set(self,name, key, value):
            cache = getattr(self, name)
            cache[key] = value

    def clear(self, name, key, value):
            cache = getattr(self, name)
            if key in cache:
               del cache[key]
               return True
            return False

    def __call__(self, name):
            def caching(func):
                @wraps(func)
                def cached(target,*args, **kwargs):
                    siteName = getPublicationRoot(target).__name__
                    if not siteName in self.siteCaches:
                       self.siteCaches [siteName]= SiteCache()
                    cache = self.siteCaches[siteName]
                    cache = getattr(cache, name)                    
                    key = target.__name__
                    if key in cache:
                        value = cache.get(key)
                        if isinstance(value, list):
                              items = target.convertNamesToObjects(value)
                              return items
                        return value  
                    value = func(target,*args, **kwargs)
                    if isinstance(value, list):
                         names = target.convertObjectsToNames(value)           
                         cache[key] = names
                    else:
                         cache[key] = value
                    return value
                return cached
            return caching
cache = Cache()        




class MixIn(object):

    #The best caches have to cache __name__
    #So we have to convert back and forth to ids. 
    def convertNamesToObjects(self,list):
       root = self.getSiteRoot() 
       result = []
       for item in list:
           theItem = root.get (item)
           if theItem is not None:
              result.append(theItem)
       return result
   
    def convertObjectsToNames(self,list):
       result = []
       for item in list:
               result.append(item.__name__)
       return result
   

    @cache('mostRecentBest')               
    def bestMostRecentPage (self):
        return self.bestObjects('mostRecent',IPage)        

    def bestObjects(self,sortKey,whichInterface):
        root = self.getPublicationRoot()
        aHeap = []

        self.bestCategoryObjects(sortKey,root,aHeap, whichInterface)
        result = []
        while (aHeap):
           result.append(heapq.heappop(aHeap)[2])
        result.reverse()
        return result

    #FOR A CATEOGRY
    def bestCategoryObjects(self,sortKey,root,aHeap,whichInterface):

       #FOR NON CONFERENCE CALCULATE THE BEST IN THIS BRANCH
       for item in self.values():
           if not IPage.providedBy (item):
               continue
           if whichInterface.providedBy(item):
               if item.webApproved:
               #if not item.__class__.__name__ != 'Page':               
                  item.addToHeapQ2(aHeap,sortKey)
           if IPage.providedBy (item):
              item.bestCategoryObjects(sortKey,root,aHeap,whichInterface)
    """
    #FOR LEAF ITEMS.  NO LONGER USED
    def bestConferenceObjects(self,sortKey,root,aHeap):
       #FOR NON CONFERENCE CALCULATE THE BEST IN THIS BRANCH
       items =  list(map(lambda x: x, self.talks.items()))       
       
       for key,item in items:
           name = item.__name__
           if name  == None:
              item.__name__ = key
              del self.talks [key]
              continue
           if name != key:
              del self.talks [key]
              continue
           if IConferenceVideo.providedBy(item):
              item.addToHeapQ2(aHeap,sortKey)
     """  
       

    def addToHeapQ2(self,aHeap,sortKey):
        # For conferences we want to compare all the talks
        # Otherwise just the top 10
        listLength = 9
        if (self.__parent__.__name__ ==
            "the-best-lightning-talks-of-pycon-usa-2019"):
            listLength = 15
        if (self.__parent__.__name__ ==
            "europython-2019-lightning-talks"):
            listLength = 27
            
        if (len(aHeap)> listLength ):
            heapq.heappushpop(aHeap,(getattr(self,sortKey),self.__name__,self))
        else:
            try:
               heapq.heappush(aHeap,(getattr(self,sortKey),self.__name__,self))
            except:
               pass


    @cache('voteTotalsCache')                       
    def getVoteTotals (self):
                ups = self.upVotes()
                downs = self.downVotes()
                n = ups - downs           
                return n

    voteTotals = property (getVoteTotals)        
           
    @cache('wilsonScoreCache')                       
    def getWilsonScore (self):
                ups = self.upVotes()
                downs = self.downVotes()
                n = ups + downs
                if n == 0:
                    return 0
                z = 1.96 #1.44 = 85%, 1.96 = 95%
                phat = float(ups) / n
                wilsonScore = ((phat + z*z/(2*n) - z * math.sqrt((phat*(1-phat)+z*z/(4*n))/n))/(1+z*z/n))
                return wilsonScore
            
    @cache('myScoreCache')                                   
    def getMyScore(self):
        viewCount = self.viewCount
        if viewCount == 0:
            return 0
        myScore =  1000*(self.upVotes() - (5 * self.downVotes()))/viewCount
        return myScore

    #THE PROBLEM IS THAT WE HAVE TO
    #PUT APPROVED ARTICLES FIRST, SO IT HAS TO
    #SORT BASED ON APPROVAL TIME.
    #BUT ON THE RAW FEED IT HAS TO SORT BASED ON THE
    #CREATION TIME.  WE WILL FIX THAT WHEN WE GET TEHRE. 
    def getMostRecent(self):
        if hasattr(self,'modificationTime'):
           return self.modificationTime        
        else:
           return 0
        #if hasattr(self,'publishedAt'):
        #   return self.publishedAt
        #if hasattr(self,'creationTime'):
        #   return self.creationTime   
        #else:
        #   return 0
       
    mostRecent = property (getMostRecent)
       
        
class RecentMixIn(MixIn):
   pass

class PageMixIn (MixIn):
   pass    
