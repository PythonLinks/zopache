import json
from json_stream import streamable_list

from zope.interface import implementer
from BTrees.OOBTree import OOBTree

from zopache.pages.geo import geoCache
from zopache.pages.cache import cache, PageMixIn, RecentMixIn
from zopache.pages.page import PageBase, Page
from zopache.pages.interfaces  import (IPage,
                                       IPin,
                                       ILocationContainer,
                                       ILocationLeaf,
                                       ILocation,
                                       IMap,
                                       ISimpleMap
                                       )
from zopache.business.interfaces import IOrganizationBase

class MapOrLocation (PageBase):
    webClass = 'Location'
    hidden = False
    def getTitle(self):
        return self.title

    def getMarkerLatLng (self):
           return self.latitude, self.longitude

    def setMarkerLatLng(self, lat,lng):
        self.latitude = lat
        self.longitude = lng
        
    def getOneMarker(self):
                  lat,lng = self.getMarkerLatLng()
                  aClass = self.__class__.__name__[0]                  
                  hasFutureEvent =  self.hasFutureEvent()
                  result = [
                      self.__name__,
                      self.title,
                      lat ,
                      lng,
                      aClass,
                      hasFutureEvent]
                  
                  result += self.getOneMarkerCore()
                  result += [ self.remoteURL]
                  return result
              
    #MAY BE OVERRIDDEN BY SUBCLASSES TO GET MORE INFO          
    def getOneMarkerCore(self):
        return []
 
    def listOfAClass(self,aClassName):
        result = []
        for item in self.values():
            if (item.__class__.__name__ == aClassName):
               result.append (item)
        return result

    def listOfAClassInParents(self,aClassName):
        result = []
        node = self
        while node != None:
            for item in node.values():
                if (item.__class__.__name__ == aClassName):
                   result.append (item)
            if not hasattr(node,'__parent__'):
               break
            node = node.__parent__
        result.reverse()    
        return result


#At least used by events. 
@implementer (ILocation)
class Location (MapOrLocation):
    icon="ttwicons/Location.svg"
    
#At least used by events. 
@implementer (ILocationLeaf)
class LocationLeaf (MapOrLocation):
    icon="ttwicons/Location.svg"
    
@implementer (ILocationContainer)
class LocationContainer (MapOrLocation):
    icon="ttwicons/Location.svg"    

@implementer(ILocation)
class Location(LocationContainer):
    pass

import googlemaps
class MapBase(LocationContainer):
    zoomLevel=5.
    mapHeight=0.
    mapWidth=0.
    webClass = 'OpenStreetMap'
    #clientClass = 'Category'
    icon="ttwicons/Map.svg"

    def __init__(self):
       self.mapPoints =  OOBTree()
        
    def filter(self,mapPoints,view):
        request = view.request
        if not hasattr(request,'form'):
           return mapPoints
        form = request.form
        if not 'focus' in form:
           return mapPoints
        value = form ['focus']
        if value in ['', 'None']:
           return mapPoints
        result = []
        for item in mapPoints:
               if not hasattr(item,'focus'):
                  result.append(item)
                  continue
               if item.focus == value:
                  result.append(item)
        return result          

    def generateItems(self): 
        for item in self.mapPoints.values():
            if item.webApproved:
               yield item.getOneMarker()

    def getLocationsJSON(self):
        #https://pypi.org/project/json-stream/
        data =  streamable_list(self.generateItems())
        return json.dumps (data, indent = 2) 

#So the old maps had a center
#Which was also their Marker
@implementer (ISimpleMap)
class SimpleMap(Page,MapBase):        
    webClass = "SimpleMap"
    def __init__(self):
       Page.__init__(self)
       MapBase.__init__(self)

    def redundantRemoteURL(self):
        return  ""
    
@implementer(IPin)
class Pin(LocationContainer):
    showChildren = False
    remoteURL = ""
    def hasFutureEvent(self):
        return 0
