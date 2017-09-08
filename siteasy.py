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
from models import BaseView, BasePlugin
from settings import env,global_config,PLUGINS_PATH,global_site_map

#logger = logging.getLogger("mylogger")

class Site:
    def __init__(self):
        #self.header = HeaderView()
        self.header = []

    def gen_views(self):
        self.indexview = BaseView(is_cate = True,tpl='index.html')
        if os.path.lexists(os.path.join('articles','index.md')):
            self.indexview.set_md_file('index.md')
            self.indexview.apply_md_file()
        for cate in global_config['cates'].keys():
            cateview = BaseView(cate,tpl='index.html',is_cate=True)
            cateview.set_parent(self.indexview)
            cateview.apply_config(global_config['cates'][cate])
            if os.path.lexists(os.path.join('articles',cate,'index.md')):
                cateview.set_md_file('index.md')
                cateview.apply_md_file()
            #external link
            if 'url' in global_config['cates'][cate].keys():
                cateview.set_ext_url(global_config['cates'][cate]['url'])
            else:
                os.mkdir(os.path.join(global_config['output'],cate))
                cateview.set_tpl('index.html')
                cateview.gen_children()
            global_site_map.append(cateview.gen_site_map())
            self.header.append(cateview)
        #self.indexview.gen_site_map()

    def apply_plugins(self):
        for cate in global_config['plugins']:
            for plugin_text in global_config['plugins'][cate]:
                plugin_module = __import__(PLUGINS_PATH + '.' + plugin_text)
                plugin = getattr(plugin_module,plugin_text).Plugin(plugin_text)
                if cate == 'all_cates':
                    for cate_ in  global_config['cates'].keys():
                        cateview = BaseView.get_by_text(cate_)
                        cateview.apply_plugin(plugin)
                elif cate == 'index':
                    self.indexview.apply_plugin(plugin)
                else:
                    cateview = BaseView.get_by_text(cate)
                    cateview.apply_plugin(plugin)

    def gen_html(self):
        self.indexview.gen_html()
        #self.indexview.gen_html() #indexview is in mainviews

    def gen(self):
        BasePlugin.all_articles = BaseView.instances
        #self.gen_index()
        self.gen_views()
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
    global_site_map.clear()
    BaseView.clear()
    if global_config['output'].count('..') or global_config['output'] in [global_config['articles_path'],PLUGINS_PATH,'theme']:
        raise Exception("Invalid output path")
    if global_config['output'] in ['','/','./','.']:
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

