# Config.json
There is a config file under the root directory. It is the global setting of the site.
## articles_path
Pointer to the folder where you put the article(md) files.  
demo:
```json
{"articles_path":"articles"}
```

## theme
Which theme you used.  
demo:
```json
{"theme":"default"}
```

## index
The context of index.  
demo:
```json
{"index":""}
```

## logo
The logo (brand) of the header.  
demo:
```json
{"logo":"siteasy"}
```

## output
Which folder to generate the static web site. 
demo:
```json
{"output":""}
```
will generate the site to the root directory.  

The setting
```json
{"output":"output"}
```
will make a folder "output" under root directory and generate the site to this "output" folder.  

## footer
The context of footer.  
demo:
```json
{"footer":"Siteasy - Make static site generation life easy"}
```

## add_date
Whether to add crated datetime to the article. Todo.
demo:
```json
{"add_date": false}
```

## cates
The configuration of headers.  
demo:
```json
{
    "cates": {
        "News": {}, 
        "Docs":{}, 
        "Themes":{}, 
        "Community":{}, 
        "github":{"url":"https://siteasy.github.io"}
    }
}
```
Description:
- The keys is the text of the categories.
- If the value of the category is empty, then
  - If there is a index.md under the category of articles, the index.html which generated from index.md will be put as the homepage of the category.
  - If there is no index.md under the category of articles, the list.html which list all articles of the category will be put as the homepage of category.
- If the value contains the key "url", that means the category is a external link.

# plugins
The plugins used for the website.
demo:
```json
{
    plugins: {
        "all_cates":["list"],
        "index":["Jumbotron"]
    }
}
```
description:
- the keys describe which page is selected to apply the plugins
- If the key is "all_cates", all pages are selected to apply the plugins
- If the key is "index", only the index of the website is selected to apply the plugins
- If the key is one of the categories, only the pages of the category are selected to apply the plugins.
