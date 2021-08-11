import json
import os
import re
import sys
from logging import getLogger
from typing import List, Union

from airtest.core.api import connect_device
from poco.drivers.android.uiautomation import AndroidUiautomationPoco
from poco.proxy import UIObjectProxy
from sqlalchemy.orm.session import Session as Session_type

from db_helper import Session, Word, query_words, transfer_to_word_obj, WordDetail
from page_maker import PageGenerator

getLogger('airtest.core.android.adb').setLevel('DEBUG')


def get_local_adb_path():
	r = os.popen('which adb', 'r')
	return r.read().strip()


def monkey_patch_for_airtest():
	import platform
	from copy import copy
	from airtest.core.android import constant
	from airtest.core.android.adb import ADB
	# use host adb for airtest to avoid the device offline error
	system = platform.system()
	machine = platform.machine()
	constant.DEFAULT_ADB_PATH['{}-{}'.format(system, machine)] = get_local_adb_path()

	def _cleanup_forwards(self):
		"""
		Remove the local forward ports
		Returns:
			None
		"""
		# remove forward成功后，会改变self._forward_local_using的内容，因此需要copy一遍
		# After remove_forward() is successful, self._forward_local_using will be changed, so it needs to be copied
		forward_local_list = copy(self._forward_local_using)
		for local in forward_local_list:
			self.remove_forward(local)

	ADB._cleanup_forwards = lambda self: None  # do nothing for clean forwards


monkey_patch_for_airtest()


class Momo:

	def __init__(self, poco: AndroidUiautomationPoco, timeout=5):
		self.poco = poco
		self.timeout = timeout
		self.poco.adb_client.cmd('root')

	def ensure_app(self, apk_path, reinstall=False):
		# https://cdn.maimemo.com/apk/maimemo_v3.8.56_1617086292.apk
		if not self.poco.adb_client.check_app(self.package_name) or reinstall:
			self.poco.adb_client.install_app(apk_path, replace=True, install_options=['-g'])

	def login_with_account(self, account, password, force_login=False):
		if not force_login:
			self.launch()
			self.main_page_container.wait(self.timeout)
			if self.main_page_container.exists():
				return True
		self.clear_cache()
		self.launch()
		self.__agree_treaty()
		# self.__goto_other_way_login_page()
		return self.__other_way_login(account, password)

	def __agree_treaty(self):
		self.tv_agree.wait(self.timeout)
		if self.tv_agree.exists():
			print('tv agree')
			return self.tv_agree.click()

	def __goto_other_way_login_page(self):
		self.login_other_way_button.wait(self.timeout)
		if self.login_other_way_button.exists():
			print('click login other way')
			return self.login_other_way_button.click()

	def __other_way_login(self, account, password, timeout=10):
		self.__goto_other_way_login_page()
		# check the page
		self.login_other_way_page_submit_button.wait(self.timeout)
		if not self.login_other_way_page_submit_button.exists():
			return False
		print('Login other way page exists')
		self.login_other_way_page_account.set_text(str(account))
		self.login_other_way_page_password.set_text(str(password))
		if not self.login_other_way_page_term_cb.attr('checked'):
			self.login_other_way_page_term_cb.click()
		self.login_other_way_page_submit_button.click()

		# check error
		self.login_other_way_page_error_hint.wait(timeout=timeout)
		if self.login_other_way_page_error_hint.exists():
			return self.login_other_way_page_error_hint.get_text()

		self.main_page_container.wait(timeout=timeout + 5)
		return self.main_page_container.exists()

	def launch(self, relaunch=True):
		if relaunch:
			self.poco.adb_client.stop_app(self.package_name)
		self.poco.adb_client.start_app(self.package_name)

	def is_login(self):
		self.main_page_container.wait(self.timeout)
		return self.main_page_container.exists()

	def is_word_detail_activity(self):
		world_detail_activity = ('com.maimemo.android.momo', '.word.WordDetailActivity', 'pid')
		return self.poco.adb_client.get_top_activity()[:-1] == world_detail_activity[:-1]

	def parse_word_detail(self):
		# self.poco.agent.hierarchy.dump()
		self.poco('com.maimemo.android.momo:id/activity_word_detail_content').wait(self.timeout)
		if not self.is_word_detail_activity():
			return False

		detail = {
			'word': 'android.widget.TextView',  # 单词
			'pron_official_avatar': 'com.maimemo.android.momo:id/pron_official_avatar',  # 美式or英式
			'pronunciation': 'com.maimemo.android.momo:id/pronunciation',  # 音标
			'interpretation': 'com.maimemo.android.momo:id/interpretation',  # 释义
			'ranking': 'com.maimemo.android.momo:id/ranking',  # 词频排名
			'study_user_count': 'com.maimemo.android.momo:id/study_user_count',  # 学习人数
			'difficulty': 'com.maimemo.android.momo:id/difficulty',  # 难度
			'acknowledge_rate': 'com.maimemo.android.momo:id/acknowledge_rate',  # 认知比率
			'note_type': 'com.maimemo.android.momo:id/note_type',  # 注记类型
			'note_content': 'com.maimemo.android.momo:id/noteTextView',  # 注记内容
		}
		detail_content = {}
		for k, v in detail.items():
			detail_content[k] = self.poco(v).get_text()

		phrase = self.poco('com.maimemo.android.momo:id/word_detail_phrases_ll')
		phrase_list = []
		for i in phrase.children():
			eng, ch, *_ = i.children().children()
			phrase_list.append((eng.get_text(), ch.get_text()))
		detail_content['phrase'] = json.dumps(phrase_list)
		return WordDetail(**detail_content)

	def parse_word_book(self, category=None, book_name=None):
		# com.maimemo.android.momo:id/selbk_last_book_btn
		current_book: UIObjectProxy = None
		word_book_title = self.poco('com.maimemo.android.momo:id/toolbar_word_list_title_tv')
		if category and book_name:
			pass
		# 如果没有输入category和book_name则取默认图书为上次使用的图书
		elif (not category) and (not book_name):
			current_book = self.last_book_btn
		# 如果当前显示的单词书名称与所需解析的相同
		elif book_name and word_book_title.exists():
			book_name_find = word_book_title.get_text()
			if re.match('.*' + re.escape(book_name) + '.*', book_name_find):
				current_book = self.poco(book_name_find)
		elif False:
			pass
		if not self.main_page_container.exists():
			self.stop()
			self.launch()
			self.main_page_container.wait(self.timeout)
			assert self.main_page_container.exists(), 'Could not find the main page container,you may not login.'
		self.mp_choose_word.wait(self.timeout)
		self.mp_choose_word.click()
		current_book: UIObjectProxy = self.last_book_btn
		# swipe to the top
		for i in range(20):
			if not self.swipe('down', check_effective=True) or current_book.exists():
				break
		else:
			print('The screen may not swipe to the top.')
		assert current_book.exists(), 'Can not find last book btn'
		book_name = current_book.get_text()
		current_book.click()
		# Get the info of the book
		total_button = self.poco('com.maimemo.android.momo:id/selwordact_tv_tab3_num')
		total_button.click()
		total_count = total_button.get_text()

		# Main loop to extract word info
		list_view = self.poco('android.widget.ListView')
		# session = get_session()
		count = 1
		with Session.begin() as session:
			session: Session_type
			while True:
				try:
					word_list = list_view.offspring('com.maimemo.android.momo:id/tv_item_list_select_word_content')
					for i in word_list:
						word = i.get_text()
						print(f'({count}/{total_count}) Getting the info of word:<{word}>')
						if session.query(Word.word).filter_by(word=word).all():
							print(f'Found the info of word<{word}> in db,skip it')
							continue
						# Enter WordDetail Activity
						i.click()
						word_detail = self.parse_word_detail()
						if not word_detail:
							print(f"Meet some trouble while parse:<{word}> ,skipped")
							print('word_detail:\n', word_detail)
							continue
						word_detail.book = book_name
						print(f'\t add:<{word}> to database')
						session.add(Word(**word_detail.__dict__))
						# session.commit()
						self.back()

						count += 1
					# session.flush()
					check_effective = bool(count % 50 == 1)
					if not self.swipe(direction='up', distance=0.75, check_effective=check_effective):
						print('Swipe to bottom, will exit the work loop.')
						break
				except Exception as e:
					print(e)

	def download_backup(self):
		if not self.main_page_container.exists():
			self.stop()
			self.launch()
			self.main_page_container.wait(self.timeout)
			assert self.main_page_container.exists(), 'Could not find the main page container,you may not login.'

		path_to_download = [self.mp_setting, self.sp_backup_and_restore, self.sp_bp_download_backup, self.ok_button,
							self.ok_button]
		self.walk_in_path(path_to_download)

	@staticmethod
	def walk_in_path(paths: Union[List[UIObjectProxy], UIObjectProxy], timeout=10):
		if not isinstance(paths, list):
			paths = [paths]
		for i in paths:
			i.wait(timeout)
			if i.exists():
				i.click()
			else:
				raise Exception(f'{i.get_name()} not exists')

	def pull_db(self, local=None):
		# /data/data/com.maimemo.android.momo/databases/maimemo.v3_8_51.db
		self.download_backup()
		db_dir = "/data/data/com.maimemo.android.momo/databases/"
		db_name_cmd = f'ls {db_dir} | grep maimemo.v'
		db_name = self.poco.adb_client.shell(db_name_cmd).strip()
		db_path = f'{db_dir.strip()}{db_name}'
		local_path = local or './'
		self.poco.adb_client.pull(db_path, local_path)
		return os.path.join(local_path, db_name)

	def dump_screen(self):
		return self.poco.agent.hierarchy.dump()

	def swipe(self, direction, distance=0.3, check_effective=False):
		"""

		:param check_effective: Whether check the swipe is effective
		:param direction:
		:param distance:
		:return: True means swipe operation makes the screen changed.
				False means hit the top or bottom the screen, the swipe do not change the state of the screen.
		"""
		direction = str(direction)
		before = (not check_effective) or self.dump_screen()

		if direction == 'up':
			d = [0, -distance]
		elif direction == 'down':
			d = [0, distance]
		elif direction == 'left':
			d = [-distance, 0]
		elif direction == 'right':
			d = [distance, 0]
		else:
			raise ValueError(f'Unknown value of direction:{direction}')

		self.poco.swipe([0.5, 0.5], direction=d, duration=0.1)
		after = (not check_effective) or self.dump_screen()
		return (not check_effective) or (not before == after)

	def swipe4find(self, ui):
		pass

	def back(self):
		self.poco.adb_client.keyevent('BACK')
		self.poco.wait_stable()

	def stop(self):
		self.poco.adb_client.stop_app(self.package_name)

	def clear_cache(self):
		self.poco.adb_client.clear_app(self.package_name)

	package_name: UIObjectProxy = property(lambda self: 'com.maimemo.android.momo')
	# treaty page
	tv_agree: UIObjectProxy = property(lambda self: self.poco('com.maimemo.android.momo:id/tv_agree'))
	tv_not_agree: UIObjectProxy = property(lambda self: self.poco('com.maimemo.android.momo:id/tv_not_agree'))
	# login page
	wechat_login_button: UIObjectProxy = property(lambda self: self.poco('com.maimemo.android.momo:id/login_btn'))
	wechat_login_terms_cb: UIObjectProxy = property(
		lambda self: self.poco('com.maimemo.android.momo:id/login_terms_cb'))

	login_other_way_button: UIObjectProxy = property(
		lambda self: self.poco('com.maimemo.android.momo:id/login_other_ways_btn'))
	# other way login page
	login_other_way_page_account: UIObjectProxy = property(
		lambda self: self.poco('com.maimemo.android.momo:id/identity_management_account_et'))
	login_other_way_page_password: UIObjectProxy = property(
		lambda self: self.poco('com.maimemo.android.momo:id/identity_management_pwd_et'))
	login_other_way_page_submit_button: UIObjectProxy = property(lambda self: self.poco(
		'com.maimemo.android.momo:id/identity_management_confirm_btn'))
	login_other_way_page_term_cb: UIObjectProxy = property(
		lambda self: self.poco('com.maimemo.android.momo:id/identity_management_terms_cb'))
	login_other_way_page_error_hint: UIObjectProxy = property(
		lambda self: self.poco('com.maimemo.android.momo:id/identity_management_error_hint_tv'))
	# main page
	main_page_container: UIObjectProxy = property(
		lambda self: self.poco('com.maimemo.android.momo:id/mainact_viewpager'))
	mp_choose_word: UIObjectProxy = property(lambda self: self.poco('选词'))
	mp_review: UIObjectProxy = property(lambda self: self.poco('复习'))
	mp_statistics: UIObjectProxy = property(lambda self: self.poco('统计'))
	mp_setting: UIObjectProxy = property(lambda self: self.poco('设置'))
	# setting page
	sp_backup_and_restore: UIObjectProxy = property(lambda self: self.poco('com.maimemo.android.momo:id/backup_ctn'))
	sp_bp_download_backup: UIObjectProxy = property(
		lambda self: self.poco('com.maimemo.android.momo:id/tv_activity_backup_revert_study'))
	# sp_bp_download_backup: UIObjectProxy = property(lambda self: self.poco('下载还原最近数据'))

	ok_button: UIObjectProxy = property(lambda self: self.poco(text='确定'))

	last_book_btn: UIObjectProxy = property(lambda self: self.poco('com.maimemo.android.momo:id/selbk_tv_last_book'))


def restart_adb(func):
	i = 0

	def wrapper():
		nonlocal i
		while i < 3:
			try:
				func()
			except Exception as e:
				os.system('echo "kill server";adb kill-server;sleep 2')
				os.system('echo "start server";adb start-server;sleep 2')
				os.system('echo "list devices";adb devices')
				i += 1
				print(e)
				continue
			return

	return wrapper


@restart_adb
def main():
	ACCOUNT = os.environ.get('ACCOUNT', None)
	PASSWORD = os.environ.get('PASSWORD', None)
	# connect_device('Android:///192.168.0.108:5555')
	connect_device('Android:///')
	poco = AndroidUiautomationPoco()
	poco.device.wake()

	momo = Momo(poco)
	momo.launch(relaunch=False)
	print('Try to login')
	print(momo.login_with_account(ACCOUNT, PASSWORD))

	if not momo.is_login():
		print('Your account seem not login, please check your account & password!')
		raise Expection()

	print("Start pull db")
	db_path = momo.pull_db()
	print(f'Using db:{db_path}')
	today_words = query_words(db_path)
	if not today_words:
		print('Could not find words learn today.')
		sys.exit(0)
	print(f'Find {len(today_words or [])} word learn today')
	print(today_words)
	word_obj = transfer_to_word_obj(today_words)
	print(f'Find {len(word_obj or [])} in database')

	p = PageGenerator(word_obj)
	md_path, _ = p.gen_md()
	print(f'Gen markdown file:{md_path}')


if __name__ == '__main__':
	main()
