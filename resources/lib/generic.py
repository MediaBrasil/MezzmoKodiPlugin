import sys
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs
import urllib2
import urllib
import xml.etree.ElementTree
import re
import xml.etree.ElementTree as ET
import urlparse
import browse
import xbmc
import sys
import json
import os
import media
import sync
import time
from views import content_mapping, setViewMode
from server import getItemlUrl, upnpCheck, picDisplay
from server import clearPictures, updatePictures, downServer


addon = xbmcaddon.Addon()
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
#argmod = sys.argv[2][1:].replace(';','&')    #  Handle change in urllib parsing to default to &
args = urlparse.parse_qs(sys.argv[2][1:])

addon_path = addon.getAddonInfo("path")
addon_icon = addon_path + '/resources/icon.png'
addon_fanart = addon_path + '/resources/fanart.jpg'

#installed_version = media.get_installedversion()

logcount = 0
gsrvrtime = int(media.settings('gsrvrtime'))
if not gsrvrtime:
    gsrvrtime = 60
generic_response = int(media.settings('generic_response'))
if generic_response > 0:
    logcount = int(media.settings('genrespcount'))

    
def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

def ghandleBrowse(content, contenturl, objectID, parentID):
    contentType = 'movies'
    itemsleft = -1
    pitemsleft = -1 
    media.settings('contenturl', contenturl)
    slideshow = media.settings('slideshow')             # Check if slideshow is enabled 
    udynlist =  media.settings('udynlist')              # Check if Dynamic Lists are enabled  
    menuitem1 = addon.getLocalizedString(30347)
    menuitem2 = addon.getLocalizedString(30346)
    menuitem3 = addon.getLocalizedString(30372)
    menuitem4 = addon.getLocalizedString(30373)
    menuitem5 = addon.getLocalizedString(30379)
    menuitem6 = addon.getLocalizedString(30380)
    menuitem7 = addon.getLocalizedString(30384)
    menuitem8 = addon.getLocalizedString(30412)
    menuitem9 = addon.getLocalizedString(30488)
    sync.deleteTexturesCache(contenturl)                # Call function to delete textures cache if user enabled.  
    #xbmc.log('Kodi version: ' + installed_version, xbmc.LOGNOTICE)
    try:
        while True:

            if len(content) == 0:                       # Handle downed server
                downServer('upnp')                      # Downed server message            
                break;     #sanity check

            e = xml.etree.ElementTree.fromstring(content)           
            body = e.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Body')
            browseresponse = body.find('.//{urn:schemas-upnp-org:service:ContentDirectory:1}BrowseResponse')
            result = browseresponse.find('Result')
            NumberReturned = browseresponse.find('NumberReturned').text
            TotalMatches = browseresponse.find('TotalMatches').text
            
            if int(NumberReturned) == 0:
                dialog_text = media.translate(30421) + '\n' + xbmc.getInfoLabel("ListItem.Label")
                xbmcgui.Dialog().ok(media.translate(30424), dialog_text)
                xbmc.executebuiltin('Action(ParentDir)')
                break; #sanity check
                
            if itemsleft == -1:
                itemsleft = int(TotalMatches)
            
            elems = xml.etree.ElementTree.fromstring(result.text.encode('utf-8'))
            #elems = xml.etree.ElementTree.fromstring(result.text)
            picnotify = 0

            if udynlist == 'true':
                genmulist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)        # Create playlist
                genmulist.clear()
                muid = genmulist.getPlayListId()              
            for container in elems.findall('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}container'):
                title = container.find('.//{http://purl.org/dc/elements/1.1/}title').text 
                containerid = container.get('id')
                
                description_text = ''
                description = container.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}longDescription')
                if description != None and description.text != None:
                    description_text = description.text
    
                icon = container.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}albumArtURI')
                if icon != None:
                    icon = icon.text
                    if 'jpg' not in icon: 
                        icon = icon + '.jpg'
                    xbmc.log('Handle browse second icon is: ' + icon, xbmc.LOGDEBUG)     

                itemurl = build_url({'mode': 'server', 'parentID': objectID, 'objectID': containerid,      \
                'contentdirectory': contenturl})        
                li = xbmcgui.ListItem(title)
                li.setArt({'banner': icon, 'poster': icon, 'icon': icon, 'fanart': addon_fanart})

                mediaClass_text = 'video'
                info = {
                        'plot': description_text,
                }
                li.setInfo(mediaClass_text, info)
                    
                searchargs = urllib.urlencode({'mode': 'search', 'contentdirectory': contenturl,           \
                'objectID': containerid})

                li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)') ])                
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=True)
                picnotify += 1
                if parentID == '0':
                    contentType = 'top'
                else:
                    contentType = 'folders'
                contentType = content_mapping(contentType)


            piclist = []
            clearPictures() 
            upnpnotify = 0     
            for item in elems.findall('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}item'):
                title = item.find('.//{http://purl.org/dc/elements/1.1/}title').text
                itemid = item.get('id')
                icon = None
                albumartUri = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}albumArtURI')
                if albumartUri != None:
                    icon = albumartUri.text
                    if 'jpg' not in icon: 
                        icon = icon + '.jpg'
                    xbmc.log('Handle browse second icon is: ' + icon, xbmc.LOGDEBUG)    

                res = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}res')
                subtitleurl = None
                duration_text = ''
                video_width = 0
                video_height = 0
                aspect = 0.0
                validf = 0
                protocol_text = ''

                if res != None:
                    itemurl = res.text
                    #xbmc.log('The current URL is: ' + itemurl, xbmc.LOGNOTICE)
                    subtitleurl = res.get('{http://www.pv.com/pvns/}subtitleFileUri')            
                    duration_text = res.get('duration') 
                    if duration_text == None:
                        duration_text = '00:00:00.000'
                    elif len(duration_text) < 9:          #  Check for proper duration Twonky
                        duration_text = duration_text + '.000'  
                    elif  len(duration_text) > 12:        #  Check for proper duration Jellyfin
                        duration_text = duration_text[:9] + '000'         
                    elif int(duration_text[len(duration_text)-3:len(duration_text)]) != 0:  
                        duration_text = duration_text[:6] + '.000'
                    #xbmc.log('The duration is: ' + str(duration_text), xbmc.LOGNOTICE)                    
                    resolution_text = res.get('resolution')
                    if resolution_text != None:
                        mid = resolution_text.find('x')
                        video_width = int(resolution_text[0:mid])
                        video_height = int(resolution_text[mid + 1:])
                        aspect = float(float(video_width) / float(video_height))
                    protocol = res.get('protocolInfo')
                    if protocol != None:
                        protocol_text = protocol
                    #xbmc.log('The protocol is: ' + str(protocol), xbmc.LOGNOTICE) 
                else:
                    duration_text = '00:00:00.000'
                    itemurl = getItemlUrl(contenturl, itemid)
                    if upnpnotify == 0:      # Do not repeat notification
                        upnpCheck()          # Check Kodi service uPNP setting                    
                    upnpnotify = 1
                    if itemurl == 'None':
                        dialog_text = media.translate(30393)
                        xbmcgui.Dialog().ok(media.translate(30406), dialog_text)
                        xbmc.executebuiltin('Action(ParentDir)')             
                        break

                backdropurl = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}cvabackdrop')
                if backdropurl != None:
                    backdropurl = backdropurl.text
                    if 'jpg' not in backdrop: 
                        backdropurl  = backdropurl  + '.jpg'

                poster = ''
                thumb = ''
                res2 = item.findall('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}res')
                for protocol in res2:
                    protocolinfo = protocol.attrib["protocolInfo"]
                    if 'poster' in protocolinfo:
                        poster = protocol.text
                    if 'thumb' in protocolinfo:
                        thumb = protocol.text
                    if 'fanart' in protocolinfo and backdropurl == None:
                        backdropurl = protocol.text
                    if 'icon' in protocolinfo and icon == None:
                        icon = protocol.text                              

                upnpclass_text = ''
                upnpclass = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}class')
                if upnpclass != None:
                    upnpclass_text = upnpclass.text  

                li = xbmcgui.ListItem(title)
                if len(thumb) > 0 and len(poster) > 0:
                    li.setArt({'thumb': thumb, 'poster': poster, 'icon': icon, 'fanart': backdropurl})
                else:
                    li.setArt({'thumb': icon, 'poster': icon, 'icon': icon, 'fanart': backdropurl})

                if subtitleurl != None:
                    li.setSubtitles([subtitleurl])
                  
                trailerurl = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}trailer')
                if trailerurl != None:
                    trailerurl = trailerurl.text
                
                genre_text = []
                for genre in item.findall('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}genre'):
                    if genre != None:
                        genre_text.append(genre.text.encode('utf-8'))              
                #xbmc.log('Mezzmo genre list is: ' + str(genre_text), xbmc.LOGNOTICE)
                    
                aired_text = ''
                aired = item.find('.//{http://purl.org/dc/elements/1.1/}date')
                if aired != None:
                    aired_text = aired.text
                  
                album_text = ''
                album = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}album')
                if album != None:
                    album_text = album.text
                  
                release_year_text = ''
                release_year = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}release_year')
                if release_year != None:
                    release_year_text = release_year.text

                release_date_text = ''
                release_date = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}release_date')
                if release_date != None:
                    release_date_text = release_date.text
                
                description_text = ''
                description = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}longDescription')
                if description != None and description.text != None:
                    description_text = description.text
                else:                                             #  Bubble uPNP description
                    description = item.find('.//{http://purl.org/dc/elements/1.1/}longDescription')
                    if description != None and description.text != None:
                        description_text = description.text
                      
                imageSearchUrl = ''
                imageSearchUrl = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}imageSearchUrl')
                if imageSearchUrl != None:
                    imageSearchUrl = imageSearchUrl.text
                   
                artist_text = ''
                artist = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}artist')
                if artist != None:
                    artist_text = artist.text

                actor_list = ''
                cast_dict = []    # Added cast & thumbnail display from Mezzmo server
                cast_dict_keys = ['name','thumbnail']
                actors = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}artist')
                if actors != None and imageSearchUrl != None:
                    actor_list = actors.text.encode('utf-8', 'ignore').replace(', Jr.' , ' Jr.').replace(', Sr.' , ' Sr.').split(',')
                    for a in actor_list:                  
                        actorSearchUrl = imageSearchUrl + "?imagesearch=" + a.lstrip().replace(" ","+")
                        #xbmc.log('search URL: ' + actorSearchUrl, xbmc.LOGNOTICE)  # uncomment for thumbnail debugging
                        new_record = [ a.strip() , actorSearchUrl]
                        cast_dict.append(dict(zip(cast_dict_keys, new_record)))
                elif actors == None:
                    actor_list = []
                    for actor in item.findall('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}actor'):
                        if actor != None:
                            actor_list.append(actor.text.encode('utf-8'))
                    artist_text = actor_list                
                    #xbmc.log('Mezzmo actor list is: ' + str(actor_list), xbmc.LOGNOTICE)
               
                #if len(actor_list) == 0:            # Sanity check for missing artists
                #    artist_text = ["Unknown artist"]
                if isinstance(artist_text, str):            # Sanity check for missing artists
                    artist_text = ["Unknown artist"]                
          
                creator_text = ''
                creator = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}creator')
                if creator != None:
                    creator_text = creator.text
                elif creator == None:
                    creator = item.find('.//{http://purl.org/dc/elements/1.1/}creator')
                    if creator != None:
                        creator_text = creator.text

                director_text = ''
                director = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}director')
                if director != None:
                    creator_text = director.text

                date_added_text = ''                
                date_added = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}date_added')
                if date_added != None:
                    date_added_text = date_added.text
                else:                                                  # Kodi uPNP 
                    date_added = item.find('.//{urn:schemas-xbmc-org:metadata-1-0/}dateadded')
                    if date_added != None:
                        date_added_text = date_added.text
                   
                tagline_text = ''
                tagline = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}tag_line')
                if tagline != None:
                    tagline_text = tagline.text
                else:                                                 # Kodi uPNP
                    tagline = item.find('.//{http://purl.org/dc/elements/1.1/}description')
                    if tagline != None:
                        tagline_text = tagline.text
                    
                categories_text = 'movie'
                categories = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}categories')
                if categories != None and categories.text != None:
                    categories_text = categories.text.split(',')[0]   #  Kodi can only handle 1 media type
                    if categories_text[:7].lower() == 'tv show':
                        categories_text = 'episode'
                        contentType = 'episodes'
                    elif categories_text[:5].lower() == 'movie':
                        categories_text = 'movie'
                        contentType = 'movies'
                        album_text = ''
                    elif categories_text[:11].lower() == 'music video':
                        categories_text = 'musicvideo'
                        contentType = 'musicvideos'
                        album_text = ''
                    else:
                        categories_text = 'video'
                        contentType = 'videos'
                        album_text = ''
                        
                episode_text = ''
                episode = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}episode')
                if episode != None:
                    episode_text = episode.text
                else:                                  #  Added for MediaMonkey track number XML tag
                    episode = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}originalTrackNumber')
                    if episode != None:
                        episode_text = episode.text   
                 
                season_text = ''
                season = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}season')
                if season != None:
                    season_text = season.text
                 
                playcount = 0
                playcount_text = ''
                playcountElem = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}playcount')               
                if playcountElem != None:
                    playcount_text = playcountElem.text
                    playcount = int(playcount_text)

                playcountElem = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}playbackCount')               
                if playcountElem != None:                              # Kodi uPNP
                    playcount_text = playcountElem.text
                    playcount = int(playcount_text)
                 
                last_played_text = ''
                last_played = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}last_played')
                if last_played != None:
                    last_played_text = last_played.text

                last_played_text = ''                                 # Kodi uPNP
                last_played = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}lastPlaybackTime')
                if last_played != None:
                    last_played_text = last_played.text
                        
                writer_text = ''
                writer = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}writers')
                if writer != None:
                    writer_text = writer.text

                writer_text = ''                                      # Kodi uPNP
                writer = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}author')
                if writer != None:
                    writer_text = writer.text
                       
                content_rating_text = ''
                content_rating = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}content_rating')
                if content_rating != None:
                    content_rating_text = content_rating.text

                content_rating_text = ''                              # Kodi uPNP
                content_rating = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}rating')
                if content_rating != None:
                    content_rating_text = content_rating.text
              
                imdb_text = ''
                imdb = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}imdb_id')
                if imdb != None:
                    imdb_text = imdb.text
                                
                dcmInfo_text = '0'
                dcmInfo = item.find('.//{http://www.sec.co.kr/}dcmInfo')
                if dcmInfo != None:
                    dcmInfo_text = dcmInfo.text
                    valPos = dcmInfo_text.find('BM=') + 3
                    dcmInfo_text = dcmInfo_text[valPos:]
              
                rating_val = ''
                rating = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}rating')
                if rating != None:
                    rating_val = rating.text
                    rating_val = float(rating_val) * 2
                    rating_val = str(rating_val) #kodi ratings are out of 10, Mezzmo is out of 5

                rating_val = ''                                        # Kodi uPNP
                rating = item.find('.//{urn:schemas-xbmc-org:metadata-1-0/}userrating')
                if rating != None:
                    rating_val = rating.text
                
                production_company_text = ''
                production_company = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}production_company')
                if production_company != None:
                    production_company_text = production_company.text
                elif  production_company == None:                     # Bubble uPNP publisher
                    production_company = item.find('.//{http://purl.org/dc/elements/1.1/}publisher')
                    if production_company != None:
                        production_company_text = production_company.text
                    else:                                             # Jellyfin publisher
                        production_company = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}publisher')
                        if production_company != None:
                            production_company_text = production_company.text

                sort_title_text = ''
                sort_title = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}sort_title')
                if sort_title != None:
                    sort_title_text = sort_title.text    

                video_codec_text = ''
                video_codec = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}video_codec')
                if video_codec != None:
                    video_codec_text = video_codec.text
                if video_codec_text == 'vc1':     #  adjust for proper Kodi codec display
                    video_codec_text = 'vc-1'
                
                audio_codec_text = ''
                audio_codec = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}audio_codec')
                if audio_codec != None:
                    audio_codec_text = audio_codec.text
                
                audio_channels_text = '0'
                audio_channels = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}audio_channels')
                if audio_channels != None:
                    audio_channels_text = audio_channels.text               
                audio_lang = ''
                audio_streams = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}audio')
                if audio_streams != None:
                    for stream in audio_streams.findall('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}stream'):
                        if stream.get('selected') == 'auto' or stream.get('selected') == 'true':
                            audio_lang = stream.get('lang')
                            break
                     
                subtitle_lang = ''
                captions_streams = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}captions')
                if captions_streams != None:
                    for stream in captions_streams.findall('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}stream'):
                        if stream.get('selected') == 'auto' or stream.get('selected') == 'true':
                            subtitle_lang = stream.get('language')
                            break
                                   
                #mediaClass 
                if 'video' in upnpclass_text or 'video' in protocol_text:
                    mediaClass_text = 'video'
                if 'audio' in upnpclass_text or 'audio' in protocol_text:
                    mediaClass_text = 'music'
                if 'photo' in upnpclass_text or 'image' in protocol_text:
                    mediaClass_text = 'pictures'

                genmupos = 0                        
                if mediaClass_text == 'video':            
                    li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)') ])                
                    info = {
                        'duration': sync.getSeconds(duration_text),
                        'genre': genre_text,
                        'year': release_year_text,
                        'title': title,
                        'plot': description_text,
                        'director': creator_text,
                        'tagline': tagline_text,
                        'writer': writer_text,
                        'cast': artist_text,
                        'artist': artist_text,
                        'rating': rating_val,
                        'imdbnumber': imdb_text,
                        'mediatype': categories_text,
                        'season': season_text,
                        'episode': episode_text,
                        'lastplayed': last_played_text,
                        'aired': aired_text,
                        'mpaa':content_rating_text,
                        'studio':production_company_text,
                        'playcount':playcount,
                        'trailer':trailerurl,
                        'tvshowtitle':album_text,
                        'dateadded':date_added_text,
                    }
                    li.setInfo(mediaClass_text, info)
                    li.setProperty('ResumeTime', dcmInfo_text)
                    li.setProperty('TotalTime', str(sync.getSeconds(duration_text)))
                    video_info = {
                        'codec': video_codec_text,
                        'aspect': aspect,
                        'width': video_width,
                        'height': video_height,
                    }
                    li.addStreamInfo('video', video_info)
                    li.addStreamInfo('audio', {'codec': audio_codec_text, 'language': audio_lang, 'channels': int(audio_channels_text)})
                    li.addStreamInfo('subtitle', {'language': subtitle_lang})
                             
                elif mediaClass_text == 'music':
                    mtitle = media.displayTitles(title)					#  Normalize title
                    pctitle = '"' + mtitle.encode('utf-8','ignore')  + '"'  		#  Handle commas
                    #li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)') ])
                    #offsetmenu = 'Resume from ' + time.strftime("%H:%M:%S", time.gmtime(int(dcmInfo_text)))
                    if udynlist == 'true':
                        li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)'),  \
                        (menuitem9, 'RunScript(%s, %s, %s, %s)' % ("plugin.video.mezzmo", "playlist", muid, genmupos)) ])
                    else:
                        li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)') ]) 

                    info = {
                        'duration': sync.getSeconds(duration_text),
                        'genre': genre_text,
                        'year': release_year_text,
                        'title': pctitle,
                        'artist': artist_text,
                        'rating': rating_val,
                        'discnumber': season_text,
                        'mediatype': 'song',
                        'tracknumber': episode_text,
                        'album': album_text,
                        'playcount':playcount,
                        'lastplayed': last_played_text,
                    }                    
                    #mcomment = media.mComment(info, duration_text, offsetmenu[11:])
                    #info.update(comment = mcomment)
                    li.setInfo(mediaClass_text, info)
                    contentType = 'songs'
                    if udynlist == 'true':
                        genmulist.add(url=itemurl, listitem=li)

                elif mediaClass_text == 'pictures':
                    li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)'), \
                    (menuitem8, 'RunScript(%s, %s)' % ("plugin.video.mezzmo", "pictures")) ])                    
                    info = {
                        'title': title,
                    }
                    li.setInfo(mediaClass_text, info)
                    contentType = 'files'
                    picnotify += 1
                    itemdict = {
                        'title': title,
                         'url': itemurl,
                    }
                    piclist.append(itemdict)
                    if picnotify == int(NumberReturned):                   # Update picture DB
                        updatePictures(piclist)
                        if slideshow == 'true':                            # Slideshow display prompt
                            picDisplay()
                    itemurl = build_url({'mode': 'picture', 'itemurl': itemurl})                 
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=False)

            itemsleft = itemsleft - int(NumberReturned) - 1
            
            xbmc.log('Mezzmo items left: ' + str(itemsleft), xbmc.LOGDEBUG) 
            if itemsleft <= 0:
                break

            if pitemsleft == itemsleft:    #  Detect items left not incrementing 
                mgenlog ='Mezzmo items not displayed: ' + str(pitemsleft)
                xbmc.log(mgenlog, xbmc.LOGNOTICE)
                media.mgenlogUpdate(mgenlog)
                break
            else:
                pitemsleft = itemsleft            
                        
            # get the next items
            offset = int(TotalMatches) - itemsleft
            requestedCount = 1000
            if itemsleft < 1000:
                requestedCount = itemsleft

            pin = media.settings('content_pin')
            content = browse.Browse(contenturl, objectID, 'BrowseDirectChildren', offset, requestedCount, pin)        
    except Exception as e:
        media.printexception()
        pass
    setViewMode(contentType)
    if contentType == 'top' or contentType == 'folders':
        contentType = ''
    xbmcplugin.setContent(addon_handle, contentType)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_DURATION)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_TRACKNUM)
    xbmcplugin.endOfDirectory(addon_handle)


def gBrowse(url, objectID, flag, startingIndex, requestedCount, pin):
    global logcount     
    headers = {'content-type': 'text/xml', 'accept': '*/*', 'SOAPACTION' : '"urn:schemas-upnp-org:service:ContentDirectory:1#Browse"', 'User-Agent': 'Kodi (Mezzmo Addon)'}
    body = '''<?xml version="1.0"?>
    <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:Browse xmlns:u="urn:schemas-upnp-org:service:ContentDirectory:1">
     <ObjectID>'''
    body += objectID
    body += '''</ObjectID>
      <BrowseFlag>'''
    body += flag
    body += '''</BrowseFlag>
      <Filter>*,cva_richmetadata,cva_bookmark</Filter>
      <StartingIndex>'''
    body += str(startingIndex)
    body += '''</StartingIndex>
      <RequestedCount>'''
    body += str(requestedCount)
    body += '''</RequestedCount>'''
    body += '''<SortCriteria></SortCriteria>
    </u:Browse>
  </s:Body>
</s:Envelope>'''
    req = urllib2.Request(url, body, headers)
    response = ''
    try:
        response = urllib2.urlopen(req, timeout=gsrvrtime).read()
        if logcount < generic_response and generic_response > 0:
            xbmc.log(response.encode('utf-8'), xbmc.LOGNOTICE)
            logcount += 1
            media.settings('genrespcount', str(logcount))
        elif logcount >= generic_response and generic_response > 0:
            media.settings('generic_response', '0')            
            media.settings('genrespcount', '0')
            mgenlog = 'Mezzmo generic server response logging limit.'   
            xbmc.log(mgenlog, xbmc.LOGNOTICE)
            media.mgenlogUpdate(mgenlog) 
    except Exception as e:
        xbmc.log( 'EXCEPTION IN Browse: ' + str(e))
        pass
        
    return response

