from settings import global_config,env
import re
import json
import time
import os
from collections import OrderedDict
from dateutil import parser

def loadjson(fn,ordered_dict = True):
    f = open(fn)
    c = json.loads(f.read(),object_pairs_hook=OrderedDict)
    f.close()
    return c

def render(tpl,context):
    t = env.get_template(tpl) 
    return t.render(context)

def get_md_content(md_path):
    #print("md_file=%s"%md_path)
    f = open(md_path)
    lines = f.readlines()
    s = ''.join(lines)
    short_content = ''.join(lines[:10])
    p = r'\{[^}]*\}'
    m = re.search(p,s)
    if m:
        head = m.group(0)
        head_dict = json.loads(head)
        date = parser.parse(head_dict['date'])
        content = s.replace(head,'')
        if global_config['add_date']:
            content += "\n---\n %s"%date
        title = head_dict['title']
    else:
        date = time.ctime(os.stat(md_path).st_ctime)
        m = re.search(r'#(.+)',s)
        if m:
            title = re.search(r'#(.+)',s).group(1)
        else:
            title = ""
        if global_config['add_date'] and os.path.splitext(md_path)[0][-5:] != 'index':
            content = s + "\n %s"%date
        else:
            content = s
    f.close()
    return content,short_content,title,date

