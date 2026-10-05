import json
from zope.interface import implementer

from dolmen.forms.base.errors import Error, Errors

from zopache.core import Leaf
from zopache.pages.content import ContentWithChildContent
from zopache.json.interfaces import IBasicJSON
from zopache.json.jsonproperties import BasicProperties


@implementer(IBasicJSON)
class BasicJSON(Leaf):
    webClass = "BasicJSON"    
    schemaName = "TrackingSchema"

    def postAddProcess(self, view = None):
        pass

from zopache.zmi.interfaces import IURLSegment
import crom
@crom.adapter
@crom.sources(IBasicJSON)
@crom.target(IURLSegment)
class IMulilingualLeafAdaptor(object):
    def __init__(self,context):
        self.context=context
    def getSegment(self):
        return 'ckedit'        
