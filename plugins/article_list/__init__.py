from siteasy import BasePlugin
class Plugin(BasePlugin):
    def apply(self,view):
        context = super(Plugin,self).apply(view)
        if view.classname == 'CateView':
            if len(view.mainviews) == 0:
                return {}
            MainView = view.mainviews[0].__class__
            article_list = []
            if view.order:
                order_articles = [a.lower() for a in view.order]
                for arti in order_articles:
                    mainview = MainView.get_by_text(arti)
                    article_list.append({'url':'/'+view.text+'/'+mainview.text+'.html','text':mainview.text})
                for mainview in view.mainviews:
                    if mainview.text.lower() not in order_articles:
                        article_list.append({'url':'/'+view.text+'/'+mainview.text+'.html','text':mainview.text})
            else:
                mainview_list = sorted(view.mainviews, key=lambda k : k.date)
                article_list = [{'url':'/'+view.text+'/'+mainview.text+'.html','text':mainview.text} for mainview in mainviews]
        context['sider']['context'].update({'article_list':article_list})
        return context
