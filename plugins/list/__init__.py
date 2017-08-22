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
        context = self.config[cateview['text']]['context']
        article_list = [] #for plugins which show list of articles
        for mainview in view.mainviews:
            article_list.append({'url':'/'+cateview.text+'/'+fn+'.html','text':fn})
        context.update({"article_list":article_list})
        view.update_extra_context(context)
