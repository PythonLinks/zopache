from zope.interface import Interface
from zope.schema.vocabulary import SimpleVocabulary
from zope import schema
import crom
from zopache.pages.interfaces import IPageBase
from zopache.zmi.interfaces import IURLSegment
from zopache.ttw.treewidget import TreeField

                           
def recordingTypes():
    terms = []
    for item in [
                ('One Lightning Talk among many in a single recording.',
                    'lightning-talk'),
                ('One Lightning Talk by itself','single-lightning-talk'),
                ('A Longer Video','longer-video'),
                ('A Lightning Talk Followed by a Longer Video (Recommended)',
                 'a-lightning-talk-followed-by-a-video'),
                ]:
        term = SimpleVocabulary.createTerm(item[1],item[1],item[0])
        terms.append(term)
    return SimpleVocabulary(terms)

from zopache.remote.interfaces import IVoteable

 

class IVideo(IPageBase,IVoteable):
    title = schema.TextLine(
        title = u'Video Title',
        description = u'What is the title of this video.?',
        required = True,
    )
    
    organization = schema.TextLine(
        title = u'The Organization presenting this video',
        description = u'Which conference, or company produced this video?',
        required = False,
    )
    organizationURL= schema.URI(
        title = u'Organization URL ',
        description = """The URL for the organization mentioned above. 
                           Must include https:// or http://""",
        required = False,
        missing_value = "",
    )
     
    description= schema.Text(
        title = u'Description',
        description = """A brief introduction of this video.  
                        This is used by the search functions.""",
        required = False,
        default = u'',
    )
    
    source= schema.Text(
        title = u'Longer Description',
        description = """A longer description of this video. Include the                             relevant links here.""",
        required = False,
        default = '',
    )

class IVideoId(Interface):
    videoId=schema.TextLine(
        title="Video Id",
        description= """The You Tube ID for this Video.  You can find it in 
                      the video URL. """,
        required = True,)
    
class IEmbed(Interface):
    embed=schema.Text(
        title="Video Embed string",
        description= """The You Tube embed string for this Video.""",
         required = True)
    
class IStartTime(Interface):
    
    hours = schema.Int(
        title = "Hours",
        description = "Start Time: Hours",
        default = 0,
        required = False)

    minutes = schema.Int(
        title="Minutes",
        description= "Start Time: Minutes",
        default = 0,
        required = False)    
    
    seconds = schema.Int(
        title="Seconds",
        description= "Start Time:Seconds",
        default = 0,
        required = False)

    """
    startTime = schema.TextLine(
        title="Start Time (Displayed",
        readonly = True,
        description= "Start Time (appended to the YouTube url).",
        default = '0',
        required = False)        
    """

class IBasicVideo(IVideo, IVideoId, IStartTime):
    pass
        
class IEmbedVideo(IVideo, IEmbed, IStartTime):
    pass        

class IJSVideo(IVideo, IEmbed, IStartTime):
      pass
               
class IPrincipalVideo(IEmbedVideo):
    recordingType = schema.Choice(
        vocabulary=recordingTypes(),
        title="Recording Type",
        description= "What type of recording was this?",
        required = True)
        
    category=TreeField(
           title="Category",
           description= "How should this video be classified?",
           required = True,
            )


@crom.adapter
@crom.sources(IVideo)
@crom.target(IURLSegment)
class IEditAdaptor(object):
    def __init__(self,context):
        self.context=context   

    def getSegment(self):
        return 'ckedit'
