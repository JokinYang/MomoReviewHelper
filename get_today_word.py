import datetime
import time
from db_helper import query_words, transfer_to_word_obj
from page_maker import PageGenerator
import sys
import uiautomator2 as u2
import os

PACKAGE = 'com.maimemo.android.momo'


class ID:
	class _Inner:
		def find_element_by_id(self, x):
			return x

		def find_element_by_accessibility_id(self, x):
			return x

		def click(self, *x):
			pass

		def send_keys(self, *x):
			pass

	driver = _Inner()

	# agree
	tv_agree = driver.find_element_by_id("com.maimemo.android.momo:id/tv_agree")
	# 其他方式登录
	login_other_ways_btn = driver.find_element_by_id("com.maimemo.android.momo:id/login_other_ways_btn")
	# 输入账号
	identity_management_account_et = driver.find_element_by_id(
		"com.maimemo.android.momo:id/identity_management_account_et")
	# el4.send_keys("")
	# 输入密码
	identity_management_pwd_et = driver.find_element_by_id("com.maimemo.android.momo:id/identity_management_pwd_et")
	# el5.send_keys("")
	# 同意协议
	identity_management_terms_cb = driver.find_element_by_id("com.maimemo.android.momo:id/identity_management_terms_cb")
	# el6.click()
	# 登录
	identity_management_confirm_btn = driver.find_element_by_id(
		"com.maimemo.android.momo:id/identity_management_confirm_btn")
	# el7.click()

	# download backup
	setting_text = driver.find_element_by_accessibility_id("设置")
	# el8.click()
	backup_and_restore_text = driver.find_element_by_accessibility_id("备份与还原")
	# el9.click()
	tv_activity_backup_revert_study = driver.find_element_by_id(
		"com.maimemo.android.momo:id/tv_activity_backup_revert_study")
	# el10.click()
	ok_button = driver.find_element_by_id("android:id/button1")

	main_page_container = driver.find_element_by_id('com.maimemo.android.momo:id/mainact_viewpager')

d = u2.connect()

def main():
	TIMEOUT = 5
	ACCOUNT = os.environ.get('ACCOUNT', None)
	PASSWORD = os.environ.get('PASSWORD', None)
	print(ACCOUNT)

	# d = u2.connect()  # connect to device

	# d._adb_shell(['root'])
	# d.app_clear(PACKAGE)
	d.app_stop(PACKAGE)
	d.app_start(PACKAGE, use_monkey=True)
	
	try:
		print('Click tv agree(if exists)')
		d(resourceId=ID.tv_agree).click_exists(TIMEOUT)
	except u2.exceptions.UiObjectNotFoundError as e:
		print(e)
	print('Login other way')
	d(resourceId=ID.login_other_ways_btn).click(timeout=20)
	# Start input account and password
	print('Agree treaty')
	d(resourceId=ID.identity_management_terms_cb).click(TIMEOUT)
	print('Input account')
	d(resourceId=ID.identity_management_account_et).set_text(ACCOUNT)
	print('Input password')
	d(resourceId=ID.identity_management_pwd_et).set_text(PASSWORD)
	print('Click login button')
	d(resourceId=ID.identity_management_confirm_btn).click(TIMEOUT)
	# Check login status
	if not d(resourceId=ID.main_page_container).exists(20):
		n = 'main_page_not_found'
		hierarchy = d.dump_hierarchy()
		with open(f'{n}.xml', 'w') as f:
			f.write(hierarchy)
		d.screenshot(f'{n}.jpg')
		os.system(f'curl --upload-file ./{n}.jpg http://transfer.sh/{n}.jpg')
		os.system(f'curl --upload-file ./{n}.xml http://transfer.sh/{n}.xml')
		print('Can not find main page')
		return None

	print('Go to setting')
	d(text=ID.setting_text).click(TIMEOUT)
	print('Go to back up and restore setting')
	d(text=ID.backup_and_restore_text).click(TIMEOUT)
	print('Download backup')
	d(resourceId=ID.tv_activity_backup_revert_study).click(TIMEOUT)
	print('Asure download')
	d(resourceId=ID.ok_button).click_exists(TIMEOUT)
	if d(text=' 还原成功！ ').exists(timeout=20):
		print('It is ok !!!')
	else:
		print('May not success')

	c = ['adb', 'pull', '/data/data/com.maimemo.android.momo/databases/maimemo.v3_8_51.db', './']
	os.system('adb root;sleep 5')
	os.system(' '.join(c))

	db_path = os.path.join('./', 'maimemo.v3_8_51.db')
	print(f'dbpath:{db_path}')
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
	try:
		main()
	except u2.exceptions.UiObjectNotFoundError as e:
		screenshot = 's.jpg'
		d.screenshot(screenshot)
		os.system(f'curl --upload-file ./{screenshot} http://transfer.sh/{screenshot}')
		# curl --upload-file ./hello.txt http://transfer.sh/hello.txt