import os
from collections import OrderedDict
import shutil
import re
import json
from http.server import HTTPServer, CGIHTTPRequestHandler 
from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server

VERSION = "0.1.0"

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
        loader=FileSystemLoader([os.path.join(os.getcwd(),'theme',c['theme']),os.path.join(os.getcwd(),'plugins')]),
        autoescape=select_autoescape(['html', 'xml'])
    )
    return c
global_config = config()

def render(tpl,context):
    t = env.get_template(tpl) 
    return t.render(context)

def get_md_content(md_path):
    f = open(md_path)
    s = f.read()
    f.close()
    return s



def gen_html(template,md,config,output):
    print('Generate %s from %s with template=%s'%(output,md,template))
    title = md.split('\n')[0].replace('#','').strip()
    context_dict = {
        'title':title,
        'md_content':md,
    }
    context_dict.update(config)
    context_dict.update(global_config)
    s = render(template,context_dict)
    #print(context_dict)
    f = open(os.path.join(global_config['output'],output),'w')
    f.write(s)
    f.close()

#def serve(path):
#    PORT = 8000
#    httpd = HTTPServer(('localhost', PORT), CGIHTTPRequestHandler)
#    os.chdir(path)
#    print('serving %s at port'%(path), PORT)
#    httpd.serve_forever()


def get_articles(cate):
    if os.path.isdir('articles'+os.sep + cate):
        if 'articles' in global_config['cates'][cate].keys() and global_config['cates'][cate]['articles']:
            fs = global_config['cates'][cate]['articles']
        else:
            fs_tuple = sorted([(fn, os.stat('articles'+os.sep+cate+os.sep+fn)) for fn in os.listdir('articles' + os.sep + cate)], key = lambda x: x[1].st_ctime,reverse=True)
        return [f[0] for f in fs_tuple if os.path.splitext(f[0])[1] == '.md' and os.path.splitext(f[0])[0] != 'index']
    else:
        return []

class NoneObject:
    def __init__(self):
        self.text = ""

class BaseView:
    def __init__(self,tpl="",md_file="",out="",context={}):
        self.cateview = NoneObject()
        self.md_file = md_file
        self.tpl = tpl
        self.context = context
        self.out = out

    def update_extra_context(self,extra_context):
        self.context.update(extra_context)

    def gen_html(self):
        print("gen_html cate=%s from md file=%s with tpl=%s and context=%s"%(self.cateview,self.md_file,self.tpl,self.context))
        if self.md_file:
            md_path = os.path.join(global_config['articles_path'],self.cateview.text,self.md_file)
            md = get_md_content(md_path)
            if not self.out:
                self.out = os.path.splitext(self.md_file)[0] + '.html'
        else:
            md = ""
        gen_html(self.tpl,md,self.context,os.path.join(self.cateview.text,self.out))

class CateView(BaseView):
    def __init__(self,text,tpl="",md_file="",out="",context={}):
        super(CateView,self).__init__(tpl,md_file,out,context)
        self.text = text
        self.is_ext_url = False
        self.cateview = self

    def set_url(self,url = None):
        if url:
            self.url = url
            self.is_ext_url = True
        else:
            self.url = '/' + self.text + '/' + self.out

class MainView(BaseView):
    def set_cateview(self,cateview):
        self.cateview = cateview

class HeaderView:
    def __init__(self):
        self.cateviews = []

    def add_cate(self,cateview):
        self.cateviews.append(cateview)

    def get_cates_link(self):
        return [{'url':cateview.url,'text':cateview.text} for cateview in self.cateviews]

    def update_extra_context(self,extra_context):
        for cateview in self.cateviews:
            cateview.update_extra_context(extra_context)

    def gen_html(self):
        for cateview in self.cateviews:
            if not cateview.is_ext_url:
                cateview.gen_html()

class Site:
    def __init__(self):
        self.header = HeaderView()
        self.mainviews = []
        self.plugins = []

    #def gen_index(self):
    #    if not os.path.lexists(os.path.join('articles','index.md')):
    #        raise Exception("[Homepage error] There should be a index.md in your article directory as homepage.")
    #    self.indexview = MainView('index.html','index.md')

    def gen_cates(self):
        for cate in global_config['cates'].keys():
            #the category which md file is specified in config.json
            if ('index' in global_config['cates'][cate] and global_config['cates'][cate]['index']):
                cateview = CateView(cate,'index.html',global_config['cates'][cate]['index'],'index.html')
            #the category which contains index.md 
            elif os.path.lexists(os.path.join('articles',cate,'index.md')):
                cateview = CateView(cate,'index.html','index.md','index.html')
            #cates which have no index.md and have some pages in the folder
            else:
                cateview = CateView(cate,'list.html','','list.html')
            #external link
            if 'url' in global_config['cates'][cate].keys():
                cateview.set_url(global_config['cates'][cate]['url'])
            else:
                os.mkdir(os.path.join(global_config['output'],cate))
                cateview.set_url()
            self.header.add_cate(cateview)

    def gen_mainviews(self):
        if os.path.lexists(os.path.join('articles','index.md')):
            indexview = MainView('index.html','index.md',context=global_config['index'])
        else:
            indexview = MainView('index.html','index.md',context=global_config['index'])
        self.mainviews.append(indexview)

        for cateview in self.header.cateviews:
            fs = get_articles(cateview.text)
            self.article_list = [] #for plugins which show list of articles
            for f in fs:
                fn,ext = os.path.splitext(f)
                self.article_list.append({'url':'/'+cateview.text+'/'+fn+'.html','text':fn})
                if ext == '.md' and fn != 'index':
                    mainview = MainView('detail.html',f,'',{}) 
                    mainview.set_cateview(cateview)
                    self.mainviews.append(mainview)
            self.handle_plugins(cateview)

    def update_cate_plugins_context(self,plugin,plugin_cate):
        for area in plugin_cate.keys():
            tpl = '/'.join([plugin,plugin_cate[area]['tpl']])
            if type(plugin_cate[area]['context']) == type(""):
                context = {plugin_cate[area]['context']:getattr(self,plugin_cate[area]['context'])}
            else:
                context = plugin_cate[area]['context']
            self.plugins_context.update({area+'_context':render(tpl,context)})

    def handle_plugins(self,cateview):
        plugins = global_config['plugins']
        self.plugins_context = {}
        for plugin in plugins:
            plugin_config = loadjson(os.path.join('plugins',plugin,'config.json'))
            cates = plugin_config.keys()
            if 'all_cates' in cates:
                self.update_cate_plugins_context(plugin,plugin_config['all_cates'])
            if cateview.text in cates:
                self.update_cate_plugins_context(plugin,plugin_config[cate])

    def update_context(self):
        self.header.update_extra_context({"cates_link":self.header.get_cates_link()})
        #self.indexview.update_extra_context({"cates_link":self.header.get_cates_link()})
        for mainview in self.mainviews:
            mainview.update_extra_context({"cates_link":self.header.get_cates_link()})
            

    def update_plugin_context(self):
        #self.indexview.update_extra_context(self.plugin_config)
        self.header.update_extra_context(self.plugins_context)
        for mainview in self.mainviews:
            mainview.update_extra_context(self.plugins_context)

    def gen_html(self):
        #self.indexview.gen_html()
        self.header.gen_html()
        for mainview in self.mainviews:
            mainview.gen_html()

    def gen(self):
        self.gen_cates()
        self.gen_mainviews()
        #self.gen_index()
        self.update_context()
        self.update_plugin_context()
        self.gen_html()

def serve(path):
    server = Server()
    server.watch(global_config['articles_path'],build)
    server.watch(os.path.join('theme',global_config['theme']),build)
    server.watch('siteasy.py',build)
    server.watch('config.json',build)
    server.serve(root=global_config['output'])


def clear_output():
    if global_config['output'].count('..') or global_config['output'] in [global_config['articles_path'],'plugins','theme']:
        raise Exception("Invalid output path")
    if global_config['output'] in ['','/','./']:
        for cate in global_config['cates'].keys():
            if os.path.lexists(cate):
                shutil.rmtree(cate)
    else:
        shutil.rmtree(global_config['output'])
        os.mkdir(os.getcwd()+os.sep+global_config['output'])

def build():
    clear_output()
    site = Site()
    site.gen()

def run():    
    build()
    serve(global_config['output'])

if __name__ ==  '__main__':
    run()

