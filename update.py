import os
import datetime

preclude = {'_config.yml', 'update.py', 'CNAME', 'feed.xml', 'index.md'}

HOST = "{{ site.url }}{{ site.baseurl }}/"

ratio = 0.2

files = sorted(
    set(
        filter(
            os.path.isfile, os.listdir('./'))
    ) - preclude,
    reverse=True)

files_for_feed = sorted(files[:int(len(files) * ratio)])


def gen_feed(file_list):
    items = ''
    for f in file_list:
        i = os.path.splitext(f)[0]
        try:
            date = datetime.datetime.strptime(i, '%Y%m%d')
        except ValueError:
            date = datetime.datetime.now()
        items += """
        <item>
            <title>{title}</title>
            <description>{description}</description>
            <pubDate>{{ {date} | date_to_rfc822 }}</pubDate>
            <link>{url}</link>
            <guid>{url}</guid>
        </item>""".format(title=i, description=i, date=date,
                          url='{}{}'.format(HOST, i))
    rss = ("""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{{ site.title | xml_escape }}</title>
    <description>{{ site.description | xml_escape }}</description>
    <link>{{ site.url }}{{ site.baseurl }}/</link>
    <atom:link href="{{ "/feed.xml" | prepend: site.baseurl | prepend: site.url }}" rel="self" type="application/rss+xml"/>
    <pubDate>{{ site.time | date_to_rfc822 }}</pubDate>
    <lastBuildDate>{{ site.time | date_to_rfc822 }}</lastBuildDate>
    <generator>Jokin</generator>
    {item}
  </channel>
</rss>""".format(item=items))
    with open('feed.xml', 'w') as f:
        f.write(rss)


def gen_index(file_list):
    items = ''
    for f in file_list:
        i = os.path.splitext(f)[0]
        items += """[{des}]({url})\n""".format(des=i, url='{}{}'.format(HOST, i))
    index = (
        "# Memo Review Helper  \n"
        "[GitHub](https://github.com/JokinYang/MomoReviewHelper) [RSS]({host}feed.xml)\n"
        "{items}"
            .format(host=HOST, items=items)
    )
    with open('index.md', 'w') as f:
        f.write(index)


gen_feed(files)
gen_index(files)
