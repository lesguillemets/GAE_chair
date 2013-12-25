#!/usr/bin/env python
# encoding:utf-8

import StringIO, cgi, webapp2
import matplotlib, matplotlib.pyplot as plt
from google.appengine.ext import ndb
from fetcher import AirData, databook_key 


MAIN_BODY = """\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
   "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<title>Air Log Viewer for WhiteDandelion</title>
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
		<input type="submit" value="Set">
	</select>
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
    
    def mkplot(self, n):
        plt.title("China Air Data: PM2.5")
        for city in CITIES:
            data = self.getvalue(city, n)
            plt.plot(list(data))
        try:
            plt.ylim(ymin=0)
            plt.legend(CITIES, loc='upper right')
            plt.ylabel("PM 2.5 [micro g / m^3]")
            ax = plt.axes()
            ax.yaxis.grid(True)
            rv = StringIO.StringIO()
            plt.savefig(rv, format='png')
            return """<img src="data:image/png;base64,{}"/>\n<br />\n""".format(
                rv.getvalue().encode("base64").strip())
        finally:
            plt.clf()

    def getvalue(self, cityname, n):
        data_query = AirData.query(
            ancestor = databook_key(cityname)).order(-AirData.datetime)
        self.latest[cityname] = data_query.fetch(1)[0]
        if n == -1:
            return reversed([d.value for d in data_query])
        else:
            data = data_query.fetch(n)
            return reversed([d.value for d in data])



class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write(MAIN_BODY.format(
            '"selected"', "", "", "", ""))
        plotter = DataPlot()
        self.response.write(plotter.mkplot(-1))
        self.createtable(plotter)
        #self.response.write("Update information: {}\n".format(plotter.latest))
        self.response.write(MAIN_FOOTER)
    
    def post(self):
        n = int(self.request.get('xrange'))
        selection=list(map(lambda x: 'selected="selected"' if x == n else "", CHOISES))
        self.response.write(MAIN_BODY.format(*selection))
        plotter = DataPlot()
        self.response.write(plotter.mkplot(n))
        self.createtable(plotter)
        #self.response.write("<br />Update information: {}\n".format(plotter.latest))
        self.response.write(MAIN_FOOTER)
    
    def createtable(self, plotter):
        self.response.write(self.tableheader)
        for city in sorted(plotter.latest.keys()):
            category = pm25_to_category_and_color(plotter.latest[city].value)
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

application = webapp2.WSGIApplication([('/', MainHandler)], debug=True)
