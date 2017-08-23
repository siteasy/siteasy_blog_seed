from siteasy import BasePlugin
class Plugin(BasePlugin):
    def apply(self,view):
        context = super(Plugin,self).apply(view)
        if view.classname == 'CateView':
            article_list = []
            for mainview in view.mainviews:
                article_list.append({'url':'/'+view.text+'/'+mainview.text+'.html','text':mainview.text})
            context['sider']['context'].update({'article_list':article_list})
        return context
