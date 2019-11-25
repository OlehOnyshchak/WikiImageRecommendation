from pathlib import Path
import pywikibot
from pywikibot import pagegenerators
import json
import mwparserfromhell as mwp
import hashlib
import urllib
import re
from urllib.request import urlretrieve
from html.parser import HTMLParser
from html.entities import name2codepoint

skipped_svg = set()

class _MyHTMLParser(HTMLParser):
    _description = ""
    _tag_counter = 0
    
    def handle_starttag(self, tag, attrs):
        if self._tag_counter > 0:
            self._tag_counter += 1
        
        for attr in attrs:
            if attr == ('class', 'description'):
                self._tag_counter = 1
                

    def handle_endtag(self, tag):
        if self._tag_counter > 0:
            self._tag_counter -= 1

    def handle_data(self, data):
        if self._tag_counter > 0:
            self._description += data
        
    def get_description(self):
        return self._description
    

def _clean(wiki_text):
    wikicode = mwp.parse(wiki_text)
    return wikicode.strip_code()

def _dump(path, data):
    with open(path, 'w', encoding='utf8') as outfile:
        json.dump(data, outfile, indent=2, ensure_ascii=False)
        
def query_size(filename):
    site = pywikibot.Site()
    pages = list(pagegenerators.TextfilePageGenerator(filename=filename, site=site))
    
    return len(pages)

def get_path(out_dir, create_if_not_exists):
    requests_path = Path(out_dir)
    if not requests_path.exists() and create_if_not_exists:
        requests_path.mkdir(parents=True)
      
    return requests_path

def get_url(img_name, size=600):
    # onyshchak: img.oldest_file_info.url might have the same information
    url_prefix = "https://upload.wikimedia.org/wikipedia/commons/thumb/"
    md5 = hashlib.md5(img_name.encode('utf-8')).hexdigest()
    sep = "/"
    
    img_name = urllib.parse.quote(img_name)
    url = url_prefix + sep.join((md5[0], md5[:2], img_name)) + sep + str(size) + "px-" + img_name
    if url[-4:] != ".jpg" and url[-4:] != "jpeg":
        url += ".jpg"
        
    return url

def get_description(img):
    html = img.getImagePageHtml()
    
    parser = _MyHTMLParser()
    parser.feed(img.getImagePageHtml())
    return parser.get_description().replace("\n", "")

def single_img_download(img, img_dir):
    img_name = img.title(as_filename=True, with_ns=False).replace("\"", "")
    img_name_valid = hashlib.md5(img_name.encode('utf-8')).hexdigest()  
    img_path = img_dir / (img_name_valid + ".jpg")
    
    if img_name[-3:].lower() == "svg":
        skipped_svg.add(get_url(img_name))
        if img_path.exists():
            img_path.unlink()
                
        return (False, "")
    
    if img_path.exists():
        return (False, img_path.name)
    
    img_path_orig = Path(str(img_path) + "_" + img_name + ".ORIGINAL")
    if len(str(img_path_orig)) >= 260:
        # pathlib doesn't support Win long path =(
        img_path_orig = Path(str(img_path) + "_" + Path(img_name).suffix + ".ORIGINAL")
    if img_path_orig.exists():
        return (False, img_path_orig.name)
    
    try:
        # TODO: remove & char from filenames before uploading to Kaggle
        urlretrieve(get_url(img_name), img_path)
        return (True, img_path.name) 
    except Exception as e:
        print(str(e))
        img.download(filename=img_path_orig, chunk_size=8*1024)
        return (True, img_path_orig.name)


def img_download(img_links, page_dir, tc, uc):
    img_dir = get_path(page_dir/"img", create_if_not_exists=True)
    meta_path = img_dir / 'meta.json'
    download_meta = not meta_path.exists()
    meta = []
    for img in img_links:
        downloaded, filename = single_img_download(img, img_dir)
        if downloaded: 
            tc += 1
            
        if download_meta and filename != "":
            meta.append({
                "filename": filename,
                "title": img.title(with_ns=False),
                "description": get_description(img),
                "url": img.full_url(),
            })
          
    if download_meta:
        meta_json = json.dumps({"img_meta": meta})
        _dump(meta_path, meta_json)
    
    return (tc, uc)

def file_log(coll, filename):
    with open(filename, 'w') as f:
        for item in coll:
            f.write("%s\n" % item)

def query(filename, out_dir='../data/', debug_info=True, offset=0, limit=None):   
    site = pywikibot.Site()    
    pages = list(pagegenerators.TextfilePageGenerator(filename=filename, site=site))
    if not limit:
        limit = len(pages) + 1
    
    print('Downloading... offset={}, limit={}'.format(offset, limit))
    prev_percent = -1
    tc = 0
    uc = 0
    for i in range(offset, min(offset + limit, len(pages))):
        p = pages[i]
        if p.pageid == 0:
            print("ERROR: Cannot fetch the page " + p.title())
            continue
            
        if debug_info:
            percent = int(i / len(pages) * 100)
            if prev_percent != percent:
                prev_percent = percent
                print('{}% completed'.format(percent))
            
        
        page_dir = get_path(out_dir + p.title(as_filename=True).rstrip('.'), create_if_not_exists=False)  # onyshchak: set to True
        if not page_dir.exists():
            continue  # onyshchak: temporary switch to enrich only existing data
        
        print(page_dir)
        text_path = page_dir / 'text.json'
        if not text_path.exists():
            page_json = json.dumps({
                "title": p.title(),
                "id": p.pageid,
                "url": p.full_url(),
                "text": _clean(p.text),
            })
            
            _dump(text_path, page_json)
            
        # downloading page images
        tc, uc = img_download(p.imagelinks(), page_dir, tc, uc)           
            
    print('Downloaded {} images, where {} of them unavailable from commons'.format(tc, uc))
    file_log(skipped_svg, 'logs/skipped_svg_{}.txt'.format(offset))