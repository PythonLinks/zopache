import aiohttp
import asyncio
import ssl
import time
import sys
import os
import logging

from dolmen.forms.base.markers import FAILURE, SUCCESS
from zopache.remote.irss import IJustRSS, IRSSArticle

os.makedirs('/app/data/logs', exist_ok=True)

rss_logger = logging.getLogger("rss")
rss_logger.setLevel(logging.INFO)
if not rss_logger.handlers:
    handler = logging.FileHandler('/app/data/logs/rss.log', mode="w")
    handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    rss_logger.addHandler(handler)

rss_error_logger = logging.getLogger("rss_errors")
rss_error_logger.setLevel(logging.INFO)
if not rss_error_logger.handlers:
    handler = logging.FileHandler('/app/data/logs/rss_errors.log', mode="w")
    handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    rss_error_logger.addHandler(handler)

async def fetch(session,node,view):
   startTime = time.time()    
   duration =  0
   className = view.className(node)
   isFeed = className in ["RSS","JustRSS"]
   if className in ["RSS","JustRSS"]:
      url = node.rssURL
   elif className == 'Article':
      if not node.title:
         url = node.articleURL
      else:   
         url = getattr(node,'imageURL',None)
         if url in ["",None]:
            return SUCCESS, (node.name + " No image URL.")
   elif className == "RSSArticle":
      url = getattr(node,'imageURL',None)
      if not url:
         return FAILURE, ("Existing Article " +
                          node.name +
                          " No image URL.") 
   else:
      return FAILURE, node.__name__, ("Error Trying to Fetch " +
      node.__class__.__name__)
   #NOW PROCESS THE URL
   try:
        url = url.strip()
        async with session.get(url) as response:
          status = response.status
          if status == 200:
             result = await node.processResponse(session,response,view)
             if isFeed:
                articles = result[1]
                entryCount = result[2]
                rss_logger.info("%s: %d/%d articles saved",
                                 node.title, len(articles), entryCount)
             return  result
          else:
             statusStr = str(status) + ' '
             logging.warning(statusStr + url)
             if isFeed:
                rss_error_logger.info("%s: status %s%s",
                                       node.title, statusStr, url)
             return FAILURE,( node,
                              ' status = ' +
                              statusStr +
                              url )
                              
   except asyncio.TimeoutError as err:
          duration =  time.time() - startTime
          duration = int(duration)
          if isFeed:
             rss_error_logger.info("%s: TIME OUT %ds %s",
                                    node.title, duration, url)
          return FAILURE, node, "TIME OUT: "  + str(duration) + 's ' + url
          
   except Exception as e:
          if isFeed:
             rss_error_logger.info("%s: %s %s", node.title, str(e), url)
          return FAILURE, node, (" IN RSSDownload " +
                                  str(e) + ' ' + url)

def fetchAll(nodes,view,allowedTime = 120):
    loop = asyncio.new_event_loop()
    #asyncio.set_event_loop(loop)
    return loop.run_until_complete(fetchCore(nodes,view,allowedTime))
   
async def fetchCore(nodes,view,allowedTime):   
    tasks = []
    timeout = aiohttp.ClientTimeout(total=allowedTime)
    user_agent = {'User-agent': 'Mozilla/5.0'}
    async with aiohttp.ClientSession(timeout = timeout,
                       headers = user_agent
                     ) as session:    
      for node in nodes:
         if view.className(node) not in {'RSS',
                                         'JustRSS',
                                         'RSSArticle',
                                         'Article',
                                         'Toot'}:
            continue
         if IRSSArticle.providedBy(node):
              if  'Logo' in node:
                   continue
         task = asyncio.create_task(fetch(session,
                                         node,
                                          view))
         tasks.append(task)
      result = await asyncio.gather(*tasks)
    return result  




