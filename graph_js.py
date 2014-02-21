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
    
    def mkplot(self, n, cities = CITIES):
        data = {}
        for city in cities:
            data[city] = self.getvalue(city, n)
        datastring = '["hours ago", '
        for city in cities:
            datastring += '"{}", '.format(city)
        datastring += '],'
        # ["hours ago", "Beijing", ... , "Shenyang"],
        for hour in range(n):
            datastring += "[{},".format(hour)
            datastring += ','.join(
                [str(data[city][hour]) for city in CITIES])
            datastring += "],"
        return datastring
    
    def getvalue(self, cityname, n):
        data_query = AirData.query(
            ancestor = databook_key(cityname)).order(-AirData.datetime)
        self.latest[cityname] = data_query.fetch(1)[0]
        if n == -1:
            return [d.value for d in data_query][::-1]
        else:
            data = data_query.fetch(n)
            return [d.value for d in data][::-1]


def pm25_to_category_and_color(conc):
    if conc < 0:
        return ("None", "#ffffff")
    elif conc <= 12:
        return ("Good", "#00e400")
    elif conc <= 35.4:
        return ("Moderate", "FFFF00")
    elif conc <= 55.4:
        return ('<font color="#ffffff">Unhealthy for Sensitive Groups</font>', "#FF7E00")
    elif conc <= 150.4:
        return ('<font color="#ffffff">Unhealty</font>', "#FF0000")
    elif conc <= 250.4:
        return ('<font color="#ffffff">Very Unhealthy</font>', "#99004c")
    elif conc <= 500.4:
        return ('<font color="#ffffff">Hazardous</font>', "#4c00256")
    else:
        return ('<font color="#ffffff">Beyond Index</font>', "575757")


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
            category = pm25_to_category_and_color(
                plotter.latest[city].value)
            self.response.write(self.tablerow.format(
                city, plotter.latest[city].value,
                category[1], category[0],
                plotter.latest[city].datetime))
        self.response.write(self.tablefooter)
    
    tableheader = u"""\
<center>The latest data:
<table border=1 frame="hsides">
	<tr><th> City </th> <th> PM 2.5 (μg/m^3)</th> <th>Category</th> <th>Last Updated</th></tr>\n
"""
    
    tablerow = """\
	<tr><td>{}</td> <td align="right">{}</td> <td align="center" bgcolor="{}">{} </td> <td>{}</td></tr>\n
"""
    tablefooter = "</table>\n</center>"


application = webapp2.WSGIApplication([('/jsgraph', MainHandler)], debug=True)
