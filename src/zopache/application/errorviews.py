import traceback

from zope.interface import implementer
from dolmen.view import name, context, view_component
from cromlech.browser import IView, IResponseFactory
from cromlech.dawnlight.interfaces import ITracebackAware
from cromlech.webob.response import Response


@view_component
@name('')
@context(Exception)
@implementer(IView, IResponseFactory, ITracebackAware)
class ExceptionView(object):
    """Catch-all error view.

    cromlech.dawnlight's exception handling (see
    cromlech.dawnlight.utils.safeguard and cromlech.dawnlight.publish
    .exception_view) looks up an IView registered on the exception's
    class. Without one registered, that lookup itself raises a
    ComponentLookupError, which causes the *original* exception to be
    re-raised unhandled all the way up to uwsgi -- which then just
    drops the connection instead of returning a 500 response.

    Registering this view on the base Exception class means any
    unhandled exception gets rendered as a real response instead.
    """

    exc_info = None

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def set_exc_info(self, exc_info):
        self.exc_info = exc_info

    def __call__(self):
        if self.exc_info is not None:
            body = ''.join(traceback.format_exception(*self.exc_info))
        else:
            body = ''.join(traceback.format_exception_only(
                type(self.context), self.context))
        response = Response(status=500)
        response.content_type = 'text/plain'
        response.write(body)
        return response
