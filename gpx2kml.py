#!/usr/bin/python
#
# Copyright 2011 - Henry Corrigan-Gibbs
# www.henrycg.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys

from xml.parsers import expat

'''
The converter utility reads from stdin and writes
to stdout. On a *nix-like system, you would invoke
the script like this:

$ python gpx2kml.py < infile.gpx > outfile.kml

The converter only supports the bare minimum of
GPX elements necessary for the signal tracking tool,
so don't expect too much from it. Enjoy!

'''

class GpxParser(object):
	''' 
	These states keep track of where we are in the
	GPX file.
	'''
	STATE_IGNORE 		= 0
	STATE_TRACK			= 1
	STATE_POINT			= 2

	STATE_TIME			= 3
	STATE_ELE			= 4

	STATE_EXTENSIONS 	= 5
	STATE_EXT_SPEED		= 6
	STATE_EXT_ACC		= 7
	STATE_EXT_COURSE	= 8
	STATE_EXT_SIG		= 9

	i=0
	'''
	STATE_DATA defines the state transitions.

	The entries of STATE_DATA have the format:
	'tag_name': (open_tag_state, close_tag_state),

	When the parser hits <tag_name> it will transition
	to state open_tag_state. When the parser reads
	</tag_name> it will transition to close_tag_state.
	'''
	STATE_DATA = {
		'trk': (STATE_TRACK, STATE_IGNORE),
		'trkpt': (STATE_POINT, STATE_TRACK),

		'time': (STATE_TIME, STATE_POINT),
		'ele': (STATE_ELE, STATE_POINT),

		'extensions': (STATE_EXTENSIONS, STATE_POINT),
		'gpx10:speed': (STATE_EXT_SPEED, STATE_EXTENSIONS),
		'ogt10:accuracy': (STATE_EXT_ACC, STATE_EXTENSIONS),
		'gpx10:course': (STATE_EXT_COURSE, STATE_EXTENSIONS),
		'gpx10:signal_strength': (STATE_EXT_SIG, STATE_EXTENSIONS),
	}

	def __init__(self, outfile):
		self.parser = expat.ParserCreate()
		self.parser.StartElementHandler 	= self._start_element
		self.parser.EndElementHandler 		= self._end_element
		self.parser.CharacterDataHandler 	= self._char_data

		self.outfile = outfile
		self.state = self.STATE_IGNORE

		self.cur_point = None

	def _write_header(self):
		self.outfile.write(\
			'<?xml version="1.0" encoding="UTF-8"?>\n'\
			'<kml xmlns="http://earth.google.com/kml/2.1">\n'\
			'\t<Document>\n')

		stylestr = """
		<Style id="icon_%(sig)d">
			<IconStyle>
				<Icon>
					<href>icon_%(sig)d.png</href>
				</Icon>
			</IconStyle>
		</Style>\n"""
		for i in xrange(0,32):
			self.outfile.write(stylestr % {'sig': i})

	def _write_footer(self):
		self.outfile.write('\t</Document>\n'\
							'</kml>\n')
	def _write_point(self):
		self.i+=1
		if self.i % 10 != 0: return
		point_data = self.cur_point

		s=\
"""\t\t<Placemark>
\t\t\t<Point>
\t\t\t\t<coordinates>
\t\t\t\t\t%(lon)s,%(lat)s
\t\t\t\t</coordinates>
\t\t\t</Point>
\t\t\t<styleUrl>#icon_%(sig)d</styleUrl>
\t\t\t<description>
\t\t\t<![CDATA[
"""
		if 'time' in point_data:
			s += "\t\t\t\t<strong>Time</strong>: %(time)s<br/>\n"
		if 'sig' in point_data:
			s += "\t\t\t\t<strong>Signal Strength</strong>: %(sig)s of 31<br/>\n"
		if 'speed' in point_data:
			s += "\t\t\t\t<strong>Speed</strong>: %(speed)0.3f<br/>\n"
		if 'accuracy' in point_data:
			s += "\t\t\t\t<strong>Accuracy</strong>: %(accuracy)0.3f<br/>\n"
		if 'course' in point_data:
			s += "\t\t\t\t<strong>Course</strong>: %(course)0.1f degrees<br/>\n"
		if 'ele' in point_data:
			s += "\t\t\t\t<strong>Elevation</strong>: %(ele)0.1f meters<br/>\n"

		s += "\t\t\t]]>\n"
		s += "\t\t\t</description>\n"
		s += "\t\t</Placemark>\n"

		self.outfile.write(s % point_data)

	def _start_element(self, name, attrs):
		if name in self.STATE_DATA:
			self.state = self.STATE_DATA[name][0]

		if name == 'trkpt':
			self.cur_point = attrs
		elif name == 'gpx':
			self._write_header()

	def _end_element(self, name):
		if name in self.STATE_DATA:
			self.state = self.STATE_DATA[name][1]

		if name == 'trkpt':
			self._write_point()
			self.cur_point = None
		if name == 'gpx':
			self._write_footer()
		
	def _char_data(self, data):
		''' Make sure we're inside a point '''
		if not self.cur_point:
			return 

		if self.state == self.STATE_TIME:
			self.cur_point['time'] = data
		elif self.state == self.STATE_ELE:
			self.cur_point['ele'] = float(data)
		elif self.state == self.STATE_EXT_SPEED:
			self.cur_point['speed'] = float(data)
		elif self.state == self.STATE_EXT_ACC:
			self.cur_point['acc'] = float(data)
		elif self.state == self.STATE_EXT_COURSE:
			self.cur_point['course'] = float(data)
		elif self.state == self.STATE_EXT_SIG:
			self.cur_point['sig'] = int(data)

	def parse(self, text):
		return self.parser.Parse(text)
	
	def parse_file(self, f):
		return self.parser.ParseFile(f)

if __name__ == '__main__':
	g = GpxParser(sys.stdout)
	g.parse_file(sys.stdin)


