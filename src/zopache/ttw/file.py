from PIL import Image as PilImage
import io
from ZODB.blob import Blob, BlobFile
from ZODB.POSException import POSKeyError
from zopache.ttw.acquisition import ParentalAcquire           
from dolmen.container import IBTreeContainer, BTreeContainer
from zope.interface import Interface, implementer
from dolmen.container import OrderedBTreeContainer
from zopache.core import Leaf
from zopache.remote.irss import IRSSArticle
from zopache.ttw.interfaces import (IFile,
                                    IImage,
                                    IFileBase,
                                    IImageBase,
                                    IBTreeImage)

from zopache.core.interfaces import ITreeSecurity
from zopache.core.breadcrumbs import Breadcrumbs          
from zope.interface import implementer

from dolmen.forms.base import  name, context

class FileBase(object):    
        
    @property
    def size(self):
        return len(self.data)

    def setData(self, data):
        try:
           dataFile = data.file
           bits =  dataFile.read()
        except:
           bits = data
        if len(bits) == 0:
            return
        if not hasattr(self,'blob'):
            self.blob = Blob()
        with self.blob.open(mode ="w") as blobFile:
           blobFile.write(bits)
           
    def getData(self):
        if not hasattr(self,'blob'):
            return ""
        try:
            with  self.blob.open(mode='r') as f:
               return f.read()
        except POSKeyError as error:
            return error.args[0]

    data = property(getData,setData)
    
@implementer(IFile)
class File(Leaf,FileBase):    
     pass

import base64 
class ImageBase(FileBase): 
    icon="ttwicons/Image.svg"
    title = ""
    attributionText = ""
    attributionURL = ""
    _altText = ""    
    def getImageTag(self,webClass = "",
                    alt = "",
                    style = "",
                    sizes = True):
        result = ""
        result += '<img src="data:' 
        result += self.contentType      
        result += ';base64,' 
        result += str(base64.b64encode(self.data).decode('utf-8'))
        result += '" '
        #if sizes:
        #   result += f'width = "{self.width}" ' 
        #   result += f'height = "{self.height}" '
        if style:   
           result +=f'style = "{style}" '
        if alt:   
           result +=f'alt="{alt}" '
        if webClass:   
           result +=f'class="{webClass}" /> '        
        return result

    
    def getHTML(self, view=None, style = ''):
        url = view.absoluteURL(self)

        tag = F"""<img src="{url}" """
        if hasattr(self,'title') and self.title!= '':
             tag += F""" alt = "{self.title}" """  
        if style !='':
             tag += F""" style = "{style}" """
        else:
             tag += """ width ="{self.width}" height = "{self.height}" """
        tag += ">"
        return tag

@implementer(IImage)
class Image (Leaf,ImageBase):
    #JUST A QUICK BUG FIX AVOIDANCE
    def get(self,arg):
        print ("BUG",self.__parent__.name, self.__parent__.__parent__.name)
        return self

    def replace (self):
        parent = self.__parent__
        name = self.__name__
        new = BTreeImage()
        new.blob = self.blob
        new.contentType = self.contentType
        new.width = self.width
        new.height = self.height
        del parent [self.__name__]             
        parent  [name] = new
        new.__name__ = name
        
    def getTitle(self):
        if self.__parent__.__class__ == BTreeImage:
           return self.__parent__.title
        else:
           return self.__dict__.get("title","")

    def setTitle(self,value):
        if self.__parent__.__class__ == BTreeImage:
           self.__parent__.__setattr__('title',value)
        else:
           self.__dict__["title"]=value       
           self._p_changed = True
           
    def getRemoteURL(self):
        if self.__parent__.__class__ == BTreeImage:
           return self.__parent__.remoteURL
        else:
           return self.__getattr_("remoteURL")        

    def setRemoteURL(self,value):
        if self.__parent__.__class__ == BTreeImage:
           self.__parent__.__setattr__('remoteURL',value)
        else:
           self.__setattr__("remoteURL",value)       
    
    remoteURL = property (getRemoteURL,setRemoteURL)
    title = property (getTitle,setTitle)
    
#BTreeImages have child thumbnails which are Images, and use
#the parent title and remoteURL.
from zopache.core import Container
@implementer (IBTreeImage)
class BTreeImage(ImageBase,Container):
    def __init__(self):
        ImageBase.__init__(self)
        BTreeContainer.__init__(self)
        
    def get(self,name,default=None):
        if name in self:
           return self[name]

        if name in {'16W',
                    '50W',
                    '75W',
                    '100W',
                    '150W',
                    '200W',
                    '400W',
                    '600W',
                     '25H',
                    '100H',
                    '200H',
                    '300H'}:
              return self.shrink(name) 
        return default

    def shrink(self,name):
         intName = int(name[0:-1])
         new = Image()
         
         if name [-1] == "H":
             ratio = intName/self.height
             newWidth = int(ratio * self.width)
             newHeight = intName
         elif name [-1] == "W":
             ratio = intName/self.width
             newWidth = intName
             newHeight = int(ratio * self.height)
         else:
             newWwidth = self.width
             newHeight = self.height
             
         size = (newWidth,newHeight)
         byteImgIO = io.BytesIO()
         byteImgIO.write(self.data)
         byteImgIO.seek(0)
         pilImage = PilImage.open(byteImgIO)
         pilImage = pilImage.resize(size)
         pilImage = pilImage.crop((0,0,newWidth,newHeight))
         #pilImage = self.cropSquare(pilImage,intName)
         byteImgIO = io.BytesIO()         
         pilImage.save(byteImgIO,'PNG')
         byteImgIO.seek(0)
         
         new.data = byteImgIO.read()
         new.contentType = "image/png"
         new.width = pilImage.width
         new.height = pilImage.height

         #new.data = self.data
         new.width = newWidth
         new.height = newHeight
         
         self._setitemf(name,new)
         new.__name__ = name
         new.__parent__ = self
         return new

    #And now we make a smaller image. 
    def mastodonImage(self):
        
         #Max size of 4MB for images on Mastodon
         ratio = 3900000  / self.size
         if ratio >=1:
             return self.data, self.contentType, getattr(self,"title","")
         
         newWidth = int(ratio * self.width)
         newHeight = int (ratio * self.height)
         size = (newWidth,newHeight)

         #PIL.Image.frombytes  Docs say to do it this way.  
         byteImgIO = io.BytesIO()
         byteImgIO.write(self.data)
         byteImgIO.seek(0)
         
         pilImage = PilImage.open(byteImgIO)
         pilImage = pilImage.resize(size)
         pilImage = pilImage.crop((0,0,newWidth,newHeight))
         
         #We could try to use pilImage.getdata()
         byteImgIO = io.BytesIO()
         pilImage.save(byteImgIO,'PNG')
         byteImgIO.seek(0)
         return byteImgIO.read(), "image/png", getattr(self,"title","")

    #THE FOLLOWING METHOD I THINK CUTS A PORTRAIT MODE PICTURE SQUARE
    #I THINK IT BREAKS ON LANDSCAPE MODE
    def cropSquare(self,image, height):
        if image.width <  image.height:
            return image
        maxWidth= height
        width = image.width
        left = (width -maxWidth )/2
        top = 0
        right = width -left
        return image.crop((left,top,right,height))
    
def make_file_response(view, result, *args, **kwargs):
        response = view.responseFactory()
        response.content_type=view.context.contentType
        response.write(result or u'')
        response.headers['cache-control'] = 'public,max-age=3600'  
        return response
    
from cromlech.webob.response import Response
from dolmen.view import View, make_view_response
from dolmen.view import view_component

@view_component
@name('index')
@context(IFile)
class IndexFile(View):
    responseFactory = Response
    make_response = make_file_response
        
    def render(self):
               return self.context.data

@view_component
@name('index')
@context(IImageBase)
class IndexImage(View):
    responseFactory = Response
    make_response = make_file_response
        
    def render(self):
               return self.context.data           

from dolmen.view import make_layout_response
#DISPLAY THE IMAGE WITH THE HEADER AND MENU BAR
@view_component
@name('displayImage')
@context(IImageBase)
class DisplayImage(View,Breadcrumbs):
    responseFactory = Response
    make_response = make_layout_response
    label=''
    subTitle='Uploaded Image'
    
    def headerScripts(self):
        return ""
    def footerScripts(self):
        return ""
    
    def breadcrumbs(self):
        return self.breadcrumbsManage()
    
    def render(self):
        #result = "<center><h2>Please Reload the page to view the image.</h2>"
        #result += "</center>"
        result = '<img src="' + self.absoluteURL(self.context)+ '">'
        return result
    
def make_logo_response(view, result, *args, **kwargs):
        response = view.responseFactory()
        response.headers['cache-control'] = 'public,max-age=3600'
        logo = ParentalAcquire(view.context)['Logo']
        if logo != None:
            contentType = logo.contentType
        else:
            contentType = ''
        response.content_type=contentType
        if result:
            response.write(result)
        return response


@view_component
@name('Logo')
@context(IBTreeContainer)
class LogoAcquire(View):
    responseFactory = Response
    make_response = make_logo_response
        
    def render(self):
               logo = ParentalAcquire(self.context)['Logo']
               if logo == None:
                   return ''
               return logo.data



#LOGO FOR ARTICLES        
@view_component
@name('Logo')
@context(IRSSArticle)
class LogoAcquire2(View):
    responseFactory = Response
    make_response = make_logo_response
        
    def render(self):
         context = self.context
         if 'Logo' in context:
             logo = context['Logo']
             return logo['200W'].data
         
         source = (getattr(context,'rssFeed',None) or
                   getattr(context,'curator',None) )

         if source:
             if 'Logo' in source:
               logo = source['Logo']
               return logo.get('200W').data
         
             logo = ParentalAcquire(source)['Logo']
         else:   
            logo = ParentalAcquire(context)['Logo']            
         if logo == None:
             return ''
         return logo['200W'].data
          

@view_component
@name('Logo150W')
@context(IBTreeContainer)
class Logo150WAcquire(View):
    responseFactory = Response
    make_response = make_logo_response
        
    def render(self):
               logo = ParentalAcquire(self.context)['Logo']
               if logo == None:
                   return ''
               return logo.get('150W').data                                 


@view_component
@name('Logo200H')
@context(IBTreeContainer)
class Logo200HAcquire(View):
    responseFactory = Response
    make_response = make_logo_response
        
    def render(self):
               logo = ParentalAcquire(self.context)['Logo']
               if logo == None:
                   return ''
               return logo.get('200H').data                                 
           

from zopache.ttw.interfaces import IInternalPrincipal           
@view_component
@name('index')
@context(IInternalPrincipal)
@implementer(ITreeSecurity)
class IndexCV(View):
    responseFactory = Response
    make_response = make_file_response
        
    def render(self):
               return self.context.data           

@view_component
@context(IFile)
@name('manage')
class ManageFile(IndexFile):    
   pass
                
                         
