import dawnlight
from cromlech.dawnlight import DawnlightPublisher
from  zopache.application.traverser import Traverser
from cromlech.dawnlight.utils import safeguard
from cromlech.browser import IPublisher, IView, IResponseFactory
from zope.interface.interfaces import ComponentLookupError
from zopache.ttw.historyitem import HistoryTraverser
from zopache.pages.interfaces import IPage,IProxyPage
from cromlech.security import unauthenticated_principal as anonymous
from cromlech.dawnlight.publish import shortcuts, PublicationError

class Publisher (DawnlightPublisher):
    """Traverses model objects, and looks up views.
    """
    def __init__(self,view_locator):
         self.view_locator=view_locator
         self.longPath = []
         self.shortPath = []
         self.shortPathOkay = True

    def newContext(self,newContext):
        self.longPath.append(newContext)

        if not IPage.providedBy (newContext):
            self.shortPathOkay = False
        if IProxyPage.providedBy (newContext):
            self.shortPathOkay = False
        if not self.shortPathOkay:
            self.shortPath.append(newContext)


    @safeguard
    def publish(self, request, root,handle_errors):
        view=None
        publisher  = self
        path = self.base_path(request)
        context=root
        hostName = request.domain
        #Maybe traverse to a lower level SiteRoot
        crumbs = dawnlight.parse_path(path, shortcuts)
        if crumbs:
             aType, name=crumbs.popleft()
             if  name in context:
                 pass
             elif  name in ['backup',
                            'manage',
                            'addRootPage',
                            'editjson',
                          'fix',
                          'editors',
                          'aceedit',
                          'addRootCategory',
                          'addPoliticiansSite',
                          'editHosts']:
                 pass
             else:
                context = context.getSiteRootFor(hostName)
        else:
                context = context.getSiteRootFor(hostName)
                domain = hostName
                splitDomain= domain.lower().split(".")
                if len(splitDomain) == 3:
                   siteRootName = splitDomain[0]
                   if siteRootName in context:
                      context = context[siteRootName]


        traverser=Traverser(self.view_locator)
        crumbs = dawnlight.parse_path(path, shortcuts)
        while crumbs:
           aType, name=crumbs.popleft()
           if (aType =='history'):
              # CALL THE HISTORY TRAVERSER
              historyTraverser=HistoryTraverser(context,None)
              context=historyTraverser.traverse('history',name)
              continue

           #NOW FOR THE REGULAR TRAVERSER
           context, view =traverser(context,request,name,publisher)
           if view != None:
                 break

        #If that did not work  check for a template or view
        if view is  None:
           name = 'index'
           context, view=traverser(context,request,name,publisher)

        #If still no view, check for a view on the template
        if view is  None:
           name = 'index'
           context, view=traverser(context,request,name,publisher)


        #IF A VIEW WAS FOUND, RETURN IT

        if (view is  not None):
            view.publisher = publisher
            factory = IResponseFactory(view)
            response = factory()

            status = getattr(view, 'httpStatus', 200)
            if status != 200:
                response.status_int = status

            content_type = response.headers['content-type']

            if status != 200:
                #Never let an error response (eg. not-found) be cached
                #as if it were a valid page.
                response.headers['cache-control'] = "no-store"
            elif 'image' in content_type: #A Month
                response.headers['cache-control'] = "public, max-age=2592000"
            elif hasattr(view,"isDeveloper") and view.isDeveloper():
                response.headers['cache-control'] = "no-store"                
            elif 'html' in content_type:
                if (request.principal != anonymous):
                    response.headers['cache-control'] = "no-store"
                else:
                    response.headers['cache-control'] = "public, max-age=3600"
            elif 'javascript' in content_type:                
                response.headers['cache-control'] = "public, max-age=86400"
            elif 'json' in content_type:
                if (request.principal != anonymous): 
                    response.headers['cache-control'] = "no-store"
                else:
                    response.headers['cache-control'] = "public, max-age=86400"
            else: # Includes CSS 
                response.headers['cache-control'] = "public, max-age=86400"

            origin = request.headers.get('Origin')
            if origin: # A CORS REQUEST
              originDomain = origin.split("://")
              if len (originDomain) > 1:
                  originDomain = originDomain [1]
              else:    
                  originDomain = None
              if view.getDomain() !=originDomain:    
                 if (('javascript' in content_type or
                      'json' in content_type)
                      and originDomain in CORS_ALLOWED_DOMAINS):
                     response.headers['access-control-allow-origin'] = origin
                     response.headers['access-control-allow-methods'] = "GET"
                     response.headers['cache-control'] = "no-store"
            return response

        raise PublicationError('%r can not be rendered.' % context)

CORS_ALLOWED_DOMAINS = (
    "wiki.pythonlinks.info",
    "uncensorednews.us",
    "greenmaps.us",
)
