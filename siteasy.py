import os
from collections import OrderedDict
import shutil
import re
import json
from http.server import HTTPServer, CGIHTTPRequestHandler 
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = None

def loadjson(fn):
    f = open(fn)
    c = json.loads(f.read(),object_pairs_hook=OrderedDict)
    f.close()
    return c

def config():
    global env
    c = loadjson('config.json')
    env = Environment(
        loader=FileSystemLoader(os.getcwd() + os.sep + 'theme' + os.sep + c['theme']),
        autoescape=select_autoescape(['html', 'xml'])
    )
    return c
global_config = config()

def render(tpl,context):
    t = env.get_template(template) 
    return t.render(context_dict)


def gen_html(template,md,config,output):
    title = md.split('\n')[0].replace('#','').strip()
    context_dict = {
        'title':title,
        'md_content':md,
    }
    context_dict.update(config)
    context_dict.update(global_config)
    s = render(template,context_dict)
    #print(context_dict)
    f = open('output' + os.sep + output,'w')
    f.write(s)
    f.close()
    print('Generate %s from %s'%(output,md))

def serve(path):
    PORT = 8000
    httpd = HTTPServer(('localhost', PORT), CGIHTTPRequestHandler)
    if not path:
        os.chdir('output')
    print('serving at port', PORT)
    httpd.serve_forever()

INDEX_CATE = 0
LIST_CATE = 1
DIRECT_CATE = 2

def gen_cates():
    cates = []
    for cate in global_config['cates'].keys():
        #the category which contains index.md 
        if ('index' in global_config['cates'][cate] and global_config['cates'][cate]['index']) or os.path.lexists(os.path.join('articles',cate,'index.md')):
            os.mkdir('output'+os.sep+cate)
            global_config['cates'][cate].update({'url':'/'+cate+'/index.html','text':cate})
            cates.append((cate,INDEX_CATE))
        #specify the page which have no directory
        elif not os.path.lexists(os.path.join('articles',cate)):
            global_config['cates'][cate].update({'url':'/'+global_config['cates'][cate]['url'],'text':global_config['cates'][cate]['text']})
            cates.append((cate,DIRECT_CATE))
        #cates which have no index.md 
        elif os.path.isdir('articles'+os.sep + cate):
            os.mkdir('output'+os.sep+cate)
            global_config['cates'][cate].update({'url':'/'+cate+'/list.html','text':cate})
            cates.append((cate,LIST_CATE))
    for cate,t in cates:
        get_site_items(cate)
        if t == INDEX_CATE:
            gen_html('index.html',get_md_content(os.path.join('articles',cate,'index.md')),global_config,os.path.join(cate,'index.html'))
        elif t == DIRECT_CATE:
            gen_html('detail.html',get_md_content(os.path.join('articles',global_config['cates'][cate]['md'])),global_config,global_config['cates'][cate]['url'])
        elif t == LIST_CATE:
            gen_html('list.html','',global_config,os.path.join(cate,'list.html'))


def get_md_content(fn):
    f = open(fn)
    s = f.read()
    f.close()
    return s

def get_articles(cate):
    if os.path.isdir('articles'+os.sep + cate):
        if 'articles' in global_config['cates'][cate].keys() and global_config['cates'][cate]['articles']:
            fs = global_config['cates'][cate]['articles']
        else:
            fs_tuple = sorted([(fn, os.stat('articles'+os.sep+cate+os.sep+fn)) for fn in os.listdir('articles' + os.sep + cate)], key = lambda x: x[1].st_ctime,reverse=True)
        return [f[0] for f in fs_tuple if os.path.splitext(f[0])[1] == '.md' and os.path.splitext(f[0])[0] != 'index']
    else:
        return []


def get_site_items(cate):
    global_config.update({'side_items':[]})
    fs = get_articles(cate)
    for fn in fs:
        fn,ext = os.path.splitext(fn)
        global_config['side_items'].append({'url':'/'+cate+'/'+fn+'.html','text':fn})

class BaseView:
    def __init__(self,cate,tpl="",md_file="",out="",extra_data={}):
        self.cate = cate
        self.md_file = md_file
        self.tpl = tpl
        self.extra_data = extra_data
        self.out = out

    def gen_html(self,cate_data):
        if md_file:
            md_path = os.path.join(global_config['articles_path'],self.cate,self.md_file)
            md = get_md_content(md_path)
            if not self.out:
                self.out = os.path.splitext(md_path)[0] + '.html'
        else:
            md = ''
        self.extra_data.update(cate_data)
        gen_html(self.tpl,md,self.extra_data,self.out):

class CateView(BaseView):
    def set_url(self,url = None):
        if url:
            self.url = self.cate + '/' + url
        else:
            self.url = self.cate + '/' + self.out

class MainView(BaseView):
    pass

class HeaderView:
    def __init__(self):
        self.cateviews = []

    def add_cate(self,cateview):
        self.cateviews.append(cateview)

    def get_cates(self):
        return [{'url':cate.url,'text':cateview.cate} for cateview in self.cateviews]

    def gen_html(self):
        for cateview in self.cateviews:
            cateview.gen_html()

class Site:
    def __init__(self):
        clear_output()
        self.header = HeaderView()
        self.mainviews = []
        self.plugins = []

    def gen_cates(self):
        for cate in global_config['cates'].keys():
            #the category which md file is specified in config.json
            if ('index' in global_config['cates'][cate] and global_config['cates'][cate]['index']):
                cate = CateView(cate,'index.html',global_config['cates'][cate]['index'],'index.html')
            #the category which contains index.md 
            elif os.path.lexists(os.path.join('articles',cate,'index.md'):
                cate = CateView(cate,'index.html','index.md','index.html')
            #specify the page which have no directory. Which can be single page or external link
            elif not os.path.lexists(os.path.join('articles',cate)):
                cate = CateView(cate)
            #cates which have no index.md and have some pages in the folder
            elif os.path.isdir('articles'+os.sep + cate):
                cate = CateView(cate,'list.html','','list.html')
            if global_config['cates'][cate]['url']:
                cate.set_url(global_config['cates'][cate]['url'])
            else:
                cate.set_url()
            self.header.add_cate(cate)

    def gen_mainviews(self):
        for cate in self.header.get_cates(text_only = 1):
            fs = get_articles(cate['text'])
            self.cate_list = []
            self.handle_plugins(cate)
            for f in fs:
                fn,ext = os.path.splitext(f)
                if ext == '.md' and fn != 'index':
                    self.mainviews.append(MainView(cate['text'],'detail.html',f,'',self.plugins_context))
                    self.cate_list.append({'url':cate['text']+'/'+fn+'.html','text':fn})

    def update_plugins_context(self,plugin,plugin_cate):
        for area in plugin_cate.keys():
            tpl = os.path.join('plugins',plugin,plugin_cate[area]['tpl'])
            if type(plugin_cate[area]['context']) == type(str):
                context = getattr(self,plugin_cate[area]['context'])
            else:
                context = plugin_cate[area]['context']
            self.plugins_context.update({area+'_context':render(tpl,context)})

    def handle_plugins(self,cate):
        plugins = global_config['plugins']
        self.plugins_context = {}
        for plugin in plugins:
            plugin_config = loadjson(os.path.join('plugins',plugin,'config.json')
            cates = plugin_config.keys()
            if 'all_cates' in cates:
                self.update_plugins_context(plugin,plugin_config['all_cates'])
            if cate in cates:
                self.update_plugins_context(plugin,plugin_config[cate])

    def gen(self):
        self.gen_cates()
        self.gen_mainviews()

def clear_output():
    if os.path.lexists('output'):
        shutil.rmtree('output')
    os.mkdir(os.getcwd()+os.sep+'output')


def run():
    clear_output()
    gen_cates()
    #generate pages
    for cate in global_config['cates'].keys():
        fs = get_articles(cate)
        get_site_items(cate)
        articles = []
        for f in fs:
            fn,ext = os.path.splitext(f)
            if ext == '.md' and fn != 'index':
                articles.append({'url':'/'+cate+'/'+fn+'.html','text':fn})
                print(global_config)
                gen_html('detail.html',get_md_content(os.path.join('articles',cate,f)),global_config,os.path.join(cate,fn+'.html'))
        global_config.update({'articles':articles})


    global_config.update({'side_items':[]})
    gen_html('index.html',get_md_content(os.path.join('articles',global_config['index'])),global_config,'index.html')
    shutil.copy('output'+os.sep+'index.html','index.html')
    
    serve(global_config['path_prefix'])

if __name__ ==  '__main__':
    run()

