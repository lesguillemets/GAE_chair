#!/usr/bin/env python
# encoding:utf-8

import StringIO, cgi, webapp2
import matplotlib.pyplot as plt
from google.appengine.ext import ndb
from fetcher import AirData, databook_key 


MAIN_BODY = """\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
   "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<title>Air Log Viewer for WhiteDandelion</title>
<link style="text/css" rel="stylesheet" href="./css/airrank.css"/>
</head>
<body>
<h2>WhiteDandelion air data logger</h2>
<p>
<form action='/' method="post">
	View 
	<select name= 'xrange'>
		<option value=-1 {}>from the beginning</option>
		<option value=240 {}>last 240 hours</option>
		<option value=120 {}>last 120 hours </option>
		<option value=48 {}>last 48 hours</option>
		<option value=24 {}>last 24 hours</option>
	</select>
	<table>
		<tr><td align="center">Beijing</td><td align="center">Chengdu</td>
            <td align="center">Guangzhou</td><td align="center">Shanghai</td><td align="center">Shenyang</td></tr>
		<tr>
			<td align="center"><input type="checkbox" name="Beijing" value="True" {}></td>
			<td align="center"><input type="checkbox" name="Chengdu" value="True" {}></td>
			<td align="center"><input type="checkbox" name="Guangzhou" value="True" {}></td>
			<td align="center"><input type="checkbox" name="Shanghai" value="True" {}></td>
			<td align="center"><input type="checkbox" name="Shenyang" value="True" {}></td>
		</tr>
	</table>
    <input type="submit" value="Set">
</form>
</p>

"""

CHOISES = (-1,240,120,48,24)

MAIN_FOOTER = """\
<center>
	<small>created by lesguillemets. Data taken from http://www.stateair.net</small>
</center>
</body></html>
"""
CITIES = ("Beijing" , "Chengdu", "Guangzhou", "Shanghai", "Shenyang")

class DataPlot(object):
    
    def __init__(self):
        self.latest = {}
        self.data = {}
    
    def mkplot(self, n, cities = CITIES):
        plt.title("China Air Data: PM2.5")
        for city in cities:
            if city not in self.data or len(self.data[city]) < n:
                self.fetchdata(city, n)
            plt.plot(self.data[city])
        try:
            plt.ylim(ymin=0)
            plt.legend(cities, loc='upper right')
            plt.ylabel("PM 2.5 [micro g / m^3]")
            ax = plt.axes()
            ax.yaxis.grid(True)
            ax.xaxis.grid(True)
            rv = StringIO.StringIO()
            plt.savefig(rv, format='png')
            return """<center><img src="data:image/png;base64,{}"/>\n<br />\n</center>""".format(
                rv.getvalue().encode("base64").strip())
        finally:
            plt.clf()
    
    def fetchdata(self, cityname, n):
        data_query = AirData.query(
            ancestor = databook_key(cityname)).order(-AirData.datetime)
        self.latest[cityname] = data_query.fetch(1)[0]
        if n == -1:
            self.data[cityname] = [d.value for d in data_query][::-1]
        else:
            data = data_query.fetch(n)
            self.data[cityname] =  [d.value for d in data][::-1]
    
    def calcmean(self, cityname, hours=24):
        # fetch data if this instance doesn't have enough data.
        if cityname not in self.data or len(self.data[cityname]) < hours:
            self.fetchdata(cityname, hours)
        # applicable_data : meaningful data for the last [hours] hours.
        applicable_data = [
            datum for datum in self.data[cityname][:-hours] if datum >= 0
        ]
        if applicable_data: # if there's been any meaningful data
            return float(sum(applicable_data))/len(applicable_data)
        else:
            return None



class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write(MAIN_BODY.format(
            "", "", "selected='selected'", "", "",
            "checked", "checked", "checked", "checked", "checked"))
        plotter = DataPlot()
        self.response.write(plotter.mkplot(120))
        self.createtable(plotter)
        #self.response.write("Update information: {}\n".format(plotter.latest))
        self.response.write(MAIN_FOOTER)
    
    def post(self):
        n = int(self.request.get('xrange'))
        selection=list(map(lambda x: 'selected="selected"' if x == n else "", CHOISES))
        #cities = { i:self.request.get(i) for i in CITIES}
        cities = [city for city in CITIES if self.request.get(city)]
        def ischecked(city):
            return city in cities
        checked = ["checked" if ischecked(city) else '' for city in CITIES]
        self.response.write(MAIN_BODY.format(*(selection + checked)))
        plotter = DataPlot()
        self.response.write(plotter.mkplot(n, cities))
        for city in CITIES:
            if not ischecked(city):
                plotter.getvalue(city, 1) # to know the latest data.
        self.createtable(plotter)
        #self.response.write("<br />Update information: {}\n".format(plotter.latest))
        self.response.write(MAIN_FOOTER)
    
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

application = webapp2.WSGIApplication([('/', MainHandler)], debug=True)
