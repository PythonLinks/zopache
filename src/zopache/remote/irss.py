from zope import schema
from zopache.pages.interfaces import IPageBase, ILinkBase
from zopache.remote.interfaces import IVoteable

class IRSSBase(IPageBase):
    pass

# Gets most of its details from the parent class
class IJustRSS(IRSSBase):
    rssURL=schema.URI(
        title = "Primary RSS URI",
        description ="""This is the source of new articles.  
              Please include "https://" or "http://".""",
        required = True,
        )
    
    htmlSummary=schema.Bool(
        title = "Is the Summary HTML?",
        description ="For those sources where the summary contains html tags",
        required = False,
        default = False,
        )
    
class IRSS(IRSSBase):
    title=schema.TextLine(
        title = "RSS Feed Name",
        description ="What is the web site called?",
        required = True,
        )
    
    description= schema.Text(
        title = 'Description',
        description = """A brief introduction of this web site.  """,
        required = False,
        default = '',
    )    

    remoteURL= schema.URI(
        title = 'URL',
        description = ("The web site's URL."
                       "Please include 'https://'"),
        required = True,
    )
    
    mastodonId=schema.TextLine(
        title = "Mastodon Id",
        description ="""@User@Domain""",
        required = False,
        )    

    rssURL=schema.URI(
        title = "Primary RSS URI",
        description ="""This is the source of new articles.  
              Please include "https://" or "http://".""",
        required = True,
        )
    
    htmlSummary=schema.Bool(
        title = "Is the Summary HTML?",
        description ="For those sources where the summary contains html tags",
        required = False,
        default = False,
        )
    
    rssApproved=schema.Bool(
        title = "Is this feed approved for downloading",
        description ="We can block some feeds without deleting them.",
        required = False,
        default = True,
        )
    
    keepAllArticles=schema.Bool(
        title = "Keep all of their articles?",
        description ="Or clear out the old ones to save space?",
        required = False,
        default = False,
        )    

class IAddRSS(IRSS):
    logoURL=schema.URI(
        title = "Logo URL ",
        description ="An image is important",
        required = False,
        missing_value = '',
        )
    
class IRSSPage (IRSS):
      pass

class IRSSArticle(ILinkBase):

    title = schema.TextLine(
        title = 'Remote Article Name',
        description = 'What is the title of this link?',
        required = True,
    )
    
    articleURL= schema.URI(
        title = 'Article URL',
        description = 'The url of the remote article',
        required = False,
    )
    
    description= schema.Text(
        title = u'Description',
        description = """A brief introduction of this page.  
                        This is used by the search functions.""",
        required = False,
        default = u'',
    )

    source= schema.Text(
        title = 'Content',
        description = 'This is the main content for this page',
        required = False,
        default = '',
    )

  
