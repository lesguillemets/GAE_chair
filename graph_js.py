#!/usr/bin/env python
# encoding:utf-8

import webapp2
from google.appengine.ext import ndb
from fetcher import AirData, databook_key

PLOT_HEAD = """\
<html>
  <head>
  <meta charset="UTF-8">
  <title>Chair viewer</title>
  <link style="text/css" rel="stylesheet" href="./css/airrank.css"/>
    <script type="text/javascript" src="https://www.google.com/jsapi"></script>
    <script type="text/javascript">
      google.load("visualization", "1", {packages:["corechart"]});
      google.setOnLoadCallback(drawChart);
      function drawChart(){
        var data = google.visualization.arrayToDataTable(["""
PLOT_TAIL = """\
     ]);
     var options = {
       title : "AirData",
       vAxis : {
         viewWindow:
             {min:0}
         }
     };
     var chart = new google.visualization.LineChart(document.getElementById('chart_div'));
     chart.draw(data,options);
    }
    </script>
  </head>
  <body>
    <div id="chart_div" style="width: 1200px; height: 800px;"></div>
"""
HTML_TAIL = """\
  </body>
</html>"""

CITIES = ("Beijing" , "Chengdu", "Guangzhou", "Shanghai", "Shenyang")

class DataPlot(object):
    
    def __init__(self):
        self.latest = {}
        self.data = {}
    
    def mkplot(self, n, cities = CITIES):
        for city in cities:
            if city not in self.data or len(self.data[city]) < n:
                self.fetchdata(city, n)
        datastring = '["hours ago", '
        for city in cities:
            datastring += '"{}", '.format(city)
        datastring += '],'
        # ["hours ago", "Beijing", ... , "Shenyang"],
        for hour in range(n):
            datastring += "[{},".format(hour)
            datastring += ','.join(
                [str(self.data[city][hour]) for city in CITIES])
            datastring += "],"
        return datastring
    
    def fetchdata(self, cityname, n):
        data_query = AirData.query(
            ancestor = databook_key(cityname)).order(-AirData.datetime)
        self.latest[cityname] = data_query.fetch(1)[0]
        if n == -1:
            self.data[cityname] = [d.value for d in data_query][::-1]
        else:
            data = data_query.fetch(n)
            self.data[cityname] = [d.value for d in data][::-1]
    
    def calcmean(self, cityname, hours=24):
        # fetch data if this instance doesn't have enough data.
        if cityname not in self.data or len(self.data[cityname]) < hours:
            self.fetchdata(cityname, hours)
        # applicable_data : meaningful data for the last [hours] hours.
        applicable_data = [
            datum for datum in self.data[cityname][-hours:] if datum >= 0
        ]
        if applicable_data: # if there's been any meaningful data
            return float(sum(applicable_data))/len(applicable_data)
        else:
            return None


def pm25_to_category(conc):
    if conc < 0:
        return 0
    elif conc <= 12:
        return 1
    elif conc <= 35.4:
        return 2
    elif conc <= 55.4:
        return 3
    elif conc <= 150.4:
        return 4
    elif conc <= 250.4:
        return 5
    elif conc <= 500.4:
        return 6
    else:
        return 7


class MainHandler(webapp2.RequestHandler):
    def get(self):
        plotter = DataPlot()
        datastring = plotter.mkplot(120)
        self.response.write(PLOT_HEAD + datastring + PLOT_TAIL)
        self.createtable(plotter)
        self.response.write(HTML_TAIL)
    
    def createtable(self, plotter):
        self.response.write(self.tableheader)
        for city in sorted(plotter.latest.keys()):
            category = pm25_to_category(plotter.latest[city].value)
            means = plotter.calcmean(city) or -999
            means_category = pm25_to_category(means)
            self.response.write(self.tablerow.format(
                city, plotter.latest[city].value, category,
                means, means_category,
                plotter.latest[city].datetime))
        self.response.write(self.tablefooter)
    
    tableheader = u"""\
<center>The latest data:
<table id="conctable">
	<tr><th> City </th> <th> PM 2.5 (μg/m^3)</th> <th>Category</th> <th>Mean for last 24 hours</th> <th>Category</th> <th>Last Updated</th></tr>\n
"""
    
    tablerow = """\
    <tr><td>{}</td> <td class="conc">{}</td> <td class="aqi_{}"></td><td class="conc">{:.3f}</td><td class="aqi_{}"></td><td>{}</td></tr>\n
"""
    tablefooter = "</table>\n</center>"


application = webapp2.WSGIApplication([('/jsgraph', MainHandler)], debug=True)
