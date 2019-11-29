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
from os import listdir, stat
from os.path import isfile, join
from dataclasses import dataclass
from typing import Optional


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
        
def _getJSON(path):
    with open(path) as json_file:
        return json.loads(json.load(json_file))
    
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

def get_img_path(img, img_dir):
    img_name = img.title(as_filename=True, with_ns=False).replace("\"", "")
    img_name_valid = hashlib.md5(img_name.encode('utf-8')).hexdigest()  
    img_path = img_dir / (img_name_valid + ".jpg")
    
    img_path_orig = Path(str(img_path) + "_" + img_name + ".ORIGINAL")
    if len(str(img_path_orig)) >= 260:
        # pathlib doesn't support Win long path =(
        img_path_orig = Path(str(img_path) + "_" + Path(img_name).suffix + ".ORIGINAL")
        
    return img_name, img_path, img_path_orig

def valid_img_type(img_name):
    # onyshchak: exclude .svg since most of it is icons. Althouh, should do better filtering
    valid_types = [
        '.tif', '.tiff', '.jpg', '.jpeg', '.jpe', '.jif,', '.jfif', '.jfi',  '.gif', '.png'
    ]
    for t in valid_types:
        if img_name.lower().endswith(t):
            return True
    return False

def single_img_download(img, img_dir):
    img_name, img_path, img_path_orig = get_img_path(img, img_dir)
    if not valid_img_type(img_name):
        skipped_svg.add(get_url(img_name))
        if img_path.exists():
            img_path.unlink()
                
        return (False, "")
    
    if img_path.exists():
        return (False, img_path.name)
    
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
    
def remove_obsolete_imgs(img_dir, img_links):
    uptodate_imgs = [get_img_path(img, img_dir) for img in img_links]
    img_names = (
        [x[1].name for x in uptodate_imgs if valid_img_type(x[0])] +
        [x[2].name for x in uptodate_imgs if valid_img_type(x[0])]
    )
    
    files = [img_dir/f for f in listdir(img_dir) if isfile(join(img_dir, f))]
    for fpath in files:
        fname = fpath.name
        if stat(fpath).st_size == 0:
            print("DELETE", fpath)
            fpath.unlink()
        elif fname in img_names or fname[-5:].lower() == ".json":
            continue
        else:
            print("DELETE", fpath)
            fpath.unlink()
    
    meta_path = img_dir/'meta.json'
    if not meta_path.exists():
        return
    
    meta = _getJSON(meta_path)
    uptodate_meta = [x for x in meta['img_meta'] if x['filename'] in img_names]
    if len(meta['img_meta']) != len(uptodate_meta):
        print("META", img_dir)
        meta_json = json.dumps({"img_meta": uptodate_meta})
        _dump(meta_path, meta_json)
        
def is_meta_outdated(meta_path, img_links):
    if not meta_path.exists():
        return True
    
    meta = _getJSON(meta_path)['img_meta']
    meta_titles = [x['title'] for x in meta]
    current_titles = [x.title(with_ns=False) for x in img_links if valid_img_type(x.title(with_ns=False))]
    
    res = sorted(meta_titles) != sorted(current_titles)
    if res: print("OUTDATED META",  meta_path)
    return res
    

def img_download(img_links, page_dir, tc, uc):
    img_dir = get_path(page_dir/"img", create_if_not_exists=True)
    meta_path = img_dir / 'meta.json'
    remove_obsolete_imgs(img_dir, img_links)
    
    download_meta = is_meta_outdated(meta_path, img_links)
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

# onyshchak: TODO - add 'on_commons' flag to meta + exreact features from all ORIGINAL files
def update_meta_description(filename, out_dir, offset=0, limit=None):
    site = pywikibot.Site()    
    pages = list(pagegenerators.TextfilePageGenerator(filename=filename, site=site))
    limit = limit if limit else len(pages) - offset
    
    for i in range(offset, offset + limit):
        p = pages[i]
        if p.pageid == 0:
            print("ERROR: Cannot fetch the page " + p.title())
            continue
        
        page_dir = get_path(out_dir + p.title(as_filename=True).rstrip('.'), create_if_not_exists=False)
        if not page_dir.exists():
            print('not page_dir.exists()', page_dir)
            continue  # onyshchak: temporary switch to enrich only existing data
            
        print(i, p.title())
        img_dir = get_path(page_dir/"img", create_if_not_exists=False)
        meta_path = img_dir / 'meta.json'
        meta = _getJSON(meta_path)
        
        updated = False
        for img in p.imagelinks():
            if not valid_img_type(img.title(with_ns=False)):
                continue
            
            i = next(i for i,x in enumerate(meta['img_meta']) if x['title'] == img.title(with_ns=False))
            updated_description = get_description(img)
            if updated_description != meta['img_meta'][i]['description']:
                updated = True
                meta['img_meta'][i]['description'] = get_description(img)
                print("DESCRIPTION", img_dir/meta['img_meta'][i]['filename'])
            
        if updated:
            meta_json = json.dumps(meta)
            _dump(meta_path, meta_json)
    

def file_log(coll, filename):
    with open(filename, 'w') as f:
        for item in coll:
            f.write("%s\n" % item)

@dataclass
class QueryParams:
    out_dir: str = '../data/'
    debug_info: bool = True
    offset: int = 0
    limit: Optional[int] = None

def query(filename: str, params: QueryParams) -> None:   
    site = pywikibot.Site()    
    pages = list(pagegenerators.TextfilePageGenerator(filename=filename, site=site))
    limit = params.limit if params.limit else len(pages) - params.offset
    
    print('Downloading... offset={}, limit={}'.format(params.offset, limit))
    tc, uc = 0, 0
    for i in range(params.offset, params.offset + limit):
        p = pages[i]
        if p.pageid == 0:
            print("ERROR: Cannot fetch the page " + p.title())
            continue
            
        # onyshchak: set to True
        page_dir = get_path(params.out_dir + p.title(as_filename=True).rstrip('.'), create_if_not_exists=False)
        if not page_dir.exists():
            continue  # onyshchak: temporary switch to enrich only existing data
        
        if params.debug_info: print(i, page_dir)
        text_path = page_dir / 'text.json'
        if not text_path.exists() or stat(text_path).st_size == 0:
            if params.debug_info: print("Downloading text.json")
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
    file_log(skipped_svg, 'logs/skipped_svg_{}.txt'.format(params.offset))