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
    
    count = 0
    for p in pages:
        count += 1
        page_json = json.dumps({
            "title": p.title(),
            "url": p.full_url(),
            "text": _clean(p.text),
        })
        
        _dump(requests_path / (str(p.pageid) + '.json'), page_json)
        # TODO: fix the problem with pageid == 0
        if p.pageid == 0: print("ERROR: Cannot fetch the page " + p.title())
        if debug_info and count % 50 == 0: print('Dumped {} pages'.format(count))
        if count > limit: break
            
    return requests_path
