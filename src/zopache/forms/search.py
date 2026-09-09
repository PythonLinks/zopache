from hypatia.catalog import CatalogQuery
import hypatia
from hypatia.query import Contains

def searchCore(view, aDict,categoryName,limit):
    context = view.context
    root = view.getSiteRoot()
    
    if context.__class__.__name__ == 'RSS':
       recommended = aDict.get("recommended","all")        
    else:
       recommended = aDict.get("recommended","recommended")        
    searchTerm = aDict.get("query","")
    type = aDict.get("type","both")

    contentCatalog = root.contentCatalog
    q = CatalogQuery (contentCatalog)
    fields = []
    if newCategory := aDict.get("newCategory",False) :
       fields.append(hypatia.query.NotAny(contentCatalog['ancestorNames'], newCategory))
    
    #NOW FOR RECOMMENDED
    if recommended == 'recommended':
        recommended = True
    elif recommended == 'other':
        recommended = False
        
    #NOW FOR THE TYPE 
    if type == "video":
       type = True
    elif type == 'article':
       type = False
   
    #FIRST FOR THE SEARCH TERM
    if searchTerm != "":
       fields.append(hypatia.query.Contains(contentCatalog['titlePlusDescription'], searchTerm))
    
    if recommended != "all":
        fields.append(hypatia.query.Eq(contentCatalog['recommended'], (recommended,recommended)))

    if type != 'both': 
           fields.append(hypatia.query.Eq(contentCatalog['isVideo'], (type,type)))

    if categoryName != 'categories':
           fields.append(hypatia.query.Any(contentCatalog['ancestorNames'], [categoryName]))

    #If NO SEARCH TERMS, RETURN ALL
    if len(fields) == 0:
        fields.append(hypatia.query.Eq(contentCatalog['isVideo'], (False,True)))

    myQuery = fields [0]
    for item in fields[1:]:
        myQuery = myQuery & item

    numDocs, docIds = q.query(
            myQuery,
            limit = limit,
            sort_index='importTime'
            )
    return numDocs, docIds

def searchForRSS(view, aDict, categoryName,limit = 20):
    numDocs, docIds  = searchCore (view,
                                   aDict,
                                   categoryName,
                                   limit)
    return  docIds

def searchADictionary(view,
                      aDict,
                      defaultCategory = None,
                      limit = 1000):

    if defaultCategory == None:
        categoryName = view.context.name
    numDocs, docIds = searchCore (view,
                                  aDict,
                                  categoryName,
                                  limit)
    docIds = list(docIds)

    searchTerm = aDict.get("query","")
    if searchTerm:
       return numDocs, [], docIds
   
    type = aDict.get("type","both")
    #Fixing a naming difference
    if type == 'article':
       type = 'articles'
    if type == 'video':
       type = 'videos'
    
    root = view.getSiteRoot()
    category = root[categoryName]
    try:
        content = category.json[type]
    except:
        return numDocs, [], docIds
   
    if len(content) == 0:
       return numDocs, [], docIds            

    featuredTimes= set()
    featuredItems = []
    for row  in content:
           name = row['name'].strip()
           if not name in root:
              continue 

           item = root[name]
           featuredItems.append(item)
           time = item.importTime
           featuredTimes.add (time)
    notFeaturedIds = []
    for time in docIds:
        if time not in featuredTimes:
           notFeaturedIds.append(time)
           
    #returning list(featuredTimes) incorrectly sorts them by importTime.
    featuredTimes =  [item.importTime for item in featuredItems]           
    return numDocs, featuredTimes,  notFeaturedIds

def valuesPlusRemainder(view, docIds, count=6):
    index = view.getSiteRoot().contentByTime
    values = [index[int(x)] for x in docIds[:count]]
    return values, docIds[count:]

def justValues(view,docIds):
    index = view.getSiteRoot().contentByTime
    return  [index[int(x)] for x in docIds]

def getResults(view):
    numDocs, featured, remainder = searchADictionary (view,view.request.form)
        
    numFeatured = len(featured)
    featured= justValues (view,featured)
    values, remainder = valuesPlusRemainder (
        view,remainder, count = 6-numFeatured)
    return numDocs, featured, values, remainder

def lastItem(view):    
    items = view.getSiteRoot().contentByTime
    maxKey = items.maxKey()
    lastItem = items[maxKey]



