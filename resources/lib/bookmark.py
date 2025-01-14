import urllib2
import urllib
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import media


def SetBookmark(url, objectID, pos):

    
    headers = {'content-type': 'text/xml', 'accept': '*/*', 'SOAPACTION' : '"urn:schemas-upnp-org:service:ContentDirectory:1#X_SetBookmark"', 'User-Agent': 'Kodi (Mezzmo Addon)'}
    body = '''<?xml version="1.0"?>
    <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:X_SetBookmark xmlns:u="urn:schemas-upnp-org:service:ContentDirectory:1">
     <ObjectID>'''
    body += objectID
    body += '''</ObjectID>
      <PosSecond>'''
    body += pos
    body += '''</PosSecond>
    </u:X_SetBookmark>
  </s:Body>
</s:Envelope>'''
    req = urllib2.Request(url, body, headers)
    response = ''
    try:
        response = urllib2.urlopen(req, timeout=60).read()
    except Exception as e:
        xbmc.log( 'EXCEPTION IN SetBookmark: ' + str(e))
        pass
        
    return response


def updateKodiBookmark(file, pos, title, mtype, dbfile=1):    # Update Kodi bookmark

    if media.settings('kbooksync') == 'false':           # Kodi bookmark sync disabled
        return

    if mtype == 'audiom':                                #  Don't update Kodi for music
        return

    if dbfile == 1:
        db = media.openKodiDB()
        dbflag = 1
    else:
        db = dbfile
        dbflag = 0
    
    mtitle = title

    xbmc.log('Mezzmo bookmark info: ' + str(file) + ' ' + str(pos) + ' ' + mtitle.encode('utf-8','ignore') \
    + ' ' + title.encode('utf-8','ignore'), xbmc.LOGDEBUG)

    musicvid = media.settings('musicvid')                # Check if musicvideo sync is enabled
    if mtype == 'musicvideo' and musicvid == 'true':     # Find musicvideo file number
        curb = db.execute('select files.idFile, c04, c13 from files inner join musicvideo on           \
        files.idFile=musicvideo.idFile where c00=?', (mtitle,))      
        mtuple = curb.fetchone()                         # Check for existing musicvideo    
        if mtuple:                                       # create bookmark
            #xbmc.log('Mezzmo musicvideo found: ' + str(mtuple[0]) + ' ' + str(pos) + ' ' + str(len(mtitle)), xbmc.LOGNOTICE)
            curm = db.execute('select idBookmark from bookmark where idFile=?', (mtuple[0],))
            mbtuple = curm.fetchone()
            if not mbtuple and len(mtitle) > 2 and int(pos) > 0:  # Not found.  Create new bookmark.
                xbmc.log('Mezzmo musicvideo not bookmark found: ' + str(mtuple[0]), xbmc.LOGDEBUG)
                db.execute('INSERT into bookmark (idFile, timeInSeconds, totalTimeInSeconds, player, type) \
                values (?, ?, ?, ?, ?)',  (mtuple[0], pos, mtuple[1], "VideoPlayer", "1", ))   
            elif len(mtitle) < 3:
                if dbflag == 1: db.commit(); db.close()           
                return
            elif int(pos) > 0 and len(mtitle) > 2:     # Musicvideo bookmark found
                xbmc.log('Mezzmo musicvideo bookmark found: ' + str(mbtuple[0]) + ' ' + str(pos), xbmc.LOGDEBUG)
                db.execute('UPDATE bookmark SET timeInSeconds=? WHERE idBookmark=?', (pos, mbtuple[0],))  
            elif int(pos) == 0 and len(mtitle) > 2:    # Musicvideo bookmark found to delete
                #xbmc.log('Mezzmo musicvideo bookmark found2: ' + str(mbtuple[0]) + ' ' + str(pos), xbmc.LOGNOTICE)
                db.execute('DELETE from bookmark WHERE idFile=?', (mtuple[0],))
            if dbflag == 1: db.commit(); db.close() 
            return

    elif mtype == 'episode':                           # Find episode bookmark
        curb = db.execute('select files.idFile, c09, c18 from files inner join episode on           \
        files.idFile=episode.idFile where c00=?', (mtitle,))      
        mtuple = curb.fetchone()                       # Check for existing episode    
        if mtuple:                                     # create bookmark
            #xbmc.log('Mezzmo episode found: ' + str(mtuple[0]) + ' ' + str(pos) + ' ' + str(len(mtitle)), xbmc.LOGNOTICE)
            curm = db.execute('select idBookmark from bookmark where idFile=?', (mtuple[0],))
            mbtuple = curm.fetchone()
            if not mbtuple and len(mtitle) > 2 and int(pos) > 0:  # Not found.  Create new bookmark.
                xbmc.log('Mezzmo episode not bookmark found: ' + str(mtuple[0]), xbmc.LOGDEBUG)
                db.execute('INSERT into bookmark (idFile, timeInSeconds, totalTimeInSeconds, player, type) \
                values (?, ?, ?, ?, ?)',  (mtuple[0], pos, mtuple[1], "VideoPlayer", "1", ))   
            elif len(mtitle) < 3:
                if dbflag == 1: db.commit(); db.close()           
                return
            elif int(pos) > 0 and len(mtitle) > 2:     # episode bookmark found
                xbmc.log('Mezzmo episode bookmark found: ' + str(mbtuple[0]) + ' ' + str(pos), xbmc.LOGDEBUG)
                db.execute('UPDATE bookmark SET timeInSeconds=? WHERE idBookmark=?', (pos, mbtuple[0],))
            elif int(pos) == 0 and len(mtitle) > 2:    # episode bookmark found to delete
                #xbmc.log('Mezzmo episode bookmark found2: ' + str(mbtuple[0]) + ' ' + str(pos), xbmc.LOGNOTICE)
                db.execute('DELETE from bookmark WHERE idFile=?', (mtuple[0],))
            if dbflag == 1: db.commit(); db.close() 
            return

    else:                                              # Find movie bookmark
        curb = db.execute('select files.idFile, c11, c22 from files inner join movie on           \
        files.idFile=movie.idFile where c00=?', (mtitle,))      
        mtuple = curb.fetchone()                       # Check for existing movie    
        if mtuple:                                     # create bookmark
            #xbmc.log('Mezzmo movie found: ' + str(mtuple[0]) + ' ' + str(pos) + ' ' + str(len(mtitle)), xbmc.LOGNOTICE)
            curm = db.execute('select idBookmark from bookmark where idFile=?', (mtuple[0],))
            mbtuple = curm.fetchone()
            if not mbtuple and len(mtitle) > 2 and int(pos) > 0:  # Not found.  Create new bookmark.
                xbmc.log('Mezzmo movie not bookmark found: ' + str(mtuple[0]), xbmc.LOGDEBUG)
                db.execute('INSERT into bookmark (idFile, timeInSeconds, totalTimeInSeconds, player, type) \
                values (?, ?, ?, ?, ?)',  (mtuple[0], pos, mtuple[1], "VideoPlayer", "1", ))   
            elif len(mtitle) < 3:
                if dbflag == 1: db.commit(); db.close()           
                return
            elif int(pos) > 0 and len(mtitle) > 2:     # Movie bookmark found
                xbmc.log('Mezzmo movie bookmark found: ' + str(mbtuple[0]) + ' ' + str(pos), xbmc.LOGDEBUG)
                db.execute('UPDATE bookmark SET timeInSeconds=? WHERE idBookmark=?', (pos, mbtuple[0],))  
            elif int(pos) == 0 and len(mtitle) > 2:    # Movie bookmark found to delete
                #xbmc.log('Mezzmo movie bookmark found2: ' + str(mbtuple[0]) + ' ' + str(pos), xbmc.LOGNOTICE)
                db.execute('DELETE from bookmark WHERE idFile=?', (mtuple[0],))
            if dbflag == 1: db.commit(); db.close() 
            return