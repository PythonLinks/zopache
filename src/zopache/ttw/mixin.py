#Just get the web class.
#Used by the html view objects. 

from zopache.core.getroot import getProducts

class Mixin (object):
    def getWebClass (self):
        context = self.context
        if hasattr(context, "webClass"):
            webClass = context.webClass
            if isinstance(webClass, str):
                products = getProducts(context)
                webClass = products.get (webClass, None)
                return webClass
        return None
