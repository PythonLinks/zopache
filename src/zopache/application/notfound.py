from zope.interface import Interface
from cromlech.browser import IView
from dolmen.view import view_component

from zopache.core.page import Page
from zopache.core.viewdecorators import *

@view_component
@context(Interface)
@name("not-found")
@target(IView)
class NotFound(Page):

    status = 404

    def render(self):
        return ("Not found: " + self.slug +
                "<br>In URL: " + self.request.url )

    def acquireTitle(self):
        return "Not Found Response"
