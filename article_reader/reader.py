from pathlib import Path
import pywikibot
from pywikibot import pagegenerators
import json
import mwparserfromhell as mwp
import hashlib
import urllib
from urllib.request import urlretrieve


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

def get_path(out_dir):
    requests_path = Path(out_dir)
    if not requests_path.exists():
        requests_path.mkdir(parents=True)
      
    return requests_path

def get_url(img_name, size=600):
    url_prefix = "https://upload.wikimedia.org/wikipedia/commons/thumb/"
    md5 = hashlib.md5(img_name.encode('utf-8')).hexdigest()
    sep = "/"
    
    img_name = urllib.parse.quote(img_name)
    url = url_prefix + sep.join((md5[0], md5[:2], img_name)) + sep + str(size) + "px-" + img_name
    if url[-4:] != ".jpg" and url[-4:] != "jpeg":
        url += ".jpg"
        
    return url

def query(filename, out_dir='../data/', debug_info=True, limit=None):   
    print('Downloading...')
    site = pywikibot.Site()    
    pages = list(pagegenerators.TextfilePageGenerator(filename=filename, site=site))
    
    prev_percent = -1
    unavailable_count = 0
    total_count = 0
    for i, p in enumerate(pages):
        if i >= limit: break
            
        page_dir = get_path(out_dir + p.title(as_filename=True))
        text_path = page_dir / 'text.json'
        if not text_path.exists():
            page_json = json.dumps({
                "title": p.title(),
                "id": p.pageid,
                "url": p.full_url(),
                "text": _clean(p.text),
            })
            
            _dump(text_path, page_json)
        
        # TODO: fix the problem with pageid == 0
        if p.pageid == 0:
            print("ERROR: Cannot fetch the page " + p.title())
            continue
            
        if debug_info:
            count = min(limit, len(pages)) if limit else len(pages)
            percent = int(i / count * 100)
            if prev_percent != percent:
                prev_percent = percent
                print('{}% completed'.format(percent))
            
        # downloading page images
        img_links = list(p.imagelinks())
        img_dir = get_path(page_dir/"img")
        for img in img_links:
            img_name = img.title(as_filename=True, with_ns=False)
            img_path = img_dir / (img_name + ".jpg")
            if img_path.exists(): continue
            
            total_count += 1
            try:
                urlretrieve(get_url(img_name), img_path)
            except:
                unavailable_count += 1
                img.download(filename=str(img_path) + ".ORIGINAL" , chunk_size=8*1024)
            
            
    print('Downloaded {} images, where {} of them unavailable from commons'.format(total_count, unavailable_count))
