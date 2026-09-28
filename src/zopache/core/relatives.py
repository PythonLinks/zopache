from cromlech.location import lineage_chain
from cromlech.browser import IPublicationRoot
from cromlech.location import lineage_chain
from zopache.crud.interfaces import IZodbRoot

def reversedParentsUpTo(self,anInterface):
        parents=[]
        item=self        
        while (item!=None):
           parents.append(item)
           if anInterface.providedBy(item):
              break
           item=item.__parent__      
        return parents

def parentWhichImplements(self,interface):
        item=self        
        while (item!=None):
           if interface.providedBy(item):
              return item
           item=item.__parent__      
        return None
    
#THIS IS PLURAL    
def parentsWhichImplement(self,interface):
        item=self        
        result=[]
        while (item!=None):
           if interface.providedBy(item):
              result.append(item)
           item=item.__parent__      
        return result

def parentsUpTo(self,anInterface):
    return self.reversedParentsUpTo(self,anInterface).reverse()

class Parents(object):
    def __init__(self,context):
        self.context = context

    def parentalMethod(self,context,method):
       for item in self.lineage(context):
           if hasattr(item,method):
              return item.__getattr__(method)
       raise Exception("NO SUCH METHOD FOUND")

    def reversedParentsUpTo(self,item,anInterface):
        parents=[]
        while (item!=None):
           parents.append(item)
           if anInterface.providedBy(item):
              break
           item=item.__parent__      
        return parents

    def reversedParentsUpToSiteRoot(self,item):
        return self.reversedParentsUpTo(item,IPublicationRoot)

    def parentsUpToSiteRoot(self,item=None):
        if item ==None:
           item = self.context 
        parents = self.reversedParentsUpToSiteRoot(item)
        parents.reverse()
        return parents
    
    def reversedParentsUpToZodbRoot(self,item):
        return self.reversedParentsUpTo(item,IZodbRoot)    

    def parentsUpToZodbRoot(self, item = None):
        if item ==None:
           item = self.context         
        parents = self.reversedParentsUpToZodbRoot(item)
        parents.reverse()
        return parents

    def parentsUpToSubDomain(self,item):
        domain = self.getDomain()
        splitDomain= domain.lower().split(".")
        if len(splitDomain) == 3:
           siteRootName = splitDomain[0]
        else:
           siteRootName = ""
        parents=[]
        while (item!=None):
           parents.append(item)
           if item.__name__ == siteRootName :
              break     
           if IPublicationRoot.providedBy(item):
              break
           item=item.__parent__
        parents.reverse()   
        return parents



    def parentsWhichImplement(self,interface):
           item=self.context
           result=[]
           while (item!=None):
             if interface.providedBy(item):
                       result.append(item)
             item=item.__parent__
           return result
   
    def parentWhichImplements(self,interface):
           item=self.context
           while (item!=None):
             if interface.providedBy(item):
                   return item
             item=item.__parent__
           return None


    def parentOfClass(self,className):
           item=self.context
           while (item!=None):
             if item.__class__.__name__ == className:
                   return item
             item=item.__parent__
           return None        


    def parentCalled(self,name):
           item=self.context
           while (item!=None):
             if item.name == name:
                   return item
             item=item.__parent__
           return None     
   
    def parents(self, item=None):
        if item == None:
           item = self.context
        result  = self.parentsUpToSiteRoot()
        return result

    def reversedParents(self,item = None):
        if item == None:
           item = self.context
        result  = self.parentsUpToSiteRoot()
        result.reverse()
        return result


    def lineage (self,item):
        return lineage_chain(item)

    def siblings (self,item):
        if item.__parent__ == None:
            return []
        if not hasattr(item.__parent__,'childCategories'):
            return []
        siblings = item.__parent__.childCategories()
        siblings.remove (item)        
        return siblings

