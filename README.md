# Amazon web scraper (Selenium)

A simple web scraper that fetches queries products from [www.amazon.fr](https://www.amazon.fr) and then stores them to csv files through a pandas dataframe.

<u>Setup environment:</u>
```
$ conda env create --name envname --file=environment.yml
```

<u>Usage:</u>
```
$ python amazon_scraper.py <search_terms> <max_pages>
```

<u>Output:</u> </br>CSV files sorted in corresponding directories under ```./amazon/ ``` folder.
