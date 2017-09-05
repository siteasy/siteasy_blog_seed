import os
import time
import copy
from collections import OrderedDict
import shutil
import re
import json
from http.server import HTTPServer, CGIHTTPRequestHandler 
from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from models import MainView, CateView, BasePlugin
from settings import env,global_config,PLUGINS_PATH


#logger = logging.getLogger("mylogger")




#def gen_html(template,md,config,output):
#    #print('Generate %s from %s with template=%s'%(output,md,template))
#    #title = md.split('\n')[0].replace('#','').strip()
#    context_dict = {
##        'title':title,
#        'md_content':md,
#    }
#    context_dict.update(config)
#    context_dict.update(global_config)
#    s = render(template,context_dict)
#    #print(context_dict)
#    f = open(os.path.join(global_config['output'],output),'w')
#    f.write(s)
#    f.close()

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

    def apply_plugin_to_all_cates(self,plugin):
            for cateview in self.cateviews:
                cateview.apply_plugin(plugin)

    def apply_plugin_to_cate(self,cate,plugin):
        cateview = CateView.get_by_text(cate)
        if cateview:
            cateview.apply_plugin(plugin)

    def apply_md_file(self):
        for cateview in self.cateviews:
            if not cateview.is_ext_url:
                cateview.apply_md_file()
                
    def update_articles(self):
        for cateview in self.cateviews:
            cateview.update_articles()


    def gen_html(self):
        for cateview in self.cateviews:
            if not cateview.is_ext_url:
                cateview.gen_html()


class Site:
    def __init__(self):
        self.header = HeaderView()
        self.mainviews = []

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

    def gen_index(self):
        mainview_list = sorted(MainView.instances, key=lambda k : k.date)
        article_list = [{'url':'/'+view.cateview.text+'/'+view.text+'.html','text':view.text,'short_md_content':view.short_md_content} for view in mainview_list]
        index_context = {'articles':article_list}
        index_context.update(global_config['index'])
        #print(index_context)
        if os.path.lexists(os.path.join('articles','index.md')):
            self.indexview = MainView('index','index.html','index.md','index.html',context=index_context)
        else:
            self.indexview = MainView('index','list.html','','index.html',context=index_context)
        self.mainviews.append(self.indexview)

    def gen_mainviews(self):
        #gen categories and articles
        for cateview in self.header.cateviews:
            fs = get_articles(cateview.text)
            for f in fs:
                fn,ext = os.path.splitext(f)
                if ext == '.md' and fn != 'index':
                    mainview = MainView(fn,'detail.html',f,'',{}) 
                    mainview.set_cateview(cateview)
                    self.mainviews.append(mainview)

    def update_context(self):
        self.header.update_extra_context({"cates_link":self.header.get_cates_link()})
        #self.indexview.update_extra_context({"cates_link":self.header.get_cates_link()})
        for mainview in self.mainviews:
            mainview.update_extra_context({"cates_link":self.header.get_cates_link()})
            
    def apply_plugins(self):
        for cate in global_config['plugins']:
            for plugin_text in global_config['plugins'][cate]:
                plugin_module = __import__(PLUGINS_PATH + '.' + plugin_text)
                plugin = getattr(plugin_module,plugin_text).Plugin(plugin_text)
                if cate == 'all_cates':
                    self.header.apply_plugin_to_all_cates(plugin)
                elif cate == 'index':
                    self.indexview.apply_plugin(plugin)
                else:
                    self.header.apply_plugin_to_cate(cate,plugin)

    def apply_md_file(self):
        self.header.apply_md_file()
        for mainview in self.mainviews:
            mainview.apply_md_file()


    def gen_html(self):
        #self.indexview.gen_html() #indexview is in mainviews
        self.header.gen_html()
        for mainview in self.mainviews:
            mainview.gen_html()

    def gen(self):
        self.gen_cates()
        self.gen_mainviews()
        BasePlugin.all_articles = MainView.instances
        #self.gen_index()
        self.apply_md_file()
        self.header.update_articles()
        self.gen_index()
        self.update_context()
        self.indexview.apply_md_file()
        self.apply_plugins()
        self.gen_html()
        self.copy_static()

    def copy_static(self):
        theme_path = os.path.join(os.getcwd(),'theme',global_config['theme'],'static')
        if os.path.lexists('static'):
            shutil.rmtree('static')
        if os.path.lexists(theme_path):
            shutil.copytree(theme_path,os.path.join(global_config['output'],'static'))




def serve(path):
    server = Server()
    server.watch(global_config['articles_path'],build)
    #server.watch(PLUGINS_PATH,build)
    server.watch(os.path.join('theme',global_config['theme']),build)
    #server.watch('siteasy.py',build)
    server.watch('config.json',build)
    print("serve... ")
    server.serve(root=global_config['output'])


def init():
    MainView.clear()
    if global_config['output'].count('..') or global_config['output'] in [global_config['articles_path'],PLUGINS_PATH,'theme']:
        raise Exception("Invalid output path")
    if global_config['output'] in ['','/','./']:
        for cate in global_config['cates'].keys():
            if os.path.lexists(cate):
                shutil.rmtree(cate)
        if os.path.lexists('index.html'):
            os.remove('index.html')
    else:
        shutil.rmtree(global_config['output'])
        os.mkdir(os.getcwd()+os.sep+global_config['output'])

def build():
    init()
    site = Site()
    site.gen()

def run():    
    build()
    serve(global_config['output'])


if __name__ ==  '__main__':
    run()

