#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmcaddon, xbmc, xbmcgui, xbmcplugin
import urllib, re, string, os, urllib2, cookielib
import xml.dom.minidom
from threading import Timer


# Plugin config
config = xbmcaddon.Addon(id='plugin.video.hdout.tv')
lang = config.getLocalizedString
login = config.getSetting('login')
password = config.getSetting('password')

handle = int(sys.argv[1])
thumb = os.path.join(os.getcwd().replace(';', ''), "icon.png")

plugin = 'HDOut.TV'
rootURL = 'https://hdout.tv/' 


class HDOPlayer(xbmc.Player):
    episode_id = 0
    c_time = 0
   
    def playEpisode(self, eid, videourl, item):
        self.episode_id = eid
        self.play(videourl, item)
        
    def onPlayBackPaused(self):
        self.report()

    def onPlayBackSeek(self, time, seekOffset):
        self.report()
        
    def onPlayBackStopped(self):
        self.episode_id = 0
        
    def onPlayBackEnded(self):
        self.episode_id = 0

    def is_playing(self):
        return self.episode_id > 0

    def report(self):
        if self.episode_id > 0:
            ping()
            try:
                time = self.getTime()
                if time and time > 0 and time != self.c_time:
                    url = "?usecase=UpdateViewTime&t=" + str(time) + "&eid=" + str(self.episode_id)
                    get(url)
                    self.c_time = time
            except:
                pass

hdoplayer = HDOPlayer()


def showSeries(pv):
    return showSeriesList("List/all/XML/", True, False)

def showMySeries(pv):
    return showSeriesList("List/my/XML/", False, True)

def showEpisodes(pv):
    global handle, plugin, lang, rootURL
    
    s = get("Series/" + pv['id'] + "/XML/")
    if s == None:
        showMessage(lang(30003), lang(30004))
        return False
    d = xml.dom.minidom.parseString(s)
    sl = d.getElementsByTagName('series')
    if sl:
        mark = getVal(sl[0], 'mark');
        server = getVal(sl[0], 'server');
        tp = getVal(sl[0], 'type');
        sli = sl[0].getElementsByTagName('season')
        if sli:
            for i in sli:
                si = i.getElementsByTagName('item')
                for e in si:
                    id = getVal(e, 'id_episodes')
                    series = getVal(e, 'series')

                    snum = int(getVal(e, 'snum'))
                    enum = int(getVal(e, 'enum'))
                    vnum = getVal(e, 'vnum')
                    title = getVal(e, 'title')
                    etitle = getVal(e, 'etitle')
                    
                    if tp == '1': img = rootURL + "v/%s/sd/%s/%02d-%02d.jpg" % (server, mark, snum, enum)
                    else: img = rootURL + "v/%s/hd/%s/sc/%02d-%02d.jpg" % (server, mark, snum, enum)
                    
                    ftitle = fTitle(title, etitle, snum, vnum)
                    url = sys.argv[0] + '?f=showEpisode&id=' + id
                
                    item = xbmcgui.ListItem(ftitle, iconImage=img, thumbnailImage=img)
                    item.setInfo(type='video', infoLabels={
                        'id': "hdout_tv_episode_" + id,
                        'title': ftitle, 
                        'season': snum,
                        'episode': enum
                        })
                    item.setProperty('fanart_image', img)
                    xbmcplugin.addDirectoryItem(handle, url, item, True)

            xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_EPISODE)
            xbmcplugin.endOfDirectory(handle)
        else:
            showMessage(lang(30003), lang(30005))
    else:
        showMessage(lang(30003), lang(30005))
    return True

def showEpisode(pv):
    global hdoplayer, handle, plugin, lang
    
    s = get("EpisodeLink/" + pv['id'] + "/XML/")
    if s == None:
        showMessage(lang(30003), lang(30004))
        return False

    d = xml.dom.minidom.parseString(s)
    i = d.getElementsByTagName('item')
    if i and len(i) > 0:
        snum = int(getVal(i[0], 'snum'))
        enum = int(getVal(i[0], 'enum'))
        vnum = getVal(i[0], 'vnum')

        title = getVal(i[0], 'title')
        etitle = getVal(i[0], 'etitle')

        smark = getVal(i[0], 'smark')
        server = getVal(i[0], 'server')
        series = getVal(i[0], 'series')

        j = i[0].getElementsByTagName('seriesitem')
        seriestitle = getVal(j[0], 'title') if j else ""
        seriesetitle = getVal(j[0], 'etitle') if j else ""

        scurl = getVal(i[0], 'scurl')
        suburl = getVal(i[0], 'suburl')
        videourl = getVal(i[0], 'videourl')
        sub_f = int(getVal(i[0], 'sub_f'))

        sub_en = int(getVal(i[0], 'sub_en'))
        sub_ru = int(getVal(i[0], 'sub_ru'))
        tp = int(getVal(i[0], 'tp'))

        ftitle = fTitle(seriestitle, seriesetitle, 0, "0") + " / " + fTitle(title, etitle, snum, vnum)
        
        item = xbmcgui.ListItem(ftitle, iconImage=scurl, thumbnailImage=scurl)
        item.setInfo(type='video', infoLabels={
            'id': "hdout_tv_episode_" + pv['id'],
            'title':  ftitle, 
            'season': snum, 
            'episode': enum })
        hdoplayer.playEpisode(pv['id'], videourl, item)
        xbmc.sleep(3000)
        
        sub = int(config.getSetting('subhd'))
        if sub == 1 and sub_ru == 1: 
            appendSubtitle(smark, "ru", suburl)
        elif sub == 2 and sub_en == 1: 
            appendSubtitle(smark, "en", suburl)
        elif sub_f == 1: 
            appendSubtitle(smark, "f", suburl)

        k = 0
        while hdoplayer.is_playing():
            if xbmc.Monitor().abortRequested():
                break
            xbmc.sleep(1000)
            k = k + 1
            if k > 180:
                hdoplayer.report()
                k = 0

    else:
        e = d.getElementsByTagName('error')
        if e and len(e) > 0:
            et = getVal(e[0], "type")
            if type == "notfound":
                showMessage(lang(30003), lang(30006))
                return False
            elif type == "nomoney":
                showMessage(lang(30003), lang(30007))
                return False
            else:
                showMessage(lang(30003), lang(30008))
                return False
        else:
            showMessage(lang(30003), lang(30008))
            return False
    return True

def showRSS(pv):
    s = get("RSS/")
    return rss(s)

def showMyRSS(pv):
    uid = config.getSetting('uid')
    if uid and len(uid) > 0:
        s = get("UserRSS/" + uid + "/")
        return rss(s)
    else:
        auth()
        return showMyRSS(pv)


def openSettings(pv):
    global config

    config.openSettings()
    config.setSetting('sidhd', '')
    config.setSetting('uid', '')
    xbmc.sleep(30)

def addToFav(pv):
    s = get('AddToFavorites/' + pv['id'] + '/')
    if s == None:
        showMessage(lang(30003), lang(30004))
        return False

def rmFromFav(pv):
    s = get('RemoveFromFavorites/' + pv['id'] + '/')
    if s == None:
        showMessage(lang(30003), lang(30004))
        return False
    xbmc.sleep(10)
    xbmc.executebuiltin('Container.Refresh')


def default(pv):
    global handle 
    
    addMenu(30010, sys.argv[0] + '?f=showSeries')
    addMenu(30011, sys.argv[0] + '?f=showMySeries')
    addMenu(30012, sys.argv[0] + '?f=showRSS')
    addMenu(30013, sys.argv[0] + '?f=showMyRSS')
    
    addMenu(30050, sys.argv[0] + '?f=openSettings')
    xbmcplugin.endOfDirectory(handle)

def init():
    global config, login, password, lang
    
    while not auth():
        user_keyboard = xbmc.Keyboard()
        user_keyboard.setHeading(lang(30001))
        user_keyboard.doModal()
        if user_keyboard.isConfirmed():
            login = user_keyboard.getText()
            pass_keyboard = xbmc.Keyboard()
            pass_keyboard.setHeading(lang(30002))
            pass_keyboard.setHiddenInput(True)
            pass_keyboard.doModal()
            if pass_keyboard.isConfirmed():
                password = pass_keyboard.getText()
                config.setSetting('login', login)
                config.setSetting('password', password)
            else: return False
        else: return False
    return True


def rss(s):
    global handle, plugin, lang
    
    if s == None:
        showMessage(lang(30003), lang(30004))
        return False
    d = xml.dom.minidom.parseString(s)
    sl = d.getElementsByTagName('item')
    if sl:
        for i in sl:
            title = getVal(i, 'title')
            link = getVal(i, 'link')
            image = getVal(i, 'image')
            tumbnail = getVal(i, 'tumbnail')
            
            ub = re.search("/Episode/([0-9]*)/", link)
            if ub:
                url = sys.argv[0] + '?f=showEpisode&id=' + ub.group(1)
                item = xbmcgui.ListItem(title, iconImage=tumbnail, thumbnailImage=tumbnail)
                item.setInfo(type='video', infoLabels={
                    'id': "hdout_tv_episode_" +  ub.group(1),
                    'title': title})
                item.setProperty('fanart_image', image)
                xbmcplugin.addDirectoryItem(handle, url, item, True)
        xbmcplugin.endOfDirectory(handle)
    else:
        showMessage(lang(30003), lang(30005))
    return True

def showSeriesList(u, afv, rfv):
    global handle, plugin, rootURL, lang
    
    s = get(u)
    if s == None:
        showMessage(lang(30003), lang(30004))
        return False
    d = xml.dom.minidom.parseString(s)
    sl = d.getElementsByTagName('serieslist')
    if sl:
        sli = sl[0].getElementsByTagName('item')
        if sli:
            for i in sli:
                id = getVal(i, 'id_series');
                title = getVal(i, 'title');
                etitle = getVal(i, 'etitle');
                info = stripHTML(getVal(i, 'info'));
                mark = getVal(i, 'mark');
                tp = getVal(i, 'type');
                
                img = rootURL + "static/c/s/" + mark + ".jpg"
                bimg = rootURL + "static/c/b/" + mark + ".jpg"
                if tp == '1':
                    title = "[SD] " + title + " (" + etitle + ")"
                else:
                    title = "[HD] " +  title + " (" + etitle + ")"
                url = sys.argv[0] + '?f=showEpisodes&id=' + id
                
                item = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
                item.setInfo(type='video', infoLabels={
                    'id': "hdout_tv_series_hd_" + id,
                    'title': title, 
                    'plot': info})
                item.setProperty('fanart_image', bimg)
                
                if afv: item.addContextMenuItems([(lang(30301), 'XBMC.RunPlugin(%s?f=addToFav&id=%s)' % (sys.argv[0], id),)])
                if rfv: item.addContextMenuItems([(lang(30302), 'XBMC.RunPlugin(%s?f=rmFromFav&id=%s)' % (sys.argv[0], id),)])
                
                xbmcplugin.addDirectoryItem(handle, url, item, True)
                
            xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_TITLE)
            xbmcplugin.endOfDirectory(handle)
        else:
            showMessage(lang(30003), lang(30005))
    else:
        showMessage(lang(30003), lang(30005))
    return True

# utility functions
def get(url):
    global config, rootURL

    sid = config.getSetting('sidhd')
    if len(sid) < 2:
        if auth(): sid = config.getSetting('sidhd')
        else: return None

    request = urllib2.Request(rootURL + url, None)
    request.add_header('Cookie', 'SID=' + sid)

    o = urllib2.urlopen(request)
    page = o.read()
    o.close()

    if page.find('<form id="loginform"') == -1:  return page
    else:
        if auth(): return get(url) 
        else: return None

def auth():
    global config, rootURL

    r = False
    params = urllib.urlencode(dict(login=config.getSetting('login'), password=config.getSetting('password'),iapp=1))
    f = urllib2.urlopen(rootURL, params)
    d = f.read()
    f.close()
    if d.find('<form id="loginform"') == -1:  
        try:
            ad = xml.dom.minidom.parseString(d)
            sid = getVal(ad, 'SID')
            if sid and len(sid) > 2:
                config.setSetting('sidhd', sid)
                r = True
            uid = getVal(ad, 'UID')
            if uid and len(uid) > 0:
                config.setSetting('uid', uid)
        except:
            r = False
            pass
    return r

def fTitle(title, etitle, snum, vnum):
    if title and len(title) > 1: 
        ftitle = title 
        if etitle and len(etitle) > 1: ftitle += " (" + etitle + ")"    
    else: ftitle = etitle
    if snum != 0 and vnum != "0":
        ftitle = ftitle + (" [%dx%s]" % (snum, vnum))
    return ftitle

def getVal(d, tag):
    r = None
    try: 
        r = d.getElementsByTagName(tag)[0].childNodes[0].nodeValue.strip().encode('utf-8')
    except:
        pass
    return r

def getParams(dv):
    param = dv
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'): params = params[0:len(params)-2]
        pairsofparams = cleanedparams.split('&')
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2: param[splitparams[0]] = splitparams[1]
    return param

def stripHTML(text):
    def fixup(m):
        text = m.group(0)
        if text[:1] == "<":
            if text[1:3] == 'br': return '\n'
            else: return ""
        if text[:2] == "&#":
            try:
                if text[:3] == "&#x": return chr(int(text[3:-1], 16))
                else: return chr(int(text[2:-1]))
            except ValueError: pass
        elif text[:1] == "&":
            import htmlentitydefs
            if text[1:-1] == "mdash": entity = " - "
            elif text[1:-1] == "ndash": entity = "-"
            elif text[1:-1] == "hellip": entity = "-"
            else: entity = htmlentitydefs.entitydefs.get(text[1:-1])
            if entity:
                if entity[:2] == "&#":
                    try: return chr(int(entity[2:-1]))
                    except ValueError: pass
                else: return entity
        return text
    ret = re.sub("(?s)<[^>]*>|&#?\w+;", fixup, text) if text else ""
    return re.sub("\n+", '\n' , ret)

def ping():
    get("PingUser/")

# XBMC misc  
def showMessage(head, message, times = 10000):
    xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, "%s")' % (head.encode('utf-8'), message.encode('utf-8'), times, thumb))

def addMenu(ids, uri):
    global handler, thumb, lang
    
    item = xbmcgui.ListItem(lang(ids), iconImage=thumb, thumbnailImage=thumb)
    xbmcplugin.addDirectoryItem(handle, uri, item, True)

def appendSubtitle(smark, ln, suburl):
    global hdoplayer

    url = suburl + smark + "_" + ln
    surl = None 
    try: 
        surl = url + ".srt"
        sf = urllib2.urlopen(surl, None)
    except: 
        surl = None 
        pass
    
    if surl == None:
        try: 
            surl = url + ".ass"
            sf = urllib2.urlopen(surl, None)
        except: 
            surl = None
            pass
         
    if surl <> None: 
        hdoplayer.setSubtitles(surl)


# Main processing
if init():
    pv = { 'f': None, 'id': 0 }
    funs = ['showSeries', 'showMySeries', 'showEpisodes', 'showEpisode', 'showRSS', 'showMyRSS', 'openSettings', 'addToFav', 'rmFromFav']
    
    pvm = getParams(pv)
    ping()
    if pvm['f'] in funs: 
        eval(pvm['f'] + "(pv)")
    else: 
        default(pv)
