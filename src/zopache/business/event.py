
from BTrees.OOBTree import OOBTree
from zopache.pages.page import Page
from zopache.business.interfaces import IEvent,IOnlineEvent
from zope.interface import implementer
from zopache.business.geocoding import GeoCodeObject
from zopache.pages.page import Page

class EventBase(Page):
    count = 0
    webClass = "Event"
    clientClass = "Category"
    webApproved = True
    
    def __init__(self):
        Page.__init__(self)

    #This method provides spelling error in the data.     
    def getMarkerLatLng (self):
           if hasattr(self,'lattitude'):
               return self.lattitude, self.longitude
           else:
               return self.latitude, self.longitude           
        
    def hasFutureEvents(self):
        return 1
    
    def listFutureEvents(self):
        return [self]
    
    def postAddProcess(self,view=None):
        if view.treeSecurity():
           self.webApproved = True
        Page.postAddProcess(self,view)
        
    def canView(self,view):
        return True

@implementer (IOnlineEvent)
class OnlineEvent (EventBase):
    webClass = "OnlineEvent"    

from zopache.pages.location import LocationLeaf
@implementer(IEvent)
class Event(GeoCodeObject,EventBase,LocationLeaf):
    remoteURL = ""
    def __init__(self):
        Page.__init__(self)
        GeoCodeObject.__init__(self)
