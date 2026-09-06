from zope.interface import implementer
from BTrees.OOBTree import OOBTree

from zopache.core.relatives import Parents
from zopache.business.interfaces import IPolitician
from zopache.business.interfaces import IOrganizationBase,IOnlineOrganization
from zopache.pages.page import Page
from zopache.pages.location import MapBase
from zopache.business.interfaces import IRegion
from zopache.business.interfaces import IEvent

class RegionBase(MapBase):

    specialization = ''
    showChildren = True
    webClass = "Region"
    remoteURL = ""
    latitude = 51
    longitude = 0
    def redundantRemoteURL(self):
        return ""



    def getColor(self):
        #COLOR BASED ON CLASS
        choose = {
                  'Business': 'yellow',
                  'Map': 'gold2x' 
                  }
        aClass = self.__class__.__name__
        if aClass in choose:
            return choose[aClass]

        #SELECT BASED On (CLASS, FUTURE EVENTS)
        hasFutureEvent = self.hasFutureEvent()
        choose = {
                  ('Politician',True):"orange",
                  ('Politician',False):"blue",
                  ('City',True):"orange",
                  ('City',False):"blue",            
                  ('MapOrganization',False):"red",                  
                  ('MapOrganization',True):"orange",                  
                  ('Organization',False):"red",
                  ('Organization',True):"orange",
                  ('Location',True):"bluered",
                  ('Location',False):"blue",
                  ('Company',True):"yellow2x",
                  ('Company',False):"yellow"                                    
                  }
        icon = choose[(aClass,bool(hasFutureEvent))]
        return icon

    def isNationalMap (self):        
        return self.webClass == 'NationalMap'

    def getMapPoliticians (self):
        if self.isNationalMap():
           return self.searchPoliticians(
                  isGreen = True
                 )
        else:
           return self.searchPoliticians(
                 )            
                      
    def getListPoliticians(self):
        if self.isNationalMap():
           return self.searchPoliticians(
                  isNational = True,
                  isGreen = True,
                 ) 
        else:
           return (self.parentPoliticians() +
                  self.searchBranchPoliticians(
                 ))
    
    def searchPoliticians(self,isNational = False,isGreen = False):    
        result = []
        for person in self.mapPoints.values():
            if person.__class__.__name__ != 'Politician':
               continue
            if isGreen and not person.isGreen():
               continue
            if isNational and not person.isNational():
               continue
            result.append(person)
        return result
        
    def parentPoliticians(self):        
        politicians = []
        parents = self.parentsWhichImplement(ILocationContainer)
        for parent in parents:
            for item in parent.values():
                if IPolitician.providedBy(item):
                    politicians.append(item)
        return politicians    
   
       
    def getOrganizations(self):
        result = []
        #Really Show Child Organizations
        showChildren = self.showChildren
        for item in self.mapPoints.values():
            if not IOrganization.providedBy(item):
                continue
            if ((item.parent == self) and
                not showChildren):
                continue
            result.append(item)
        return result

    def hasFutureEvent(self):
        return 0

    
#I Think this is not needed    
@implementer(IRegion)
class Region(Page,RegionBase):
    def __init__(self):
       Page.__init__(self)
       RegionBase.__init__(self)

