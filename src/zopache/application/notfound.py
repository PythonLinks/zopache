from zope.interface import Interface
from cromlech.webob.response import Response
from dolmen.view import View, make_view_response
from cromlech.browser import IView
from dolmen.view import View, view_component

from zopache.core.viewdecorators import *

@view_component
@context(Interface)
@name("not-found")
@target(IView)
class NotFound(View):
    responseFactory = Response
    make_response = make_view_response

    def render(self):
        return "Not found: " + self.slug + " (" + self.request.url + ")"


