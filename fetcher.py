#!/usr/bin/env python

from google.appengine.ext import ndb
import urllib2
import xml.etree.ElementTree as el
import datetime
import re

class AirData(ndb.Model):
    cityname = ndb.StringProperty(indexed=True)
    value = ndb.IntegerProperty()
    datetime = ndb.DateTimeProperty()


def databook_key(cityname):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('Databook', cityname)


class Fetcher(object):
    
    cities = {"Beijing" : 1,
              "Chengdu" : 2,
              "Guangzhou" : 3,
              "Shanghai" : 4,
              "Shenyang" : 5,
              }
    
    def __init__(self):
        pass
    
    def fetch(self):
        for cityname in self.cities.keys():
            cty = CityData(cityname)
            cty.fetchdata()
    

class CityData(object):
    """
    Gathers data for specific city.
    """
    
    cities = {"Beijing" : 1,
              "Chengdu" : 2,
              "Guangzhou" : 3,
              "Shanghai" : 4,
              "Shenyang" : 5,
              }
    
    def __init__(self, cityname):
        self.cityname = cityname
    
    def fetchdata(self):
        lastread = self.getlastread()
        
        u = urllib2.urlopen(
            "http://www.stateair.net/web/rss/1/{}.xml".format(
                self.cities[self.cityname]))
        rss = u.read() # get data
        u.close()
        
        rtree = el.fromstring(rss) # parse
        
        # reads data.
        buff = []
        for i in rtree.iter('item'):
            itsReadingDateTime = i.find("ReadingDateTime").text
            itsdatetime = rdt_to_datetime(itsReadingDateTime)
            if itsdatetime == lastread: 
                # reached to the last read item
                break
            else:
                #if type(itsdatetime) != type(lastread):
                #    raise TypeError,""" itsdatetime : {}, lastread: {}""".format(
                # the above : was not raised.
                #        type(itsdatetyme), type(lastread))
                buff.append((itsdatetime,
                             int(float(i.find("Conc").text))))
        
        for datum in reversed(buff): # add to database
            self.add_to_database(datum)
        
        currentread = list(rtree.iter('item'))[0].find("ReadingDateTime").text
        self.update_lastread(rdt_to_datetime(currentread))
    
    def add_to_database(self, datum):
        dtime = datum[0]
        conc = datum[1]
        newdatum = AirData(parent=databook_key(self.cityname))
        newdatum.cityname = self.cityname
        newdatum.value = conc
        newdatum.datetime = dtime
        newdatum.put()
    
    def getlastread(self):
        try:
            data_query = AirData.query(
                ancestor = databook_key(self.cityname)).order(-AirData.datetime)
            return data_query.fetch(1)[0].datetime
        except IndexError:
            return None
    def update_lastread(self, newdatetime):
        pass

def rdt_to_datetime(rdt):
    list_of_digits = re.split('\W+', rdt)
    year = int(list_of_digits[2])
    month = int(list_of_digits[0])
    day = int(list_of_digits[1])
    hour = int(list_of_digits[3]) + 12*(list_of_digits[-1] == 'PM')
    if hour == 24:
        hour = 12
    elif hour == 12:
        hour = 0
    return datetime.datetime(year, month, day, hour)


def main():
    Fetcher().fetch()

if __name__ == '__main__':
    main()
