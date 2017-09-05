from utils import get_md_content,render,loadjson
from settings import global_config,logging
import os
import json
import copy

class NoneObject:
    def __init__(self):
        self.text = ""

class BaseView:
    instances = []
    def __init__(self,text,tpl="",md_file="",out="",context={},not_in_instances = 0):
        self.text = text
        self.cateview = NoneObject()
        self.md_file = md_file
        self.tpl = tpl
        self.context = copy.deepcopy(context)
        self.out = out
        if not not_in_instances:
            self.instances.append(self)
        self.plugins = {} # {"sider" [{'tpl':'','context':''}]
        self.classname = self.__class__.__name__

    #def __repr__(self):
    #    return self.classname + ':' + self.text

    @classmethod
    def clear(cls):
        cls.instances = []

    @classmethod
    def get_by_text(cls,text):
        #print("text=%s; ins_len=%d"%(text,len(cls.instances)))
        for view in cls.instances:
            #print ("view.text=",view.text)
            if view.text.lower() == text.lower():
                return view 
        raise Exception("Instance %s not found"%text)

    def apply_md_file(self):
        if self.md_file:
            md_path = os.path.join(global_config['articles_path'],self.cateview.text,self.md_file)
            self.md_content,self.short_md_content,title,date = get_md_content(md_path)
            self.date = date
            self.context.update({'title':title,'short_md_content':self.short_md_content})
            if not self.out:
                self.out = os.path.splitext(self.md_file)[0] + '.html'
        else:
            self.md_content = ''
            self.short_md_content = ''

    def update_extra_context(self,extra_context):
        self.context.update(extra_context)

    def update_plugin_context(self):
        if self.classname == 'MainView' and type(self.cateview) != NoneObject:
            self.merge_plugin(self.cateview.plugins)
        self.context.update({'plugins_context':self.plugins})
        if 'sider' in self.plugins.keys():
            self.context.update({'has_sider':True})


    def gen_html(self):
        logging.debug("%s update_articles %s: %s"%(str(self),self.text,json.dumps(self.context,indent=4,sort_keys=True)))
        self.update_plugin_context()
        logging.debug("gen_html text=%s cate=%s from md file=%s with tpl=%s and context=\n%s\n"%(self.text, self.cateview.text,self.md_file,self.tpl,json.dumps(self.context,indent=4,sort_keys=True)))
        #gen_html(self.tpl,self.md_content,self.context,os.path.join(self.cateview.text,self.out))
        self.context.update({'md_content':self.md_content,'short_md_content':self.short_md_content})
        self.context.update(global_config)
        s = render(self.tpl,self.context)
        #print(context_dict)
        f = open(os.path.join(global_config['output'],self.cateview.text,self.out),'w')
        f.write(s)
        f.close()

    def merge_plugin(self,plugin):
        logging.debug("%s merge plugin %s"%(self.text,json.dumps(plugin,indent=4,sort_keys=True)))
        k_plugins = set(self.plugins.keys())
        k_plugin = set(plugin)
        k_plugins.update(k_plugin)
        for k in k_plugins:
            if k not in self.plugins.keys():
                self.plugins.update({k:plugin[k]})
            elif k in plugin.keys():
                self.plugins[k].extend(plugin[k])
        logging.debug("%s after merge plugins %s"%(self.text,json.dumps(self.plugins,indent=4,sort_keys=True)))
        self.plugins = copy.deepcopy(self.plugins)

    def apply_plugin(self,plugin):
        logging.debug("%s before apply plugins = %s"%(self.text,self.plugins))
        context_plugin = plugin.apply(self)
        logging.debug("%s after apply plugins = %s"%(self.text,self.plugins))
        for k in context_plugin:
            context_plugin[k] = [context_plugin[k]]
        self.merge_plugin(context_plugin)

class CateView(BaseView):
    def __init__(self,text,tpl="",md_file="",out="",context={}):
        super(CateView,self).__init__(text,tpl,md_file,out,context)
        self.is_ext_url = False
        self.cateview = self
        self.mainviews = []
        self.apply_config()
        self.article_list = []

    def apply_config(self):
        cate_config = global_config['cates'][self.text]
        if 'order' in cate_config.keys():
            self.order = cate_config['order']
        else:
            self.order = []

    def set_url(self,url = None):
        if url:
            self.url = url
            self.is_ext_url = True
        else:
            self.url = '/' + self.text + '/' + self.out

    def update_articles(self):
        if self.order: #global config.json have articles order
            order_articles = [a.lower() for a in self.order]
            for arti in order_articles:
                mainview = MainView.get_by_text(arti)
                self.article_list.append({'url':'/'+self.text+'/'+mainview.text+'.html','text':mainview.text})
            for mainview in self.mainviews:
                if mainview.text.lower() not in order_articles:
                    self.article_list.append({'url':'/'+self.text+'/'+mainview.text+'.html','text':mainview.text})
        else:
            mainview_list = sorted(self.mainviews, key=lambda k : k.date)
            self.article_list = [{'url':'/'+self.text+'/'+mainview.text+'.html','text':mainview.text} for mainview in self.mainviews]
        self.update_extra_context({'articles':self.article_list})
        logging.debug("%s update_articles %s: %s"%(str(self),self.text,json.dumps(self.context,indent=4,sort_keys=True)))

class MainView(BaseView):
    def set_cateview(self,cateview):
        self.cateview = cateview
        cateview.mainviews.append(self)

class BasePlugin:
    all_articles = None
    def __init__(self,name):
        self.name = name
        self.config = loadjson(os.path.join('plugins',name,'config.json'))
        self.areas = self.config.keys()

    def apply(self,view):
        plugin_context = {}
        for area in self.areas:
            plugin_context.update({area:{'tpl':self.name +'/'+self.config[area]['tpl']}})
            plugin_context[area].update({'context':self.config[area]['context']})
        return plugin_context 

