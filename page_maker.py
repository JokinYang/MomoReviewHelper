import datetime
from db_helper import WordDetail
from typing import List


class PageGenerator:
	def __init__(self, words: List[WordDetail], date: datetime.date = None):
		self.date = date or datetime.datetime.now(
			datetime.timezone(datetime.timedelta(hours=8)))
		self.words = words

	def gen_md(self, output_path=None):
		delta = 1 if self.date.time() < datetime.time(4, 0, 0) else 0
		timestamp = '{:%Y%m%d}'.format(self.date.today() - datetime.timedelta(delta))
		output_path = output_path or '{}.md'.format(timestamp)
		content = ''.join([self._gen_head(), self._gen_body()])
		with open(output_path, 'w') as f:
			f.write(content)
		return output_path, content

	def _gen_head(self):
		date_str = '{:%Y/%m/%d} [{}]'.format(self.date, len(self.words))
		return f"# {date_str}  \n"

	def _gen_body(self):
		items = [self._gen_item(i) for i in self.words]

		return '\n'.join(items)

	def _gen_item(self, word: WordDetail, highlight_word=True):
		phrase_list = word.phrase_list
		if not phrase_list:
			return f'Not found the phrase of:{word.word}\n'
		phrase_choose = max(phrase_list, key=lambda x: len(x[0]))
		en, zh = phrase_choose
		en = en.replace(word.word, f' **{word.word}** ')
		return f'{en}  \n'
