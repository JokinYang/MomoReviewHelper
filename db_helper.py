import datetime
import json
import sqlite3
from dataclasses import dataclass, field
from itertools import chain
from typing import List
from contextlib import contextmanager

from sqlalchemy import Column, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session as Session_type

Base = declarative_base()

engine = create_engine('sqlite:///database.sqlite')


class Word(Base):
    __tablename__ = 'word'
    word = Column(String(), primary_key=True)
    book = Column(String())
    pron_official_avatar = Column(String())
    pronunciation = Column(String())
    interpretation = Column(String())
    ranking = Column(String())
    study_user_count = Column(String())
    difficulty = Column(String())
    acknowledge_rate = Column(String())
    note_type = Column(String())
    note_content = Column(String())
    phrase = Column(String())  # 单词短语（句子）


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


def trans_Word_to_wordDetail(word: Word) -> WordDetail:
    word_dict = word.__dict__
    word_dict.pop('_sa_instance_state')
    return WordDetail(**word_dict)


Base.metadata.create_all(engine, checkfirst=True)

Session = sessionmaker(bind=engine, autocommit=True, autoflush=True)


@contextmanager
def session_maker(session=Session):
    try:
        s = session()
        yield s
        s.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def query_words(db_path, date=None):
    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        if isinstance(date, str):
            date_str = '{}000000'.format(date)
        elif isinstance(date, datetime.date):
            date_str = '{:%Y%m%d000000}'.format(date)
        else:
            date_str = '{:%Y%m%d000000}'.format(datetime.date.today())
        query_words_id_sql = (
                "SELECT ssr_new_vocs_today_familiar,"
                "ssr_new_vocs_today_forget,"
                "ssr_new_vocs_today_uncertain,"
                "ssr_new_vocs_today_well_familiar "
                "FROM SSR_TB "
                "WHERE ssr_date == %s;" % date_str)

        cursor.execute(query_words_id_sql)
        r = cursor.fetchone()
        if not r: return False
        word_ids = chain(*filter(lambda x: x, map(lambda x: json.loads(x), r)))

        query_words_sql = "SELECT vc_vocabulary FROM VOC_TB WHERE vc_id IN  %s ;" % str(tuple(word_ids))
        cursor.execute(query_words_sql)
        words = cursor.fetchall()
        if not words: return False
        word_list = list(map(lambda x: x[0], words))
        cursor.close()

        return word_list


def transfer_to_word_obj(words: List) -> List[WordDetail]:
    if not words: return False
    with Session.begin() as s:
        s: Session_type
        word_objs = s.query(Word).filter(Word.word.in_(words)).all()
        return list(map(trans_Word_to_wordDetail, word_objs))
