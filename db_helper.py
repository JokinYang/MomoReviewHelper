from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import sessionmaker, session
from sqlalchemy.ext.declarative import declarative_base

import sqlite3

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
	phrase = Column(String())


Base.metadata.create_all(engine, checkfirst=True)

Session = sessionmaker(bind=engine, autocommit=True, autoflush=True)


def query_words(db_path):
	with sqlite3.connect(db_path) as db:
		cursor = db.cursor()
		cursor.execute('')

		cursor.fetchall()

		cursor.close()
