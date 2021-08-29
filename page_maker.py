import datetime
from db_helper import WordDetail
from typing import List


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

    def gen_md(self, output_path=None):
        output_path = output_path or '{}.md'.format(self.timestamp)
        content = ''.join([self._gen_head(), self._gen_body()])
        style = """<style>
/*不显示details的三角符号*/
details > summary::marker {
    display: none;
    content: "";
}
</style>
"""
        content = style + content
        with open(output_path, 'w') as f:
            f.write(content)
        return output_path, content

    def _gen_head(self):
        date_str = '{} [{}]'.format(self.timestamp, len(self.words))
        return f"# {date_str}  \n"

    def _gen_body(self):
        items = [self._gen_item_html(i) for i in self.words]

        return '\n'.join(items)

    def _gen_item(self, word: WordDetail, highlight_word=True):
        phrase_list = word.phrase_list
        if not phrase_list:
            return f'Not found the phrase of:{word.word}\n'
        phrase_choose = max(phrase_list, key=lambda x: len(x[0]))
        en, zh = phrase_choose
        en = en.replace(word.word, f' **{word.word}** ')
        return f'{en}  \n'

    def _gen_item_html(self, word: WordDetail, highlight_word=True):
        phrase_list = word.phrase_list
        if not phrase_list:
            return f'Not found the phrase of:{word.word}  \n'
        phrase_choose = max(phrase_list, key=lambda x: len(x[0]))
        en, ch = phrase_choose
        en = en.replace(word.word, f'<strong>{word.word}</strong>')
        i = """
<div><h2 style="display: inline-block;margin-bottom: 0;margin-top: 0">{word}</h2>
    <p style="display: inline-block; padding:0 .5em; margin: 0;">{phonetic}</p></div>
<details>
    <summary style="color: #303030;">{en}</summary>
    {ch}
</details>
<hr style="padding-bottom: 0.5em;" />
""".format(phonetic=word.pronunciation,
           word=word.word, en=en, ch=ch)
        return i
