from zopache.ttw.acquisition import ParentalAcquire,webClassAcquire


class Acquisition(object):

    def acquireBoth(self, name, context = None):
        result = self.parentalAcquire(name, context = context)
        if result != None:
           return result
        return self.webClassAcquire(name, context = context)
    
    #WITH ZOPACHE TEMPLATES THE CONTEXT
    #CAN BE DIFFERENT THAN THE PARENT
    #VIEW -> PARENT
    def acquire(self,name, context=None):
        if (context == None):
           context = self        
        return self.parentalAcquire(name,context)

    #VIEW -> CONTEXT
    def parentalAcquire (self,name,context=None):
        if (context == None):
            context = self.context
        return ParentalAcquire(context)[name]

    def layoutAcquire(self,name):
        layout = self.getLayout()
        return ParentalAcquire (layout)[name]

    def possibleWebClassAcquire(self,name):
        context = self.context
        if not hasattr(context,'webClass'):
           return webClassAcquire(self.context.__parent__,name)
        return webClassAcquire(context,name)
    

    def webClassAcquire(self,name,context=None):
        if context == None:
           context = self.context
        return webClassAcquire(context,name)

    def acquireTitle(self):
        if (hasattr(self.context,"webClass") and
            (self.context.webClass == "Company") and
            not self.isAuthenticated()):
              return "Please login to see the Company"
        if hasattr(self,'title'):
           return self.title
        return self.acquireAttribute('title')

    def acquireAttribute(self, attribute):      
        parents = self.lineage(self.context)
        for item in parents:
            result = getattr(item,attribute,'')
            if result:
               return result
        return ''

    
    #QUITE A STRANGE METHOD.  DO I REALLY USE IT?
    def safeParentalAcquire(self,name,context=None):
          if context==None:
             context = self.context

          result = ParentalAcquire(context) [name]
          if result == None:
             return ("ERROR: " + name +
                     "DOES NOT EXIST IN THE PARENTS OF" +
                     self.href(self.url(context), context.name))
          try:
              result = result (self)
              return result
          except:
            return "ERROR IN SAFE PARENTAL ACQUIRE"

    def templateParentalAcquire(self, name):
        result = ParentalAcquire(self.zopacheTemplate)
        return result [name]

    def parentalAcquireAndView(self, name):
        item = self.parentalAcquire(name)
        if not item:
            return ''
        return item(view=self)    
