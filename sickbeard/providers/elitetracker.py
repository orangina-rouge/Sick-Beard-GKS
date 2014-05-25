# Author: Tenshy <orangina.rouge@gmail.com>
#
# This file is based upon torrentleech.py and ezrss.py.
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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

import urllib
import re
try:
    import xml.etree.cElementTree as etree
except ImportError:
    import elementtree.ElementTree as etree

import sickbeard
import generic

from sickbeard.common import Quality
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import helpers

class EliteTrackerProvider(generic.TorrentProvider):

    def __init__(self):
        generic.TorrentProvider.__init__(self, "ELITETRACKER")

        self.supportsBacklog = False
        self.cache = EliteTrackerCache(self)
        self.url = 'https://elite-tracker.net/'

    def isEnabled(self):
        return sickbeard.ELITETRACKER

    def imageName(self):
        return 'elitetracker.png'

    def _checkAuth(self):

        if not sickbeard.ELITETRACKER_KEY:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")
        return True

    def _checkAuthFromData(self, parsedXML):

        if parsedXML is None:
            return self._checkAuth()

        description_text = helpers.get_xml_text(parsedXML.find('.//channel/item/description'))

        if "Your RSS key is invalid" in description_text:
            logger.log(u"Incorrect authentication credentials for " + self.name + " : " + str(description_text), logger.DEBUG)
            raise AuthException(u"Your authentication credentials for " + self.name + " are incorrect, check your config")

        return True

    def getQuality(self, item):

        filename = helpers.get_xml_text(item.find('title'))
        quality = Quality.nameQuality(filename)

        return quality

    def findSeasonResults(self, show, season):

        results = {}

        if show.air_by_date:
            logger.log(self.name + u" doesn't support air-by-date backlog because of limitations on their RSS search.", logger.WARNING)
            return results

        results = generic.TorrentProvider.findSeasonResults(self, show, season)

        return results

    def _get_season_search_strings(self, show, season=None):

        params = {}

        if not show:
            return params

        params['q'] = helpers.sanitizeSceneName(show.name, ezrss=False).replace('.', ' ').encode('utf-8')
        params['ak'] = sickbeard.ELITETRACKER_KEY

        if season != None:
            params['q'] = helpers.sanitizeSceneName(show.name, ezrss=False).replace('.', ' ').encode('utf-8')+" S%02d" % (season)

        return [params]

    def _get_episode_search_strings(self, ep_obj):

        params = {}

        if not ep_obj:
            return params
        
        params['ak'] = sickbeard.ELITETRACKER_KEY

        params['q'] = helpers.sanitizeSceneName(ep_obj.show.name, ezrss=False).replace('.', ' ').encode('utf-8')+" S%02dE%02d" % (ep_obj.season, ep_obj.episode)

        return [params]

    def _doSearch(self, search_params, show=None):
        #TODO
        return []
        params = {"mode": "rss"}

        if search_params:
            params.update(search_params)

        search_url = self.url + 'rdirect.php?type=search&order=desc&sort=normal&' + urllib.urlencode(params)

        logger.log(u"Search string: " + search_url, logger.DEBUG)

        data = self.getURL(search_url)

        if not data:
            logger.log(u"No data returned from " + search_url, logger.ERROR)
            return []

        parsedXML = helpers.parse_xml(data)

        if parsedXML is None:
            logger.log(u"Error trying to load " + self.name + " RSS feed", logger.ERROR)
            return []

        items = parsedXML.findall('.//channel/item')

        results = []

        for curItem in items:

            (title, url) = self._get_title_and_url(curItem)

            if title and url:
                logger.log(u"Adding item from RSS to results: " + title, logger.DEBUG)
                results.append(curItem)
            else:
                logger.log(u"The XML returned from the " + self.name + " RSS feed is incomplete, this result is unusable", logger.ERROR)

        return results

    def _get_title_and_url(self, item):
        (title, url) = generic.TorrentProvider._get_title_and_url(self, item)
        return (title, url)

class EliteTrackerCache(tvcache.TVCache):

    def __init__(self, provider):
        tvcache.TVCache.__init__(self, provider)

        # only poll every 15 minutes
        self.minTime = 15

    def _getRSSData(self):

        rss_url = 'https://elite-tracker.net/rss.php?secret_key=' + sickbeard.ELITETRACKER_KEY + '&feedtype=download&timezone=-12&showrows=50&categories=all'
        logger.log(self.provider.name + u" cache update URL: " + rss_url, logger.DEBUG)

        data = self.provider.getURL(rss_url)

        if not data:
            logger.log(u"No data returned from " + rss_url, logger.ERROR)
            return None

        return data

    def _checkAuth(self, parsedXML):
            return self.provider._checkAuthFromData(parsedXML)

provider = EliteTrackerProvider()
