import json
import os
import re
from dataclasses import dataclass, field
from logging import getLogger

from airtest.core.api import connect_device
from poco.drivers.android.uiautomation import AndroidUiautomationPoco
from poco.proxy import UIObjectProxy
from sqlalchemy.orm.session import Session as Session_type

from db_helper import Session, Word

connect_device('Android:///192.168.59.158:5555')
poco = AndroidUiautomationPoco()
poco.device.wake()

ACCOUNT = os.environ.get('ACCOUNT', None)
PASSWORD = os.environ.get('PASSWORD', None)

getLogger('airtest.core.android.adb').setLevel('ERROR')


@dataclass(init=True)
class WordDetail:
    word: str = field(default=None)
    book: str = field(default=None)
    pron_official_avatar: str = field(default=None)
    pronunciation: str = field(default=None)
    interpretation: str = field(default=None)
    ranking: str = field(default=None)
    study_user_count: str = field(default=None)
    difficulty: str = field(default=None)
    acknowledge_rate: str = field(default=None)
    note_type: str = field(default=None)
    note_content: str = field(default=None)
    phrase: str = field(default=None)  # json

    phrase_list = property(lambda self: json.loads(self.phrase or '[]'))


class Momo:

    def __init__(self, poco: AndroidUiautomationPoco, timeout=5):
        self.poco = poco
        self.timeout = timeout

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
        self.__goto_other_way_login_page()
        self.__other_way_login(account, password)

    def __agree_treaty(self):
        self.tv_agree.wait(self.timeout)
        if self.tv_agree.exists():
            return self.tv_agree.click()

    def __goto_other_way_login_page(self):
        self.login_other_way_button.wait(self.timeout)
        if self.login_other_way_button.exists():
            return self.login_other_way_button.click()

    def __other_way_login(self, account, password, timeout=10):
        self.__goto_other_way_login_page()
        # check the page
        self.login_other_way_page_submit_button.wait(self.timeout)
        if not self.login_other_way_page_submit_button.exists():
            return False
        self.login_other_way_page_account.set_text(str(account))
        self.login_other_way_page_password.set_text(str(password))
        if not self.login_other_way_page_term_cb.attr('checked'):
            self.login_other_way_page_term_cb.click()
        self.login_other_way_page_submit_button.click()

        # check error
        self.login_other_way_page_error_hint.wait(timeout=timeout)
        if self.login_other_way_page_error_hint.exists():
            return self.login_other_way_page_error_hint.get_text()

        self.main_page_container.wait(timeout=timeout)
        return self.main_page_container.exists()

    def launch(self):
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
                        session.commit()
                        self.back()

                        count += 1
                    session.flush()
                    check_effective = bool(count % 50 == 1)
                    if not self.swipe(direction='up', distance=0.75, check_effective=check_effective):
                        print('Swipe to bottom, will exit the work loop.')
                        break
                except Exception as e:
                    print(e)

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

    last_book_btn: UIObjectProxy = property(lambda self: self.poco('com.maimemo.android.momo:id/selbk_tv_last_book'))


momo = Momo(poco)

momo.launch()
# momo.login_with_account(ACCOUNT, PASSWORD)
# momo.goto_wordActivity()
# momo.parse_word_detail()
# start direct in  android shell
# su
# setprop service.adb.tcp.port 5555
# stop adbd
# start adbd

# Start from abd
# adb tcpip 5555
# adb connect 192.168.0.101:5555
