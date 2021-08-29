import os
import re
import sys
from xml.sax import saxutils
from email.utils import format_datetime
import datetime

preclude = {'_config.yml', 'update.py', 'CNAME', 'feed.xml', 'index.md'}

HOST = "{{ site.url }}{{ site.baseurl }}/"

ratio = 0.3

files = sorted(
    set(
        filter(
            lambda x: os.path.isfile(x) and os.path.splitext(x.lower())[1] == '.md',
            os.listdir('./'))
    ) - preclude,
    reverse=True)

files_for_feed = sorted(files[:int(len(files) * ratio)])


def gen_des_for_feed(md_file):
    if not os.path.exists(md_file):
        return 'Can not find file:{}'.format(md_file)
    with open(md_file, 'r') as f:
        md_content = f.read()
    pieces = re.findall(r'<summary+(?:\s+[a-zA-Z]+=".*")*>(.*)</summary+(?:\s+[a-zA-Z]+=".*")*>', md_content)
    return '\n'.join(map(lambda x: '<p>{}</p>'.format(x), pieces))


def gen_feed(file_list):
    items = ''
    for f in file_list:
        des = gen_des_for_feed(f)
        i = os.path.splitext(f)[0]
        try:
            date = datetime.datetime.strptime(i, '%Y%m%d')
        except ValueError:
            date = datetime.datetime.now()
        date = format_datetime(date)
        items += """
        <item>
            <title>{title}</title>
            <description>{description}</description>
            <pubDate>{date}</pubDate>
            <link>{url}</link>
            <guid>{url}</guid>
        </item>""".format(title=saxutils.escape(i), description=saxutils.escape(des), date=date,
                          url='{}{}'.format(HOST, i))
    rss = ("""---
layout: none
---
 
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>墨墨复习助手</title>
        <description>a feed help remember words</description>
        <link>{HOST}</link>
        {item}
    </channel>
</rss>""".format(item=items, HOST=HOST))
    with open('feed.xml', 'w') as f:
        f.write(rss)


def gen_index(file_list):
    items = ''
    for f in file_list:
        i = os.path.splitext(f)[0]
        items += """[{des}]({url})  \n""".format(des=i, url='{}{}'.format(HOST, i))
    index = (
        "[GitHub](https://github.com/JokinYang/MomoReviewHelper) [RSS]({host}feed.xml)  \n"
        "{items}"
            .format(host=HOST, items=items)
    )
    with open('index.md', 'w') as f:
        f.write(index)


gen_feed(files)
print('Updated feed.xml')
gen_index(files)
print('Updated index.html')
