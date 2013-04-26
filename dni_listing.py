#!/usr/bin/env python
# -*- coding: utf-8 -*-


from lxml import etree, html
import re
import sys
from datetime import date, datetime, tzinfo, timedelta


NUM_DAYS = 10
DATETIME_FMT = '%Y%m%d%H%M %Z'
EPISODE_RE = '^Ep(\.|isodio) (?P<ep_num>\d+)([\. -]+)?(?P<ep_title>.+)?$'
SERIES_RE = '^(?P<series_name>.+?) T(?P<season_num>\d+)$'
BASEURL = 'http://www.tudiscoverykids.com'

# <channel channel-code="APAR-SP" schedule-start="21600">Animal Planet</channel> - 64
# <channel channel-code="DCAR-SP" schedule-start="21600">Discovery Channel</channel> - 63
# <channel channel-code="DKAR-SP" schedule-start="21600">Discovery Kids</channel> - 25
# <channel channel-code="DHAR-SP" schedule-start="21600">Discovery Mujer</channel> - ??
# <channel channel-code="IDAR-SP" schedule-start="21600">Investigation Discovery</channel> - 49
# <channel channel-code="LVAR-SP" schedule-start="21600">LIV</channel> - ??
# <channel channel-code="TLCA-SP" schedule-start="21600">TLC</channel> - 69
# <channel channel-code="TLAR-SP" schedule-start="21600">Travel and Living</channel> - ??

CHANNELS = [
    ['7',  "APAR-SP", u'Animal Planet', u'Nature / Animals / Environment'],
    ['23', "DCAR-SP", u'Discovery Channel', u'Magazines / Reports / Documentary'],
    ['25', "DKAR-SP", u'Discovery Kids', u'Pre-school children\'s programmes'],
    ['48', "IDAR-SP", u'Investigation Discovery'],
    ['90', "TLCA-SP", u'TLC'],
]


class GMT (tzinfo):

    def __init__ (self, offset):
        self.__offset = timedelta(hours=offset)
        if offset < 0:
            sign = '-'
        else:
            sign = '+'
        self.__name = sign + '%02d' % abs(offset) + '00'

    def utcoffset (self, dt):
        return self.__offset

    def dst (self, dt):
        return timedelta(0)

    def tzname (self, dt):
        return self.__name

def dni_get_listings_by_day(for_date = None, channel_code = 'DKAR-SP', chan_num_str = '25', category = None):
    """
    """
    if for_date is None:
        for_date = date.today()
		
    date_formatted = for_date.strftime('%d%m%Y')
		
    
    theurl = BASEURL + '/dni-tvlistings/GetScheduleByBroadcastDate?channel_code=%s&date=%s' % (channel_code, date_formatted)
        
    try:
        data = etree.parse(theurl)
        #print etree.tostring(data)
        utc_offset_el = data.find(".//dni-listings/get-listings-by-day/utc-offset")
        if utc_offset_el is not None:
            utc_offset = int(uct_offset_el.text)
        else:
        	utc_offset = -3;
        
        programmes = []
        
        for prog in data.findall(".//programme"):
            p = {}
            #print etree.tostring(prog, pretty_print=True)
# 				<programme>
# 				  <channel-code-id>DKAR-SP</channel-code-id>
# 				  <channel-name>Discovery Kids</channel-name>
# 				  <channel-url>http://www.tudiscovery.com</channel-url>
# 				  <programme_id>1865104</programme_id>
# 				  <series_id>198193</series_id>
# 				  <start-time>
# 					<raw>0530</raw>
# 					<formatted>05:30:00</formatted>
# 				  </start-time>
# 				  <date>
# 					<raw>16042013</raw>
# 					<formatted>16 abr</formatted>
# 					<day>TUESDAY</day>
# 				  </date>
# 				  <duration-time>30</duration-time>
# 				  <series-title>HI-5 (AUSTRALIA) T13</series-title>
# 				  <programme-title>Ep. 11 - Amor</programme-title>
# 				  <programme-description>En este episodio se explora todo lo relacionado al amor: sensaciones c&#225;lidas pero confusas, y cosas que nos encanta hacer, como por ejemplo cantar.</programme-description>
# 				  <promo/>
# 				  <schedule-id>38144692DKAR</schedule-id>
# 				</programme>

            p['chan-num'] = chan_num_str
            if category is not None:
                p['category'] = category

            el = prog.find(".//channel-code-id")
            if el is not None:
            	p['channel-code-id'] = el.text
            	
            el = prog.find(".//channel-name")
            if el is not None:
            	p['channel-name'] = el.text
            	
            el = prog.find(".//channel-url")
            if el is not None:
            	p['channel-url'] = el.text
            	
            el = prog.find(".//programme_id")
            if el is not None:
            	p['programme_id'] = el.text
            	
            el = prog.find(".//series_id")
            if el is not None:
            	p['series_id'] = el.text
            	
            eltime = prog.find(".//start-time/raw")
            eldate = prog.find(".//date/raw")
        
            if eltime is not None and eldate is not None:
            	dttemp = datetime.strptime(eldate.text + " " + eltime.text,
            		'%d%m%Y %H%M').replace(tzinfo = GMT(-3))
            	p['starttime'] = dttemp.astimezone(GMT(0))
            	 
            	
            el = prog.find(".//duration-time")
            if el is not None:
            	p['duration-time'] = el.text

            el = prog.find(".//series-title")
            if el is not None:
            	p['series-title'] = el.text

            el = prog.find(".//programme-title")
            if el is not None:
            	p['programme-title'] = el.text

            el = prog.find(".//programme-description")
            if el is not None and el.text is not None:
            	p['programme-description'] = el.text

            el = prog.find(".//promo")
            if el is not None:
            	p['promo'] = el.text

            el = prog.find(".//schedule-id")
            if el is not None:
            	p['schedule-id'] = el.text
            	
            elimg = prog.find(".//promo/image/image-path")
            if elimg is not None:
                p['image'] = BASEURL + elimg.text
            	
            #print repr(p)
            programmes.append(p)
            
        return programmes
    except Exception, e:
        print >> sys.stderr, 'error: %s ' % unicode(e)

startdate = date.today()
progs = []
for chan in CHANNELS:
    cat = None
    if len(chan) > 3:
        cat = chan[3]
    for doff in range(NUM_DAYS):
        thedate = startdate + timedelta(days=doff)
        progs.extend(dni_get_listings_by_day(thedate, chan[1], chan[0], cat))

#print repr(progs)

tv = etree.Element('tv', { 'generator_info_name': "dni_listing",
                           'generator_info_url': "http://brickybox.com",
                           'source_info_name': BASEURL,
                           'source_info_url': BASEURL})

for chan in CHANNELS:
    channel = etree.SubElement(tv, 'channel', { 'id' : chan[0] })
    etree.SubElement(channel, 'display-name', { 'lang': 'es' }).text = chan[2]
    etree.SubElement(channel, 'display-name', { 'lang': 'es' }).text = chan[0]

re_series = re.compile(SERIES_RE)
re_episode = re.compile(EPISODE_RE)

for prog in progs:
    start_time = prog['starttime'].strftime(DATETIME_FMT)
    end_time = (prog['starttime'] + timedelta(minutes=int(prog['duration-time']))).strftime(DATETIME_FMT)
    
    series_name = prog['series-title']
    episode_name = prog['programme-title']
    season_num = -1
    episode_num = -1
    
    series_match = re_series.match(series_name)
    episode_match = re_episode.match(episode_name)
    
    if series_match:
    	series_name = series_match.group('series_name')
    	season_num = int(series_match.group('season_num'))
    	
    if episode_match:
    	if episode_match.group('ep_title') is not None:
    		episode_name = episode_match.group('ep_title')
    	episode_num = int(episode_match.group('ep_num'))
    
    #EPISODE_RE = '^(Ep(\.|isodio) (?P<ep_num>\d+)([\. -]+)?(?P<ep_title>.+)?$'
	#SERIES_RE = '^(?P<series_name>.+?) T(?P<season_num>\d+)$'

    programme = etree.SubElement(tv, 'programme', { 'start' : start_time, 
                                                 'stop' : end_time,
                                                 'channel' : prog['chan-num']})
    etree.SubElement(programme, 'title', { 'lang': 'es' }).text = series_name
    etree.SubElement(programme, 'sub-title', { 'lang': 'es' }).text = episode_name
    
    if prog.has_key('programme-description'):
        etree.SubElement(programme, 'desc', { 'lang': 'es' }).text = prog['programme-description']
    
    if prog.has_key('category'):
        etree.SubElement(programme, 'category', { 'lang': 'en' }).text = prog['category']
        
    if prog.has_key('image'):
        etree.SubElement(programme, 'icon').text = prog['image']
    
    if season_num > 0 or episode_num > 0:
    	# <episode-num system="xmltv_ns">8.7.</episode-num>
    	season_str = ''
    	episode_str = ''
    	if season_num > 0:
    		season_str = '%d' % (season_num - 1)
    	if episode_num > 0:
    		episode_str = '%d' % (episode_num - 1)
    	etree.SubElement(programme, 'episode-num', { 'system': 'xmltv_ns'}).text = '%s.%s.' % (season_str, episode_str)
    
    
print etree.tostring(tv, pretty_print=True, encoding='utf-8', xml_declaration=True)
    
# {'programme-title': 'Ep. 15 - Mis cosas favoritas', 
# 'channel-code-id': 'DKAR-SP', 
# 'promo': None, 
# 'programme_id': '1865108', 
# 'series-title': 'HI-5 (AUSTRALIA) T13', 
# 'duration-time': '30', 
# 'series_id': '198193', 
# 'channel-url': 'http://www.tudiscovery.com', 
# 'schedule-id': '38144696DKAR', 
# 'programme-description': u'Las mejores cosas vienen en distintos tama\xf1os y formas y el episodio de hoy trata de tesoros accesibles que provocan bienestar.', 
# 'starttime': datetime.datetime(2013, 4, 22, 8, 30, tzinfo=<__main__.GMT object at 0x104547bd0>), 
# 'channel-name': 'Discovery Kids'}
