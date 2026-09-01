
from jsmin import jsmin
from . import tal_template
from html import escape
from zope import interface
from zope import schema
from zope.interface import Interface
from zope.schema.interfaces import IField
from zope.interface import Interface
from zopache.ttw.interfaces import ITestSource as ISource
from zopache.ttw.addeditforms import AceAddForm, PugEditForm
from zopache.crud.forms import EditDemoForm
from dolmen.container import IBTreeContainer
from zopache.core.breadcrumbs import Breadcrumbs
from zopache.core.interfaces import ITreeSecurity
from zopache.core.getroot import getProducts
from zopache.core.viewdecorators import *
from dolmen.container import IBTreeContainer,BTreeContainer
from zopache.core import Leaf, Container
from zopache.ttw.acescripts import  AceScriptPug
from .interfaces import ISourceContainer
from .interfaces import IJavascript
from zopache.ttw.interfaces import ISourceLeaf, ISourceContainer
from zopache.ttw.interfaces import ITemplate
from zopache.core.page  import  Page
from .interfaces import ITestURL
from cromlech.webob.response import Response
from .javascript import JavascriptBase
from dolmen.view import View, make_view_response
from .html import TrustedHTML

defaultPug = """
html
  head
    title Hello World
  body
    h1 Hello World 
"""

defaultHTML = """
<html>
<head>
<title>Hello World</title>
</head>
<body>
Hello World 
</body>
</html>

"""

class IPugBase(ISourceLeaf,IJavascript):
    "Basic Pug Form"

    title = schema.TextLine(
        title = u'Title',
        description = u'Describe this Pug Object.',
        required = False,
    )

    functionName = schema.TextLine(
        title = u'Function Name',
        description = 'What is this function called?',
        required = False,
    )
    
    globals = schema.TextLine(
        title = u'Globals',
        description = u'Which Global Variables are Accessible?',
        required = False,
    )        

    source= schema.Text(
        title = u'Pug Source Code',
        description = u'The Pug Template:',
        required = False,
        default = defaultPug,
    )
    
    javascript= schema.Text(
        title = u'Javascript',
        description = u'The generated Javascript:',
        required = False,
        default = defaultHTML,
    )
    
    html= schema.Text(
        title = u'HTML:',
        description = u'The generated HTML:',
        required = False,
        default = '',
    )

    compileDebug= schema.Bool(
        title = 'Compile Debug',
        description = 'Include Debugging Info in JS.',
        required = False,
        default = False,
    )

    sideBySide = schema.Bool(
        title = 'Side By Side',
        description = 'Show Text Areas Side By Side?',
        required = False,
        default = True,
    )    


    showJavascript = schema.Bool(
        title = 'Show Javascript',
        description = 'Show the Javascript or Not',
        required = False,
        default = True,
    )    

    showHTML = schema.Bool(
        title = 'Show HTML',
        description = 'Show the HTML Text Area?',
        required = False,
        default = True,
    )
    showIFrame    = schema.Bool(
        title = 'Show the IFrame?',
        description = 'Show the Iframe or Not?',
        required = False,
        default = True,
    )    

class IPug(ISourceLeaf, IPugBase):
    pass

class IPugContainer(ISourceContainer,IPugBase):    
    pass
    
from .javascript import JavascriptBase              
class PugBase(TrustedHTML,JavascriptBase):
    icon="ttwicons/Pug.svg"    
    source =defaultPug
    html = defaultHTML
    title=u''
    className='Pug'
    sideBySide = True
    showJavascript = True
    showIFrame = True
    showHTML = True

    def postProcess(self,view=None):
        parent = self.__parent__
        if (IPugContainer.providedBy(parent)):
            parent.mergeChildren()
            
        TrustedHTML.postProcess(self,view)
        JavascriptBase.postProcess(self,view = view)

    def postAddProcess(self, view = None):
        self.postProcess(view=view)
        
    def getHTML(self):
        return self.html
    
    def getJavascript(self):
        return self.javascript

    def getSource(self):
        return self.source
        
@implementer(IPug)
class Pug(PugBase,Leaf):
    pass

import re
# r"" ignores python \ commands
# \s*  Any white space characters
# {}()$ are special characters, they get escaped
# \w* any number of  [a-zA-Z0-9_].
# The original string
#| ${structure: pug['about'](view=view)}
# [$]matches $  

expression = r"([$]\{\s*structure:\s*pug\[\s*'(\w*)'\s*\]\s*\(\s*view\s*=\s*view\s*\)\s*\})"

@implementer(IPugContainer)
class PugContainer(PugBase, Container):
    """Has child PUG objects."""
    
    def getHTML(self):
        return self.mergedHTML
    
    def postProcess(self,view=None):
        self.mergeChildren()
        PugBase.postProcess(self,view=view)
            
    def mergeChildren(self):
        query = re.compile(expression)
        html = self.html
        result = query.findall(html)
        for (string,arg) in result:
            new = self[arg].html
            html = html.replace(string,new,1)
        self.mergedHTML = html
               
class BasePugForm(AceScriptPug):
    label=''
    def breadcrumbs(self):
        return self.breadcrumbsManage()
    

@form_component
@name('addPug')
@context(IBTreeContainer)
@target(IView)
@title("Add Pug")
@implementer(ITreeSecurity)
class AddPug(AceScriptPug,AceAddForm):
    subTitle='Add a Pug Object'
    interface = Interface
    ignoreContent = True
    factory=PugContainer
    def update(self):
        self.template = self.getTemplates()['TranspilerTemplate']
        AceAddForm.update(self)
        
#HERE WE HAVE THE ACE EDIT FORM               
@form_component
@context(IPugBase)
@target(IView)
@name("aceedit")
@implementer(ITreeSecurity)
class AceEditPug(BasePugForm,PugEditForm):
    subTitle='Ace Edit this Pug Template.'
    def update(self):
        self.template = self.getTemplates()['TranspilerTemplate']        
        PugEditForm.update(self)


#RENDER HTML
@view_component
@name('index')
@context(IPugBase)
@title("View Pug  HTML")
class PugIndex(View,Breadcrumbs):
    count=0    
    responseFactory = Response
    make_response = make_view_response

    def setDisplayObject(self,item):
         self.zopacheTemplate=item

    def render(self):
        return self.context(self)
    
@view_component
@name('template')
@context(IPugBase)
class ViewTemplate(PugIndex):
    def render(self):
            return self.context.getHTML()

from .javascript import makeJavascriptResponse, JavascriptBase

@view_component
@name('javascript')
@context(IPug)
@title("View Pug")
class PugJavascipt(Page):
    responseFactory = Response
    make_response = makeJavascriptResponse
        
    def render(self ):
        return self.context.javascript

      
import crom
from zopache.zmi.interfaces import IURLSegment
@crom.adapter
@crom.sources(IPugContainer)
@crom.target(IURLSegment)
class IPugContainerAdaptor(object):
    def __init__(self,context):
        self.context=context   

    def getSegment(self):
        return 'manage'
