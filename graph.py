#!/usr/bin/env python

import StringIO, cgi, webapp2
import matplotlib, matplotlib.pyplot as plt
from google.appengine.ext import ndb
from fetcher import AirData, databook_key 


MAIN_BODY = """\
<html>
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
        plt.title("China Air Data: PM")
        for city in CITIES:
            data = self.getvalue(city, n)
            plt.plot(list(data))
        try:
            plt.ylim(ymin=0)
            plt.legend(CITIES, loc='upper right')
            rv = StringIO.StringIO()
            plt.savefig(rv, format='png')
            return """<img src="data:image/png;base64,{}"/>\n""".format(
                rv.getvalue().encode("base64").strip())
        finally:
            plt.clf()

    def getvalue(self, cityname, n):
        data_query = AirData.query(
            ancestor = databook_key(cityname)).order(-AirData.datetime)
        self.latest[cityname] = data_query.fetch(1)[0].datetime
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
        self.response.write("Update information: {}\n".format(plotter.latest))
        self.response.write(MAIN_FOOTER)
    
    def post(self):
        n = int(self.request.get('xrange'))
        selection=list(map(lambda x: 'selected="selected"' if x == n else "", CHOISES))
        self.response.write(MAIN_BODY.format(*selection))
        plotter = DataPlot()
        self.response.write(plotter.mkplot(n))
        self.response.write("<br />Update information: {}\n".format(plotter.latest))
        self.response.write(MAIN_FOOTER)
    

application = webapp2.WSGIApplication([('/', MainHandler)], debug=True)
