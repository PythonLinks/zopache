import requests


class Tootable(object):
    _toot = ''
    lastTootTime = 0
    delay = 0
    spoilerText = None
    tootURL = ""
    
    def getToot(self, view = None):
        if self._toot != "":
            return self._toot
        else:
            return self.defaultToot(view = view)

    def setToot(self,value):
        self._toot = value

    toot = property (getToot, setToot)    
    
    
    def lastTooted(self, view = None):
        if self.lastTootTime == 0:
           lastTooted = "My first toot of this video. "
        elif view == None:
           lastTooted = "ERROR CANNOT DISPLAY LAST TOOT TIME "           
        else:
            lastTooted = "Last Tooted " + view.ago(self.lastTootTime)
        return lastTooted

    def timeFreeToot(self):
         content = self._toot
         content = content.splitlines()
         
         for i, line in enumerate(content):
               if "Last tooted" in line:
                     content[i] = "" 
         
         separator = '\n'
         content = separator.join(content)        
         self._toot = content
         return content
     
    def defaultToot(self,view=None):
        return( self.title +
                "\n\n" + 
                self.description +
                "\n\n" +
                self.parentalTags() +
                "\n\n"          
        )    

    def defaultToot(self,view = None):
        result =  self.title +"\n\n" 
        result += self.description
        result += "\n"
        result += "(Click the url, not the image.)"
        result +=  "\n\n"
        result +=  view.secureShortURL(self)
        result +=  "\n\n" 
        if view:
           if not view.isManager():
              result += "Via @PythonLinks@Mastodon.Social \n\n"
        allTags = self.tags
        for item in allTags:
            result += item
            result += " "
        result += self.parentalTags()
        return result
    
    def getEmbed(self,view,tootURL):

        if tootURL:
           host = tootURL [8:].split('/')[0]
           embedURL = "https://"+ host + "/api/oembed?url=" + tootURL
           result = requests.get(embedURL)
           if result.status_code == 200:
              html = result.json()["html"]
              if(view.className()=="JSONMarkdown"):
                 json = self.json
                 if not (toots := json.get('toots')):
                    toots = list()
                    json['toots'] = toots                    
                 toots.append({'name' : "@" + view.request.principal.email,
                               'embed': html})
        else:
          view.submissionError += "Failed to fetch the embed code."
