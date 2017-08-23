import os
import copy
from collections import OrderedDict
import shutil
import re
import json
from http.server import HTTPServer, CGIHTTPRequestHandler 
from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
import logging
import logging.config


VERSION = "0.1.0"

env = None
PLUGINS_PATH = 'plugins'

LOGGING = {
    'version': 1,
    #'formatters':{
    #    'default': {
    #        'format': '%(asctime)s %(levelname)s %(name)s %(message)s'
    #    },
    #},
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file':{
            'class': 'logging.FileHandler',
            #'formatter': 'default',
            'filename': 'site.log',
            'mode': 'w',
            #'encoding': 'utf-8',
        },
    },
    'root': {
        'handlers': ['file'],
        'level' : 'INFO',
    },
}

logging.config.dictConfig(LOGGING)
logger = logging.getLogger("mylogger")

def loadjson(fn):
    f = open(fn)
    c = json.loads(f.read(),object_pairs_hook=OrderedDict)
    f.close()
    return c

def config():
    global env
    c = loadjson('config.json')

    env = Environment(
        loader=FileSystemLoader([os.path.join(os.getcwd(),'theme',c['theme']),os.path.join(os.getcwd(),PLUGINS_PATH)]),
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
    #print('Generate %s from %s with template=%s'%(output,md,template))
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

class BasePlugin:
    def __init__(self,name):
        self.name = name
        self.config = loadjson(os.path.join('plugins',name,'config.json'))

    def apply(self,view):
        plugin_context = {}
        for area in self.config.keys():
            plugin_context.update({area:{'tpl':self.name +'/'+self.config[area]['tpl']}})
            plugin_context[area].update({'context':self.config[area]['context']})
        return plugin_context 
        

class BaseView:
    instances = []
    def __init__(self,text,tpl="",md_file="",out="",context={}):
        self.text = text
        self.cateview = NoneObject()
        self.md_file = md_file
        self.tpl = tpl
        self.context = context
        self.out = out
        self.instances.append(self)
        self.plugins = {} # {"sider" [{'tpl':'','context':''}]
        self.classname = self.__class__.__name__

    @classmethod
    def get_by_text(cls,text):
        for view in cls.instances:
            if view.text == text:
                return view 
        raise Exception("Instance %s not found"%text)


    def update_extra_context(self,extra_context):
        self.context.update(extra_context)

    def update_plugin_context(self):
        if self.classname == 'MainView' and type(self.cateview) != NoneObject:
            self.merge_plugin(self.cateview.plugins)
        self.context.update({'plugins_context':self.plugins})
        if 'sider' in self.plugins.keys():
            self.context.update({'has_sider':True})


    def gen_html(self):
        self.update_plugin_context()
        logger.debug("gen_html cate=%s from md file=%s with tpl=%s and context=\n%s\n"%(self.cateview.text,self.md_file,self.tpl,json.dumps(self.context,indent=4,sort_keys=True)))
        if self.md_file:
            md_path = os.path.join(global_config['articles_path'],self.cateview.text,self.md_file)
            md = get_md_content(md_path)
            if not self.out:
                self.out = os.path.splitext(self.md_file)[0] + '.html'
        else:
            md = ""
        gen_html(self.tpl,md,self.context,os.path.join(self.cateview.text,self.out))

    def merge_plugin(self,plugin):
        logger.debug("%s merge plugin %s"%(self.text,json.dumps(plugin,indent=4,sort_keys=True)))
        k_plugins = set(self.plugins.keys())
        k_plugin = set(plugin)
        k_plugins.update(k_plugin)
        for k in k_plugins:
            if k not in self.plugins.keys():
                self.plugins.update({k:plugin[k]})
            elif k in plugin.keys():
                self.plugins[k].extend(plugin[k])
        logger.debug("%s after merge plugins %s"%(self.text,json.dumps(self.plugins,indent=4,sort_keys=True)))
        self.plugins = copy.deepcopy(self.plugins)


    def apply_plugin(self,plugin):
        logger.debug("%s before apply plugins = %s"%(self.text,self.plugins))
        context_plugin = plugin.apply(self)
        logger.debug("%s after apply plugins = %s"%(self.text,self.plugins))
        for k in context_plugin:
            context_plugin[k] = [context_plugin[k]]
        self.merge_plugin(context_plugin)

class CateView(BaseView):
    def __init__(self,text,tpl="",md_file="",out="",context={}):
        super(CateView,self).__init__(text,tpl,md_file,out,context)
        self.is_ext_url = False
        self.cateview = self
        self.mainviews = []

    def set_url(self,url = None):
        if url:
            self.url = url
            self.is_ext_url = True
        else:
            self.url = '/' + self.text + '/' + self.out

class MainView(BaseView):

    def set_cateview(self,cateview):
        self.cateview = cateview
        cateview.mainviews.append(self)

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

    def gen_mainviews(self):
        if os.path.lexists(os.path.join('articles','index.md')):
            self.indexview = MainView('index','index.html','index.md',context=global_config['index'])
        else:
            self.indexview = MainView('index','index.html','index.md',context=global_config['index'])
        self.mainviews.append(self.indexview)

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
                else:
                    self.header.apply_plugin_to_cate(cate,plugin)


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
        self.apply_plugins()
        self.gen_html()

def serve(path):
    server = Server()
    server.watch(global_config['articles_path'],build)
    #server.watch(PLUGINS_PATH,build)
    server.watch(os.path.join('theme',global_config['theme']),build)
    #server.watch('siteasy.py',build)
    server.watch('config.json',build)
    print("serve... ")
    server.serve(root=global_config['output'])


def clear_output():
    if global_config['output'].count('..') or global_config['output'] in [global_config['articles_path'],PLUGINS_PATH,'theme']:
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

