# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

import urllib
import generic
import sickbeard

try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree

from sickbeard import exceptions, logger
from sickbeard import tvcache, show_name_helpers

class NZBsRUSProvider(generic.NZBProvider):
    def __init__(self):
        generic.NZBProvider.__init__(self, "NZBs'R'US")
        self.cache = NZBsRUSCache(self)
        self.url = 'https://www.nzbsrus.com/'
        self.supportsBacklog = True

    def isEnabled(self):
        return sickbeard.NZBSRUS

    def _checkAuth(self):
        if sickbeard.NZBSRUS_UID in (None, "") or sickbeard.NZBSRUS_HASH in (None, ""):
            raise exceptions.AuthException("NZBs'R'US authentication details are empty, check your config")

    def _get_season_search_strings(self, show, season, episode, abd=False):
        return ['^' + x for x in show_name_helpers.makeSceneSeasonSearchString(show, season, episode, abd)]

    def _get_episode_search_strings(self, show, season, episode, abd=False):
        return ['^' + x for x in show_name_helpers.makeSceneSearchString(show, season, episode, abd)]

    def _doSearch(self, search, show=None, age=None):
        params = {'uid': sickbeard.NZBSRUS_UID,
                  'key': sickbeard.NZBSRUS_HASH,
                  'xml': 1,
                  'age': sickbeard.USENET_RETENTION,
                  'lang0': 1,  # English only from CouchPotato
                  'lang1': 1,
                  'lang3': 1,
                  'c91': 1,  # TV:HD
                  'c104': 1,  # TV:SD-x264
                  'c75': 1,  # TV:XviD
                  'searchtext': search}

        if not params['age']:
            params['age'] = 500

        searchURL = self.url + 'api.php?' + urllib.urlencode(params)
        logger.log(u"NZBS'R'US search url: " + searchURL, logger.DEBUG)

        data = self.getRSSFeed(searchURL)
        if not data:
            return []

        items = data.entries
        if not len(items) > 0:
            logger.log(u"Error trying to parse NZBS'R'US XML data.", logger.ERROR)
            logger.log(u"RSS data: " + data, logger.DEBUG)
            return []

        return items

    def _get_title_and_url(self, item):
        if item.title:  # RSS feed
            title = item.title
            url = item.link
        else:  # API item
            title = item.name
            nzbID = item.id
            key = item.key
            url = self.url + 'nzbdownload_rss.php' + '/' + \
                  nzbID + '/' + sickbeard.NZBSRUS_UID + '/' + key + '/'
        return (title, url)


class NZBsRUSCache(tvcache.TVCache):
    def __init__(self, provider):
        tvcache.TVCache.__init__(self, provider)
        # only poll NZBs'R'US every 15 minutes max
        self.minTime = 15

    def _getRSSData(self):
        url = self.provider.url + 'rssfeed.php?'
        urlArgs = {'cat': '91,75,104',  # HD,XviD,SD-x264
                   'i': sickbeard.NZBSRUS_UID,
                   'h': sickbeard.NZBSRUS_HASH}

        url += urllib.urlencode(urlArgs)
        logger.log(u"NZBs'R'US cache update URL: " + url, logger.DEBUG)

        data = self.provider.getRSSFeed(url)
        return data

    def _checkAuth(self, data):
        return data != 'Invalid Link'


provider = NZBsRUSProvider()
