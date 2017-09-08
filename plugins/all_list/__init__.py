from models import BasePlugin
class Plugin(BasePlugin):
    def apply(self,view):
        context = super(Plugin,self).apply(view)
        #print("inst:",MainView.instances)
        #print("all_list instance:",self.all_articles)
        article_list = view.get_all_sub_articles()
        for area in self.areas:
            context[area]['context'].update({'article_list':article_list})
        return context
