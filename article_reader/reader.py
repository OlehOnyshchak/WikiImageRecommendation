from pathlib import Path
import pywikibot
from pywikibot import pagegenerators
import json
import mwparserfromhell as mwp

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

def get_requests_path(request, out_dir):
    requests_base = Path(out_dir)
    requests_path = requests_base / request
    
    is_exist = requests_path.exists()
    if not is_exist:
        requests_path.mkdir(parents=True)
      
    return (requests_path, is_exist)

def query(filename, out_dir='../requests', force_rewrite=True, debug_info=True, limit=None):
    requests_path, existed = get_requests_path(filename, out_dir)
    
    if existed:
        if not force_rewrite:
            if debug_info: print('Request has already been downloaded')
            return requests_path
        else:
            if debug_info: print('Cleaning old data')
            for x in requests_path.iterdir():
                x.unlink()
    
    print('Downloading...')
    site = pywikibot.Site()    
    pages = list(pagegenerators.TextfilePageGenerator(filename=filename, site=site))
    
    for i, p in enumerate(pages):
        page_json = json.dumps({
            "title": p.title(),
            "url": p.full_url(),
            "text": _clean(p.text),
        })
        
        _dump(requests_path / (str(p.pageid) + '.json'), page_json)
        
        # TODO: fix the problem with pageid == 0
        if p.pageid == 0:
            print("ERROR: Cannot fetch the page " + p.title())
            continue
            
        if debug_info and (i+1) % 50 == 0: print('Dumped {} pages'.format(i+1))
        if i >= limit: break
            
        # downloading page images
        img_links = list(p.imagelinks())
        path = Path("../data/img/" + str(p.pageid))
        if not path.exists():
            path.mkdir(parents=True)
            
        for img in img_links:
            img_path = path/img.title(as_filename=True, with_ns=False)
            if img_path.exists(): continue
            if debug_info: print('Downloading {} | {}'.format(img_path, p.title()))
            img.download(filename=img_path, chunk_size=8*1024)
            
    return requests_path
