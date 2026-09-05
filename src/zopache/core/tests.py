from cromlech.security.interfaces import IPrincipal ,IUnauthenticatedPrincipal
from zopache.application.treesecurity import TreeSecurity
from dolmen.container import IBTreeContainer
from pydoc import locate
from zopache.pages.interfaces import IImaginaryBTree
from zopache.remote.ivideo import IVideo
from zopache.ttw.interfaces import  ICanonical
from zopache.remote.ivideo import IVideo
    
class Tests(object):
    def isCanonical (self,view):
        return ICanonical.providedBy(view.context)
    
    def hasMembers(self):
        return hasattr(self.context,'isMember')
    
    def isPerson(self):
        return IPrincipal.implementedBy(self.context)

    def isVideo(self,*item):
        if item:
           item = item[0]
        else:
           item = self.context 
        return IVideo.providedBy (item)

    def isConference(self):
        return False
    
    def isForestWiki(self):
        root = self.getSiteRoot()
        return root.name == 'wiki'
        
    def treeSecurity(self):
        tree = TreeSecurity(self)
        if (self.isAuthenticated() and
           tree.hasEditorPermission()):
            return True
        return False

    def hasPermission(self, aPermission):
        if (self.isAuthenticated() and
           aPermission in self.request.principal.permissions):
           return True
        return False

    def isManager(self):
        return self.hasPermission('Manage')

    def isParty(self):
        return self.hasPermission('Party')

    def isCurator(self):
        return self.hasPermission('Curate')    

    def isPython(self):
        return self.hasPermission('Python')    
    
    def isDeveloper(self):
        return self.hasPermission('Develop')    

    def hasValue(self,attribute,*args):
        item = self.context if len(args)==0 else args [0]
        if hasattr(item, attribute):
            value = getattr(self.context,attribute,None)
            if value:
               return True
        return False

    #I DO NOT THINK THIS IS USED ANYWHERE
    #def hasTrueAttribute(self,attribute):
    #    return self.hasValue(attribute)
    
    def implements (self,dottedName):
        return self.itemImplements(self.context,dottedName)
    
    def itemImplements(self, item, dottedName):
        myInterface = locate(dottedName)
        if myInterface == None:
            return False
        result = myInterface.providedBy(item)
        return result

    def isAuthenticated(self):
       return not IUnauthenticatedPrincipal.providedBy(self.request.principal)

    def isBTreeContainer(self,*args):
        item = self.context if len(args)==0 else args [0]        
        return  IBTreeContainer.providedBy(item)

    #SHOULD BE USING
    #from zopache.pages.iimaginary import IImaginaryBTree
    #BUT THAT BREAKS THE BUILD
    def isContainer(self,*args):
        item = self.context if len(args)==0 else args [0]        
        if IBTreeContainer.providedBy(item):
            return True
        if IImaginaryBTree.providedBy(item):
            return True
        return False


    def hasRootPermission(self):
        principal = self.request.principal
        if principal.__class__  == UnauthenticatedPrincipal:
            return False
        principalName = principal.__name__
        root = self.getZodbRoot()
        if principalName in root.editors:
            return True
        return False
    
    def getResizeCommand(self):
        if IVideo.providedBy(self.context):
           return "resize()"
        else:
           return None
    
        
    
