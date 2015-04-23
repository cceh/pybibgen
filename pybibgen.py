#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# (C) 2015 Marcel Schaeben, Cologne Center for eHumanities (CCeH)
#
#

from __future__ import (absolute_import, division, print_function,
	                    unicode_literals)

from pyzotero import zotero
import sys
import os, inspect

zot_script_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

from citeproc import CitationStylesStyle, CitationStylesBibliography
from citeproc import formatter
from citeproc import Citation, CitationItem
from citeproc.source.bibtex import BibTeX

import traceback
import codecs

UTF8Writer = codecs.getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)
sys.stderr = UTF8Writer(sys.stderr)


import sys
reload(sys)
sys.setdefaultencoding('UTF8')

import StringIO
import urllib2
import re
import argparse

zot_jinja2_availible = True

try:
	import jinja2
except:
	zot_jinja2_availible = False



# defaults

global_config = {
	"library_id": None,
	"library_type": None,
	"sort": None,
	"top_collection": None,
	"citation_style": 'theologie-und-philosophie',
	"styles_dir": zot_script_path + '/citation_styles/',
	"api_key": None
}

try:
	from pybibgen_settings import pybibgen_config
	global_config.update(pybibgen_config)
except:
	pass

zot_styles_repo_url = 'https://www.zotero.org/styles'
zot_default_style = "harvard1"

zot = None

def warning(*objs):
    print("DEBUG: ", *objs, file=sys.stderr)


# take a string of bibtex entries and build a list of dicts each containing the bibtex key,
# the bibtex string and rendered html for one item
def parse_zotero_bibtex(items, citation_style_path):
	
	# separate the bibtex items and extract the key
	p = re.compile(ur'{([^,]+)')
	bibtexItems = []
	for item in items.split('@'):
		if len(item) > 1:
			# make a tuple containing bibtex key and bibtex string
			# splitting removed the @ of each entry so we need to add it back to get valid bibtex
			bibtexItems.append((re.search(p, item).group(1), "@" + item))

	# citeproc_py expects a bibtex file for input so we cannot just pass the bibtex string,
	# so we need to write it into a virtual file using StringIO
	output = StringIO.StringIO()
	output.write(items)
	output.seek(0)

	itemDicts = []
	try:
		# initialize citeproc-py
		bib_source = BibTeX(output)
		bib_style = CitationStylesStyle(citation_style_path, validate=False)
		
		# parse each bibtex entry into a html formatted bibliography entry
		# instead of generating a bibliography of all entries at once, create a
		# bibliography for each of the single items to retaing mapping to the 
		# corresponding bibtex string
		for (key, bibtex) in bibtexItems:
			bibliography = CitationStylesBibliography(bib_style, bib_source, formatter.html)

			citationItem = CitationItem(key)
			citation = Citation([citationItem])
			
			bibliography.register(citation)
			bibliography.cite(citation, warning)
			
			renderedItem = ""

			# the rendered bibliography item returned by citeproc-py is split
			# inton an array of separate tokens, so we need to join them together 
			for token in bibliography.bibliography()[0]:
				renderedItem += token 

			itemDicts.append({
					'key': key,
					'bibtex': bibtex,
					'html': renderedItem
				})

	except:
		warning("ERROR PARSING")
		traceback.print_exc(file=sys.stderr)

	finally:
		output.close()
		return itemDicts

# takes a collection object as returned by pyzotero, the current recursion level,
# a zotero sort string and the path of the citation style to be used.
# returns a dict containing the current header level, the collection name and key,
# its subcollections and bibliography items
def recurse_collections(top_collection, level, sort, citation_style_path):

	subcollections = []
	bibitems = []

	# recurse into each subcollection 
	if top_collection['meta']['numCollections'] is not 0:
		global zot
		for collection in sorted_collections(zot.collections_sub(top_collection['data']['key'])):
			subcollections.append(recurse_collections(collection, level + 1, sort, citation_style_path))
	else:
		# gather all bibliography items of this collection. 
		# zotero returns up to 100 items at once.
		item_count = top_collection['meta']['numItems']
		item_start = 0
		item_limit = 100

		while item_start < item_count:
			warning(top_collection['data']['name'] + ": " + str(item_start) + "/" + str(item_count))
			collection_items = zot.collection_items(top_collection['data']['key'], format='bibtex', start=item_start, limit=item_limit, sort=sort)
			bibitems += parse_zotero_bibtex(collection_items, citation_style_path)
			item_start += item_limit

	return {
		'header_level': level,
		'name': top_collection['data']['name'].lstrip("0123456789 "),
		'key': top_collection['data']['key'],
		'subcollections': subcollections,
		'bibitems': bibitems
	}


# sort collections by name. numbers at the beginning of a collection name will be 
# stripped in the output, enabling custom sorting of collections
def sorted_collections(collections):
 	return sorted(collections, key=lambda k: k['data']['name'])


# get the path to a specified citation style. if the csl style is not found in the 
# styles directory, try to retrieve it from the zotero styles repository
def get_citation_style(name, styles_dir):
	try:
		with open(styles_dir + name + '.csl', 'r') as f:
			return styles_dir + name + '.csl'
	
	except:
		warning("Citation style '" + name + "' not found. Trying to fetch from styles repository...")
		style_url = zot_styles_repo_url + "/" + name

		try:
			remote_file = urllib2.urlopen(style_url)
			with open(styles_dir + name + ".csl", 'wb') as local_file:
				local_file.write(remote_file.read())
				return styles_dir + name + '.csl'

		except:
			warning("Error fetching'" + style_url + "' Falling back to " + zot_default_style)
			traceback.print_exc(file=sys.stderr)
			return styles_dir + zot_default_style + '.csl'


# return a list containing all collections and bibliography items
def get_collections(config=global_config):
	config = merge_config(config)
	citation_style_path = get_citation_style(config['citation_style'], config['styles_dir'])

	collections = []
	global zot
	if zot is None:
		zot = zotero.Zotero(config["library_id"], config["library_type"], config["api_key"])
	
	sub_collections = None
	parent_collections = None
	if config['top_collection'] is not None:
		top_collection = zot.collection(config['top_collection'])
		if top_collection['meta']['numCollections'] is 0: 
			parent_collections = [top_collection]
		else:
			sub_collections = zot.collections_sub(config['top_collection']) 
			parent_collections = (i for i in sub_collections if not i['data']['parentCollection'] is config['top_collection'])
	else: 
		sub_collections = zot.collections()
		parent_collections = (i for i in sub_collections if i['data']['parentCollection'] is False)


	for collection in sorted_collections(parent_collections):
		collections.append(recurse_collections(collection, 2, config['sort'], citation_style_path))

	return collections

# return a complete html formatted bibliography (jinja2 template engine required)
def get_bibliography(config=global_config):
	global zot_script_path

	if not zot_jinja2_availible:
		warning("Package 'jinja2' used to render the html output not found, exiting.")
		return

	templateLoader = jinja2.FileSystemLoader(zot_script_path + "/templates/")
	templateEnv = jinja2.Environment( loader=templateLoader )
	template = templateEnv.get_template("bibliography.html")

	return template.render(collections=get_collections(config))


# returns the current bibliography version number, can be used for caching
def get_last_modified_version(config=global_config):
	config = merge_config(config)

	zot = zotero.Zotero(config['library_id'], config['library_type'], config['api_key'])
 	return zot.last_modified_version();

def merge_config(local_config):
	global global_config

	if local_config is not global_config:
		config = global_config.copy()
		config.update(local_config)
		return config

	else:
		return global_config

# if this script is called directly, return a html formatted bibliography
if __name__ == '__main__':

	parser = argparse.ArgumentParser(description="Generate a static HTML bibliography from a Zotero library.")

	argdesc = {
		'l': "The Zotero library id",
		't': "The Zotero library type: 'group' or 'user'",
		'a': "Your Zotero API Key. Required for user or private group libraries.",
		's': "The name of the field by which entries are sorted.",
		'c': "The key of the top level collection to include in the bibliography. By default, all collections in a library are included. ",
		'S': "The citation style used for bibliography entries. By default, the Harvard Reference format 1 (harvard1) is used. If the specified style is not found in styles_dir, the script will try to download it from the Zotero styles repository.", 
		'd': "The directory where citation styles are found."
	}

	parser.add_argument('-l', '--library-id', help=argdesc['l'], type=int, default=global_config['library_id'])
	parser.add_argument('-t', '--library-type', help=argdesc['t'], choices=['group', 'user'], default=global_config['library_type'])
	parser.add_argument('-a', '--api-key', help=argdesc['a'], default=global_config['api_key'])
	parser.add_argument('-s', '--sort', help=argdesc['s'], default=global_config['sort'], choices=['dateAdded', 'dateModified', 'title', 'creator', 'type', 'date', 'publisher', 'publicationTitle', 'journalAbbreviation', 'language', 'accessDate', 'libraryCatalog', 'callNumber', 'rights', 'addedBy', 'numItems'])
	parser.add_argument('-c', '--top-collection', help=argdesc['c'], default=global_config['top_collection'])
	parser.add_argument('-S', '--citation-style', help=argdesc['S'], default=global_config['citation_style'])
	parser.add_argument('-d', '--styles-dir', help=argdesc['d'], default=global_config['styles_dir'])
	args = parser.parse_args()

	if args.library_id is None:
		print("ERROR: no library ID specified.")
		parser.print_help()
	if args.library_type is None:
		print("ERROR: no library type specified.")
		parser.print_help()

	print(get_bibliography(vars(args)))


