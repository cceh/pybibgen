# pybibgen

This script generates static HTML bibliography page from a Zotero collection or library. The HTML output is generated using the jinja2 templating engine. The included template contains a client-side filtering form.

## Requirements

* citeproc-py
* jinja2 (optional, required for HTML output)

## Usage

### Invoking the script directly from command line

```bash
python pybibgen.py -l LIBARY_ID -t LIBRARY_TYPE
```

The minimum required options are `-l` specifying the library id and `-t` specifying the library type, which can be either "group" or "user". 


Supported options:

```
./pybibgen.py --help                                                                                                                     
usage: pybibgen.py [-h] [-l LIBRARY_ID] [-t {group,user}] [-a API_KEY]
                   [-s {dateAdded,dateModified,title,creator,type,date,publisher,publicationTitle,journalAbbreviation,language,accessDate,libraryCatalog,callNumber,rights,addedBy,numItems}]
                   [-c TOP_COLLECTION] [-S CITATION_STYLE] [-d STYLES_DIR]

Generate a static HTML bibliography from a Zotero library.

optional arguments:
  -h, --help            show this help message and exit
  -l LIBRARY_ID, --library-id LIBRARY_ID
                        The Zotero library id
  -t {group,user}, --library-type {group,user}
                        The Zotero library type: 'group' or 'user'
  -a API_KEY, --api-key API_KEY
                        Your Zotero API Key. Required for user or private
                        group libraries.
  -s {dateAdded,dateModified,title,creator,type,date,publisher,publicationTitle,journalAbbreviation,language,accessDate,libraryCatalog,callNumber,rights,addedBy,numItems}, --sort {dateAdded,dateModified,title,creator,type,date,publisher,publicationTitle,journalAbbreviation,language,accessDate,libraryCatalog,callNumber,rights,addedBy,numItems}
                        The name of the field by which entries are sorted.
  -c TOP_COLLECTION, --top-collection TOP_COLLECTION
                        The key of the top level collection to include in the
                        bibliography. By default, all collections in a library
                        are included.
  -S CITATION_STYLE, --citation-style CITATION_STYLE
                        The citation style used for bibliography entries. By
                        default, the Harvard Reference format 1 (harvard1) is
                        used. If the specified style is not found in
                        styles_dir, the script will try to download it from
                        the Zotero styles repository.
  -d STYLES_DIR, --styles-dir STYLES_DIR
                        The directory where citation styles are found.
```

### Using pybibgen from another python script

(TODO)

## To Do

* allow simple BibTeX files as input, making the script independent from Zotero
* extract and render abstracts
* add rst and plaintext output

## History and Credits 

`pybibgen` is inspired by David Reitter's [zot_bib_web](https://github.com/davidswelt/zot_bib_web). `zot_bib_web` retrieves bibliographic items in a copule of formats at once by making several calls to the Zotero API per bunch of items. This heavy API usage makes the harvesting process quite slow for huge libraries. `pybibgen` only retrieves the items once as BibTeX and relies on the `citeproc-py` CSL parser to generate formatted bibligraphic entries locally, while still providing BibTex output for exporting. This makes harvesting much faster, while the output produced can be a bit less accurate than `zot_bib_web` which uses the Zotero webservice to generate the formatted items.  

The code for the included template's client side filtering form is, with slight modifications, taken directly from `zot_bib_web`.


