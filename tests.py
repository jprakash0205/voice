#!venv\Scripts\python
from coverage import coverage
cov = coverage(branch=True, omit=['venv/*', 'tests.py'])
cov.start()

import os
import unittest
from analytics import PageView, JAVASCRIPT, DOMAIN, app
from flask import url_for
from peewee import *

basedir = os.path.abspath(os.path.dirname(__file__))
APP_DIR = os.path.dirname(__file__)
#DATABASE_NAME = os.path.join(APP_DIR, 'analytics-test.db')
database = SqliteDatabase(os.path.join(APP_DIR, 'analytics-test.db'))

class BasicTestCase(unittest.TestCase):

	def setUp(self):
		database.create_tables([PageView], safe=True)
	
	def tearDown(self):
		#database.drop_tables([PageView], safe=True)
		pass

	def test_db_url(self):
		self.assertTrue(isinstance(database, SqliteDatabase))

	def test_pageview_insert(self):
		dmn = 'www.test.com'
		turl = 'http://www.test.com'
		PageView.create(
            domain=dmn,
            url=turl,
            headers='',
            params=''
            )
		self.assertTrue(PageView.select().count() > 0)

	def test_pageview_select(self):
		dmn = 'example.com'
		turl = 'http://www.test.com'
		PageView.create(
            domain=dmn,
            url=turl,
            title='index',
            ip='127.0.0.1',
            headers='',
            params=''
            )
		self.assertTrue(PageView.select(PageView.title).where(PageView.title=='index').count() > 0)	
		self.assertFalse(PageView.select(PageView.ip).where((PageView.ip=='0.0.0.9') & (PageView.title=='index')).count() > 0)

	def test_config(self):
		self.assertFalse(JAVASCRIPT == '')
		self.assertTrue(DOMAIN != '')

if __name__ == '__main__':
    try:
        unittest.main()
    except:
        pass
    cov.stop()
    cov.save()
    print "\n\nCoverage Report:\n"
    cov.report()
    print "\nHTML version: " + os.path.join(basedir, "tmp/coverage/index.html")
    cov.html_report(directory='tmp/coverage')
    cov.erase()
