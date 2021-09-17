#! /bin/env python3
import argparse
import datetime
import os

des = "A tool for querying words info form maimemo(墨墨背单词) and " \
      "generating a list of words learned today for review"

version = "0.0.1"

parser = argparse.ArgumentParser(description=des,
                                 prog='MemoReviewHelper')

parser.add_argument('-v', action='version', version='%(prog)s {}'.format(version))
parser.add_argument('action', choices=['claw', 'gen'])

gen_review = parser.add_argument_group('gen', 'Gen the list for review')
gen_review.add_argument('-u', '--account', metavar='ACCOUNT',
                        default=os.getenv('ACCOUNT'),
                        help='maimemo account.'
                             'if not given will get the the value of ACCOUNT for env')
gen_review.add_argument('-p', '--password', metavar='PASSWORD',
                        default=os.getenv('PASSWORD'),
                        help='maimemo password.'
                             'if not given will get the the value of PASSWORD for env')
gen_review.add_argument('-d', '--date', metavar='DATE', nargs='?', type=str,
                        default="{:%Y%m%d}".format(datetime.date.today()),
                        const="{:%Y%m%d}".format(datetime.date.today()),
                        help='the learn date of the words to gen. '
                             'the date must format as YYYYMMDD; '
                             'a date range is available,such as: 20210113 20210127. '
                             'If nothing given, today`s date will be used.')
gen_review.add_argument('-o', '--out-dir', metavar='OUTPUT_DIR',
                        default=os.path.abspath('.'),
                        help='the directory to store the review files.'
                             'default use current dir.')
gen_review.add_argument('--ignore-missing', action='store_true', default=True,
                        help="ignore the words do not in database.sqlite ")
gen_review.add_argument('--timeout', type=int,
                        help='the time limitation for the script running')

args = parser.parse_args()
print(str(args))
