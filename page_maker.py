import datetime
from db_helper import WordDetail
from typing import List
import random


class PageGenerator:
    def __init__(self, words: List[WordDetail], date: datetime.date = None):
        if date:
            self.date = date
            delta = 0
        else:
            self.date = datetime.datetime.now(
                datetime.timezone(datetime.timedelta(hours=8)))
            delta = 1 if self.date.time() < datetime.time(4, 0, 0) else 0

        self.timestamp = '{:%Y%m%d}'.format(self.date.date() - datetime.timedelta(delta))

        self.words = words
        random_int = random.randint(0, 2 ** 16)
        self.interpretation_class = '{}_{}'.format('interpretation', str(random_int))
        self.details_class = '{}_{}'.format('details', str(random_int))

    def gen_md(self, output_path=None):
        output_path = output_path or '{}.md'.format(self.timestamp)
        content = ''.join([self._gen_head(), self._gen_body()])
        style = """<style>
/*不显示details的三角符号*/
details > summary::marker {
    display: none;
    content: none;
}
/*去掉外边框*/
details summary{
    outline:none;
    cursor:pointer;/*鼠标放上去之后变成手型*/
}
/*去掉前面默认的小黑三角*/
details summary::-webkit-details-marker{
    display:none; 
}
</style>
"""
        script = ("""
<script>
const details = document.querySelectorAll('.{d}');
const translates = document.querySelectorAll('.{tr}');
""".format(d=self.details_class, tr=self.interpretation_class) + """
details.forEach((item, index) => item.addEventListener('toggle', () => {
    if (item.open) {
        translates[index].style.display = 'block';
    } else translates[index].style.display = 'none';
}));
</script>\n""")
        content = style + content + script
        with open(output_path, 'w') as f:
            f.write(content)
        return output_path, content

    def _gen_head(self):
        date_str = '{} [{}]'.format(self.timestamp, len(self.words))
        return f"# {date_str}  \n"

    def _gen_body(self):
        items = [self._gen_item_html(i) for i in self.words]

        return '\n'.join(items)

    def _gen_item_html(self, word: WordDetail, highlight_word=True):
        phrase_list = word.phrase_list
        if not phrase_list:
            return f'Not found the phrase of:{word.word}  \n'
        phrase_choose = max(phrase_list, key=lambda x: len(x[0]))
        en, ch = phrase_choose
        en = en.replace(word.word, f'<strong>{word.word}</strong>')
        i = """
<div style="display: flex;align-items: baseline;">
    <h2 style="margin-bottom: 0;margin-top: 0">{word}</h2>
    <p style="padding:0 .5em; margin: 0;font-family: monospace;">{phonetic}</p>
    <p class="{inter_class}" style="display:none ;padding:0 .5em; margin: 0; white-space: nowrap;overflow: hidden;text-overflow: ellipsis;">{interpretation}</p>
</div>
<details class="{detail_class}">
    <summary style="color: #303030;">{en}</summary>
    {ch}
</details>
<hr style="padding-bottom: 0.5em;" />
""".format(word=word.word, en=en, ch=ch,
           phonetic=word.pronunciation, interpretation=word.interpretation,
           inter_class=self.interpretation_class, detail_class=self.details_class)
        return i
