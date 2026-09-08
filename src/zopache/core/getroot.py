#THERE IS A COPY OF THIS IN zopache.core  as well       
from cromlech.browser.interfaces import IPublicationRoot
from BTrees.OOBTree import OOBTree

from zopache.core.interfaces import ISiteRoot
from zopache.crud.interfaces import IZodbRoot

def getProducts(item):
        return getZodbRoot(item)["Products"]                        

def getRoot(object,anInterface):
        max = 9999
        context=object
        while context is not None:
            if anInterface.providedBy(context):
                return context
            #IF YOU GET TO ZODB ROOT AND STILL NO STIE ROOT,
            #RETURN NONE
            if ((IZodbRoot.providedBy(context)) and
               (anInterface == IPublicationRoot)):
               return None
            context = context.__parent__
            max -= 1
            if max < 1:
                raise TypeError("Maximum location depth exceeded, "                                "probably due to a a location cycle.")
        raise TypeError("Parents needed to  determine location root")

def getPublicationRoot(item):
    return getRoot(item, IPublicationRoot)
               
def getZodbRoot(item):
    return  getRoot(item, IZodbRoot)

def getPrincipalFolderNoView(item):
    root = getPublicationRoot(item)
    if ((root != None) and not
       ("person" in root)):
        root = root ['syndicate']    
    return root["person"]

def getPrincipalFolder(item,view):
    root = view.getSiteRoot()
    if ((root != None) and
       ("person" in root)):
        return root["person"]
    raise Exception ("No Prncipal Folder found.  Odd. ")

def getSiteRoot(self,view):
    siteRoot =  getPublicationRoot(self)
    if not ISiteRoot.providedBy(siteRoot):
        siteRoot = siteRoot.getSiteRootFor(view.getDomain())         
    return siteRoot

class Root(object):
    def getDBRoot(self):
           return (self.request.environ['zodb.connection'].root()
                   ['applicationRoot'])


    #There is ZODB Root and Site Root, both have to be publication roots.
    def getSiteRoot(self):
        siteRoot= getattr(self,'_siteRoot',None)
        if (siteRoot != None):
           return siteRoot        
        self._siteRoot = siteRoot = getSiteRoot(self.context,self)
        return siteRoot        

    def getZodbRoot(self):
        return getZodbRoot(self.context)

    def getPrincipalFolder(self):
        siteRoot = self.getSiteRoot()
        return siteRoot["person"]


    def getPrincipal(self):
           return self.request.principal

    def getProducts(self):
        products = getattr(self,'_products',None)
        if products == None:
            root = getZodbRoot(self.context)
            self._products = products =  root["Products"]                
        return products

    def getLayout(self):
        products = self.getProducts()
        layouts = products ["Layouts"]
        domain = self.getDomain()
        if domain in layouts:
           layout =  layouts [domain]
        elif "default" in layouts:
           layout =  layouts ["default"]
        else:
           layout = layouts
        return layout

    def getTemplates(self):
        products = self.getProducts()
        return products['Templates']

    def getATempalate(self,name):
        return self.getTemplates().get (name,None)

    def getHeaders(self):
        products = self.getProducts()
        return products['Headers']

    def getAllHeaders(self):
        headers = self.getHeaders()
        result = ""
        for item in headers.values():
            result += item.render(self, view = self)
        return result
    
    def getSiteRootAndView(self, name,view):
        root = self.getSiteRoot()    
        item = root.get(name, None)
        if not item:
            return ''
        return item(view=view)    
