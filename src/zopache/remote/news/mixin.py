from zopache.core.getroot import getPublicationRoot

class NewsMixIn(object):
    #To make a simple unified codebase
    #All of the inheritors get a default toot array
    #Just make sure that the first time you
    #Add somethign to it, to create a new array
    toots = []

    def tootTitlePlusDescription (self):            
            
            result = (
                self.title +
                "\n\n" +
                self.description +
                "\n\n" )
            return result


    def tootArticleURL(self):
        return self.articleURL + "\n\n"
                
    def tootVia(self, view):
            if view.isManager():
                return ""
            else:      
                return  "via @UncensoredNews@Mastodon.Social \n\n"

    def tootReadMore(self):                
            result = ("Read more at:  https://UncensoredNews.US/" +
               self.parent.name + 
               "\n\n" +
                self.tagsAsString() + ' ' +
                self.parentalTags()                 
                )
            return result
    
    def getDescriptionFor(self,view):
        if self.description:
            return self.description
        for toot in self.toots:
            if len (toot.content) > 10:
                return toot.content
        return self.description
            
    def getViaHref(self):
      result = []
      if len (self.toots) == 0:
          return ""
      for toot in self.toots:
        result.append ( f'<a href = "{toot.tootURL}" target = "_blank">{toot.parent.mastodonId}</a>')
      return "Via: " + ", ".join(result)       
       
    def getVia(self):
        result = [toot.parent.userName() for toot in self.toots]
        if result:
            return "Via: " + ' '.join (result)
    
    def getDescription(self,view):
        for item in self.toots:            
            if len(item.articles) == 1:
                if item.content:
                    return item.content
        return self.description

    def getBoosts(self):
        return sum( [item.numberOfBoosts for item in self.toots])

    
    def addToot(self,toot):
        #Because, to save space,  some have a shared class toot list.
        if len (self.toots) == 0:
           self.toots = [] 
        self.toots.append(toot)
        if len (self.toots) == 1:
           getPublicationRoot(self).tootedArticles[
               int(self.importTime)] = self 
        self.p_changed = True

    def hasToots(self):
        return len (self.toots) > 0

    def removeToot(self,toot):
        self.toots.remove(toot)
        if len(self.toots) == 0:
           del getPublicationRoot(self).tootedArticles[int(self.importTime)] 
        self.p_changed = True

    def removeAllToots(self):
        if len(self.toots)==0:                    
           return
        for aToot in self.toots:
            aToot.removeArticle(self)
        self.toots =[] 
        del getPublicationRoot(self).tootedArticles[int(self.importTime)]         
