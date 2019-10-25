# Wikipedia Featured Articles multimodal dataset
## Overview
This is a multimodal truncated dataset containing 500 [featured articles](https://en.wikipedia.org/wiki/Wikipedia:Featured_articles)
with more than 8,000 images. Its mirror is also uploaded to [Kaggle](https://www.kaggle.com/jacksoncrow/wiki-articles-multimodal).
A full version of the dataset, containing 5,638 pages and nearly 95,000 images, can be found on [Google Drive](https://drive.google.com/open?id=18i0D-N1J18UC1ebT9qbHZegKJQiKba5z). It contains the text of an article along with all
the images from that article. From Wikipedia, we selected featured articles, which is just a small subset of all available
ones, because they are manually reviewed and protected from edits. Thus it's the best theoretical quality human editors on Wikipedia
can offer.

## Dataset structure
The high-level structure of the dataset is as follows:

    .
    +-- page1  
    |   +-- text.json  
    |   +-- img  
    |       +-- image1  
    |       +-- image2  
    |       :  
    |       +-- imageN  
    +-- page2  
    |   +-- text.json  
    |   +-- img  
    |       +-- image1  
    |       +-- image2  
    |       :  
    |       +-- imageN  
    :  
    +-- page1  
    |   +-- text.json  
    |   +-- img  
    |       +-- image1  
    |       +-- image2  
    |       :  
    |       +-- imageN  

where:

* pageN - is the title of N-th Wikipedia page and contains all information about the page
* text.json - text of the page saved as JSON. Please refer to details of JSON schema below.
* img - folder for all images of the page
* imageN - is the N-th image of an article, saved in `jpg` format where width of each image is set to 600px. Name of the image is md5 hashcode of original image title. 

### Note on Images

* Some images aren't embedded on Wikipedia page from Commons, thus we can only download them in original type&size, thus they should be
properly processed later. Each such image can be identified by suffix `.ORIGINAL` in a filename
* Some images weren't downloaded because of active [pywikibot bug](https://phabricator.wikimedia.org/T236405). You can identify such pages with output in
 `download_log(incomplete_pages).txt` file.
 
### JSON Schema
Below you see an example of how data is stored:

    {
      "title": "Naval Battle of Guadalcanal",
      "id": 405411,
      "url": "https://en.wikipedia.org/wiki/Naval_Battle_of_Guadalcanal",
      "text": "The Naval Battle of Guadalcanal, sometimes referred to as... ",
    }

where:

* title - page title
* id - unique page id
* url - url of a page on Wikipedia
* text - text content of the article escaped from Wikipedia formatting

## Collection method
Data was collected by fetching featured articles text&image content with [pywikibot](https://pypi.org/project/pywikibot/) library.

* [collection script](https://github.com/OlehOnyshchak/WikiImageRecommendation/blob/master/article_reader/reader.py)
* [subsampling script](https://github.com/OlehOnyshchak/WikiImageRecommendation/blob/master/article_reader/dataset_subsampling.ipynb)
* [current list of Featured Articles](https://github.com/OlehOnyshchak/WikiImageRecommendation/blob/master/article_reader/featured_Articles.tsv)
