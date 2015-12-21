#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import re
import csv
import uuid
import os.path
import logging

from urllib.parse import urlparse

_filename_csv = "CriticalAppraisal.csv"
_filename_html = "CriticalAppraisal.html"

_body = """<doctype HTML>
<html>
<head>
	<title>{{ title }}</title>
	<style>
	html, body { margin: 0; padding: 0; font: 14/17pt -apple-system, Roboto, "Helvetica Neue", Helvetica, Arial, sans-serif; }
	h1 { margin: 2em 0 1em; }
	h2 { margin: 1.5em 0 0.75em; }
	h3 { margin: 1em 0 0.4em; }
	p { margin: 0 0 0.5em; }
	a { text-decoration: none; color: #28E; }
	a:visited { color: #95C; }
	h3 a:visited { color: #28E; }
	table { border-collapse: collapse; }
	tbody th { font-weight: normal; text-align: left; }
	tbody th, tbody td { padding: 0.2em 0.5em; vertical-align: top; }
	tbody th:first-child, tbody td:first-child { padding-left: 0; }
	tbody th:last-child, tbody td:last-child { padding-right: 0; }
	#container { display: flex; max-width: 800px; margin: 0 auto; }
	#index { flex: 1 0 auto; max-width: 15em; padding: 9em 15px 0 0; border-right: 1px solid #DDD; }
	#content { flex: 4 1 auto; padding: 2em 15px; }
	#index ul { list-style: none; }
	#index ul li { margin-top: 0.6em; }
	#index ul li a:visited { color: #28E; }
	.topic table { display: none; }
	.topic.show table { display: initial; }
	@media screen and (max-width: 720px) {
		#container { flex-wrap: wrap; }
		#index { display: none; }
	}
	</style>
</head>
<body>
	<div id="container">
		<div id="index"><ul></ul></div>
		<div id="content">
		<h1>{{ title }}</h1>
		{{ chapters }}
		</div>
	</div>
	<script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.4/jquery.min.js"></script>
	<script>
	$(window).on('hashchange', function(evt) {
		updateFromHash();
	});
	$(document).ready(function() {
		updateFromHash();
		buildIndex();
		window.setTimeout(defuseHash, 2000);
	});
	function updateFromHash() {
		if (window.location.hash && window.location.hash.length > 1) {
			$(window.location.hash).addClass('show');	// ignore: $('article[data-id="' + window.location.hash.substr(1) + '"]')
		}
	}
	function defuseHash() {		/// Remove all ids on topics to prevent scrolling, add JS click action to toggle
		$('.topic').attr('id', null)
		.find('h3 > a').each(function(i, elem) { $(elem).click(function(evt) {
			$(this).parent().parent().toggleClass('show');
		}) });
	}
	function buildIndex() {		/// Build an index of all chapter titles
		var idx = $('#index > ul').empty();
		$('.chapter').each(function(i, chap) {
			var id = $(chap).attr('id');
			var h2 = $(chap).find('h2').first();
			idx.append('<li><a href="#' + id + '">' + h2.text() + '</a></li>');
		});
	}
	</script>
</body>
</html>"""

_chapter = """<article id="{{ id }}" class="chapter">
<h2>{{ name }}</h2>
<section>
{{ topics }}
</section>
</article>
"""

_topic = """<article id="{{ id }}" class="topic" data-id="{{ id }}">
<h3><a href="#{{ id }}">{{ name }}</a></h3>
<table><tbody>
{{ entries }}
</tbody></table>
</article>
"""

_entry = """<tr>
<th>{{ name }}</th><td>{{ links }}</td>
</tr>
"""


class ReferenceParser(object):
	name = "__abstract"
	joiner = None
	registered = []
	
	def parse(self, data):
		""" Return a list of `Link` instances or None.
		"""
		return None
	
	@classmethod
	def register(cls):
		ReferenceParser.registered.append(cls)
	
	@classmethod
	def for_reference(cls, name):
		for prsr in ReferenceParser.registered:
			if prsr.name.lower() == name.lower():
				return prsr()
		return None

class TextOrLinkParser(ReferenceParser):
	""" Accepts complete links (will be shown as domain-only) or simple text
	(will be shown as text-only). """
	name = "__domain"
	def parse(self, data):
		if data:
			links = []
			for link in re.split(r',\s+', data):
				if 'http' == link[:4]:
					urlparts = urlparse(link)
					links.append(Link(urlparts.netloc, link))
				else:
					links.append(Link(link, None))
			return links
		return super().parse(data)

class TherapeuticChoicesParser(ReferenceParser):
	name = "Therapeutic Choices 7th edition"
	def parse(self, data):
		if data:
			return [Link("Chapter {}".format(link), None) for link in re.split(r',\s*', data)]
		return super().parse(data)

TherapeuticChoicesParser.register()

class MedManagementParser(ReferenceParser):
	name = "MED MANAGEMENT MODULE"
	def parse(self, data):
		if data:
			return [Link(data, None)]
		return super().parse(data)

MedManagementParser.register()

class MedCasesParser(ReferenceParser):
	name = "MED MANAGEMENT CASES"
	def parse(self, data):
		if data:
			return [Link(data, None)]
		return super().parse(data)
		
MedCasesParser.register()

class CochraneParser(ReferenceParser):
	name = "Cochrane Reviews"
	def parse(self, data):
		""" Accepts Cochrane links "http://onlinelibrary.wiley.com/doi/10.1002/14651858.CD009069.pub2/abstract",
		separated by space, or Cochrane ids, "CD009069", separated by comma. """
		if data:
			links = []
			for link in re.split(r',\s+', data):
				if 'http' == link[:4]:
					name = os.path.basename(os.path.dirname(link))
					name = name.replace('14651858.', '').replace('.pub2', '').replace('.pub3', '')
					links.append(Link(name, link))
				else:
					links.append(Link(link, "http://onlinelibrary.wiley.com/doi/10.1002/14651858.{}.pub2/abstract".format(link)))
			return links
		return super().parse(data)

CochraneParser.register()

class KeyStudiesParser(TextOrLinkParser):
	name = "Key Studies"
KeyStudiesParser.register()

class RiskToolsParser(TextOrLinkParser):
	name = "Risk Tools"
RiskToolsParser.register()

class TheNNTParser(ReferenceParser):
	name = "thennt.com"
	joiner = '<br>'
	def parse(self, data):
		""" Accepts links "http://www.thennt.com/nnt/nicotine-replacement-therapy-for-smoking-cessation/"
		separated by space. Will show last path component.
		"""
		if data:
			return [Link(os.path.basename(os.path.dirname(link)), link) for link in re.split(r'\s+', data)]
		return super().parse(data)

TheNNTParser.register()

class MyStudiesParser(ReferenceParser):
	name = "mystudies.org"
	def parse(self, data):
		if data:
			return [Link("MyStudies", 'http://www.mystudies.org/#{}'.format(data))]
		return super().parse(data)

MyStudiesParser.register()

class BSPodcastParser(ReferenceParser):
	name = "Best Science Medicine Podcasts"
	def parse(self, data):
		if data:
			return [Link("#{}".format(link), 'http://www.therapeuticseducation.org/podcast/') for link in re.split(r',\s*', data)]
		return super().parse(data)

BSPodcastParser.register()

class ToolsForPracticeParser(ReferenceParser):
	name = "Tools for Practice"
	def parse(self, data):
		if data:
			return [Link("#{}".format(link), 'https://www.acfp.ca/tools-for-practice/') for link in re.split(r',\s*', data)]
		return super().parse(data)

ToolsForPracticeParser.register()

class TILettersParser(ReferenceParser):
	name = "TI Letters"
	def parse(self, data):
		if data:
			links = []
			for letter in re.split(r',\s*', data):
				try:
					num = int(letter)
					link = 'http://www.ti.ubc.ca/letter{}'.format(num) if int(num) >= 75 else 'http://www.ti.ubc.ca/newsletter/'
				except Exception as e:
					try:
						link, ltr = re.split(r'\s+', letter)
						if '(' == ltr[0] and ')' == ltr[-1]:
							ltr = ltr[1:-1]
						letter = ltr
					except Exception as ee:
						raise Exception("The format for \"TI Letters\" is incorrect, needs to be the letter number only (letters 75 and newer), separated by comma and space, or the full link + space + the letter number (number may be in brackets)")
				links.append(Link("#{}".format(letter), link))
			return links
		return super().parse(data)

TILettersParser.register()


class Chapter(object):
	def __init__(self, name):
		self.id = as_id(name)
		self.name = name
		self.topics = []
	
	def add_topic(self, topic):
		assert isinstance(topic, Topic)
		self.topics.append(topic)
	
	def html(self):
		topics = [t.html() for t in self.topics]
		return _chapter.replace('{{ id }}', self.id) \
			.replace('{{ name }}', self.name) \
			.replace('{{ topics }}', ''.join(topics))

class Topic(object):
	def __init__(self, chapter, name):
		self.id = as_id(name, chapter.name)
		self.chapter = chapter
		self.name = name
		self.entries = []
	
	def parse_entry(self, parser, data):
		entry = Entry(parser.name, joiner=parser.joiner)
		entry.links = parser.parse(data)
		if entry.links is not None:
			self.entries.append(entry)
	
	def html(self):
		entries = [e.html() for e in self.entries]
		return _topic.replace('{{ id }}', self.id) \
			.replace('{{ name }}', self.name) \
			.replace('{{ entries }}', ''.join(entries))

class Entry(object):
	def __init__(self, name, joiner=', '):
		self.name = name
		self.links = None
		self.joiner = joiner
	
	def html(self):
		links = [l.html() for l in self.links] if self.links is not None else ''
		joiner = self.joiner if self.joiner is not None else ', '
		return _entry.replace('{{ name }}', self.name) \
			.replace('{{ links }}', joiner.join(links))

class Link(object):
	def __init__(self, text, link):
		self.text = text
		self.link = link
	
	def html(self):
		if self.link is None:
			return self.text
		return """<a href="{}" target="_blank">{}</a>""".format(self.link, self.text)

def as_id(text, prefix=None):
	txt = text or uuid.uuid4()
	if prefix is not None:
		txt = prefix + '_' + txt
	return re.sub(r'[^\w\d_]+', '', txt).lower()

def parse_row(row, headers, chapter):
	""" Parse one row. If `chapter` is None, regard the given row as chapter.
	:returns: A Chapter instance, if a new one was created, None otherwise
	"""
	if chapter is None:
		if '' == row[0]:
			return None
		return Chapter(row[0])
	
	# create topic
	topic = Topic(chapter, row[0])
	chapter.add_topic(topic)
	
	# loop cells
	idx = 1
	for data in row[1:]:
		parser = ReferenceParser.for_reference(headers[idx])
		if parser is not None:
			try:
				topic.parse_entry(parser, data=data)
			except Exception as e:
				logging.error("Error on row \"{}\":  {}".format(row[0], e))
				raise Exception("Aborted")
		elif headers[idx]:
			logging.warn("No parser for reference named «{}»".format(headers[idx]))
		idx += 1


def read_file(filename):
	with io.open(filename, 'r', encoding='utf-8') as h:
		logging.info("Reading «{}»".format(filename))
		headers = None
		reader = csv.reader(h)
		chapters = []
		chapter = None
		for row in reader:
			if headers is None:
				headers = row
				continue
			if '' == row[0]:
				chapter = None
			else:
				new_chapter = parse_row(row, headers, chapter)
				if new_chapter is not None:
					chapter = new_chapter
					chapters.append(chapter)
		return chapters

def write_page(target, title, chapters):
	chapters = [c.html() for c in chapters]
	html = _body.replace('{{ title }}', title).replace('{{ chapters }}', ''.join(chapters))
	with io.open(target, 'w', encoding='utf-8') as h:
		h.write(html)


if '__main__' == __name__:
	logging.basicConfig(level=logging.INFO)
	try:
		chapters = read_file(_filename_csv)
		write_page(_filename_html, "Learn all the things", chapters)
		logging.info("Written to «{}»".format(_filename_html))
	except Exception as e:
		logging.critical(e)
