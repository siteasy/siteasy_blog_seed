# Structure

The basic structure of the siteasy looks like this

```
- articles
  |__category0
  |  |__index.md
  |  |__article0.md
  |  |__article1.md
  |  |__article2.md
  |__category1
  |  |__index.md
  |  |__article0.md
  |  |__article1.md
  |  |__article2.md
  |__index.md     
- theme
  |__default
- siteasy.py
```
Notes:  
- The index.md under articles defines the content of index of the site
- The index.md under categories defines the content of index of each category. If you don't put index.md in the category folder, then the list of articles will be the index of category.
- The category folder name can't be "index"

