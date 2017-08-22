import siteasy
import os
class Plugin:
    def __init__(self):
        self.config = siteasy.loadjson(os.path.join('plugins','list','config.json'))

    def apply(self,view):
        for area in self.config.keys():
            if area not in view.tpl_plugins.keys():
                view.tpl_plugins.update({area:[]})
            view.tpl_plugins[area].append('list'+'/'+self.config[area]['tpl'])
            print(view.text,view.tpl_plugins)

        context = self.config[area]['context']
        article_list = []
        if view.classname == 'CateView':
            for mainview in view.mainviews:
                article_list.append({'url':'/'+view.text+'/'+mainview.text+'.html','text':mainview.text})
            view.context_plugins.update({'article_list':article_list})
