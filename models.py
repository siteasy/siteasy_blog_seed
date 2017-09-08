from utils import get_md_content,render,loadjson
from settings import global_config,logging,global_context,global_site_map
import os
import json
import copy

class BaseView:
    """
    site_map format:
    [
        'cate0':{'id':self.id, 'text': self.text, 'selected': True/False, 'sub': site_map },
        'cate1':{'id':self.id, 'text': self.text, 'selected': True/False, 'sub': site_map },
        ...
    ]
    """
    id_next = 0
    instances = []
    def __init__(self,text="",md_file="",tpl="",is_cate=False,not_in_instances = 0):
        self.text = text
        self.md_file = md_file
        self.tpl = tpl
        self.context = {"site_map":{"sub":[]}}
        #self.out = out
        if not not_in_instances:
            self.instances.append(self)
        self.plugins_context = {} # {"sider" [{'tpl':'','context':''}]
        self.classname = self.__class__.__name__
        #self.is_ext_url = False
        self.id = self.id_next
        self.id_next += 1
        self.children = []
        self.parent = None
        self.ext_url = ""
        self.url = text
        self.is_cate = is_cate
        self.order = []
        self.date = None
        self.md_content = ''
        self.short_md_content = ''

    def __repr__(self):
        return self.classname + ':' + self.text

    def set_ext_url(self,url = None):
        self.ext_url = url

    def set_tpl(self,tpl):
        self.tpl = tpl

    def get_path(self):
        paths = []
        obj = self
        while obj.parent:
            paths.append(obj.text)
            obj = obj.parent
        paths.reverse()
        mypath = os.path.sep.join(paths)
        return mypath

    def get_article_path(self):
        return global_config['articles_path'] + os.sep + self.get_path()

    def get_md_path(self):
        if self.is_cate:
            if not self.text: #index
                arti_path = 'index.md'
            else:
                arti_path = self.get_path() + os.sep + 'index.md'
        else:
            arti_path = self.get_path() + '.md'
        return global_config['articles_path'] + os.sep + arti_path

    def get_output_path(self):
        if self.is_cate:
            if self.get_path():
                return global_config['output'] + os.sep + self.get_path() + os.sep + 'index'
            else: #site index
                return global_config['output'] + os.sep + 'index'
        else:
            return global_config['output'] + os.sep + self.get_path() 
            
    def gen_children(self):
        path = self.get_article_path()
        if os.path.isdir(path):
            if self.order:
                flist = [arti+'.md' for arti in self.order]
            else:
                flist = sorted([fn for fn in os.listdir(path) if os.path.isfile(os.path.join(path,fn))], key = lambda x: os.stat(os.path.join(path,x)).st_ctime,reverse=True)
            #TODO check if flist with config.json has inccorect file name
            article_list = [(os.path.splitext(fn)[0],fn) for fn in flist if os.path.splitext(fn)[1] == '.md' and os.path.isfile(os.path.join(path,fn)) and os.path.splitext(fn)[0] != 'index']
            #print("flist of %s = %s %s"%(path,flist,article_list))
            for arti,md_file in article_list:
                mainview = BaseView(arti,md_file=md_file,tpl='detail.html')
                #print(mainview,mainview.md_file,mainview.get_path())
                mainview.set_parent(self)
                mainview.apply_md_file()
            dir_list = sorted([fn for fn in os.listdir(path) if os.path.isdir(os.path.join(path,fn))], key = lambda x: os.stat(os.path.join(path,x)).st_ctime,reverse=True)
            for cate in dir_list:
                cateview = BaseView(cate,tpl='index.html',is_cate=True)
                cateview.set_parent(self)
                cateview.gen_children()

    def get_all_sub_articles(self):
        articles = []
        for child in self.children:
            if not child.is_cate:
                articles.append({'text':child.text,'url':child.url,'date':child.date,'short_md_content':child.short_md_content})
            else:
                articles.extend(child.get_all_sub_articles())
        #print(self,self.children,articles)
        return sorted(articles,key=lambda x: x['date'],reverse=True)

    def gen_site_map(self):
        self.site_map = {'id':self.id, 'text':self.text,'url':self.url,'selected':False,'is_cate':self.is_cate}
        if self.ext_url:
            self.site_map.update({'url':self.ext_url})
        sub_site_map = []
        for child in self.children:
            sub_site_map.append(child.gen_site_map())
        self.site_map.update({'sub':sub_site_map})
        self.update_context({'site_map':self.site_map})
        return self.site_map

    def set_parent(self,view):
        self.parent = view 
        view.children.append(self)
        if self.is_cate:
            self.url = view.url + '/' + self.text 
        else:
            self.url = view.url + '/' + self.text + '.html'

    @classmethod
    def clear(cls):
        id_next = 0
        cls.instances = []

    @classmethod
    def get_by_text(cls,text):
        #print("text=%s; ins_len=%d"%(text,len(cls.instances)))
        for view in cls.instances:
            #print ("view.text=",view.text)
            if view.text.lower() == text.lower():
                return view 
        raise Exception("Instance %s not found"%text)

    def apply_config(self,cate_config):
        if 'order' in cate_config.keys():
            self.order = cate_config['order']

    def set_md_file(self,md_file):
        self.md_file = md_file

    def apply_md_file(self):
        if self.md_file:
            self.md_content,self.short_md_content,title,date = get_md_content(self.get_md_path())
            self.date = date
            self.update_context({'title':title,'short_md_content':self.short_md_content})
            #if not self.out:
            #self.out = os.path.splitext(self.md_file)[0] + '.html'

    def update_context(self,extra_context):
        self.context.update(extra_context)

    def update_plugin_context(self):
        logging.debug("%s update plugin context"%self.text)
        #if self.classname == 'MainView' and self.parent:
        #    self.merge_plugin(self.parent.plugins_context)
        obj = self.parent
        if obj:
            while obj.parent: #do not add index's plugins
                self.merge_plugin(obj.plugins_context)
                obj = obj.parent
        self.update_context({'plugins_context':self.plugins_context})
        if 'sider' in self.plugins_context.keys():
            self.update_context({'has_sider':True})

    def gen_html(self):
        if not self.ext_url:
            logging.debug("%s update_articles %s: %s"%(str(self),self.text,json.dumps(self.context,indent=4,sort_keys=True)))
            self.update_plugin_context()
            logging.debug("gen_html text=%s cate=%s from md file=%s with tpl=%s and context=\n%s\n"%(self.text, self.parent,self.md_file,self.tpl,json.dumps(self.context,indent=4,sort_keys=True)))
            #gen_html(self.tpl,self.md_content,self.context,os.path.join(self.parent.text,self.out))
            self.update_context({'md_content':self.md_content,'short_md_content':self.short_md_content})
            self.update_context(global_context)
            self.update_context({'global_site_map':global_site_map})
            s = render(self.tpl,self.context)
            #print(context_dict)
            f = open(self.get_output_path()+'.html','w')
            f.write(s)
            f.close()
            for view in self.children:
                view.gen_html()

    def merge_plugin(self,plugin_context):
        logging.debug("%s merge plugin %s"%(self.text,json.dumps(plugin_context,indent=4,sort_keys=True)))
        cur_areas = set(self.plugins_context.keys())
        new_areas = set(plugin_context)
        cur_areas.update(new_areas)
        for area in cur_areas:
            if area not in self.plugins_context.keys():
                self.plugins_context.update({area:plugin_context[area]})
            elif area in plugin_context.keys():
                self.plugins_context[area].extend(plugin_context[area])
        logging.debug("%s after merge plugins %s"%(self.text,json.dumps(self.plugins_context,indent=4,sort_keys=True)))
        #self.plugins_context = copy.deepcopy(self.plugins_context)

    def apply_plugin(self,plugin):
        logging.debug("%s before apply plugins = %s"%(self.text,self.plugins_context))
        context_plugin = plugin.apply(self)
        logging.debug("%s after apply plugins = %s"%(self.text,self.plugins_context))
        for area in context_plugin:
            context_plugin[area] = [context_plugin[area]]
        self.merge_plugin(copy.deepcopy(context_plugin))
        if self.text:
            for childview in self.children:
                childview.apply_plugin(plugin)


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

