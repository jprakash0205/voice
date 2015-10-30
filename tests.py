import unittest
from analytics import *


class BasicTestCase(unittest.TestCase):
	def setUp(self):
		DATABASE_NAME = os.path.join(APP_DIR, 'analytics-test.db')
		database = SqliteDatabase(DATABASE_NAME)
		database.drop_tables([PageView], safe=True)
		database.create_tables([PageView], safe=True)
	
	def tearDown(self):
		database.drop_tables([PageView], safe=True)

	def test_db_url(self):
		db = connect('sqlite:///:analytics-test.db:')
		self.assertTrue(isinstance(db, SqliteDatabase))
		self.assertEqual(db.database, ':analytics-test.db:')

	def test_config(self):
		self.assertEqual(DATABASE_NAME, ':analytics-test.db:')

	def test_domain(self):
		dmn = 'www.test.com'
		turl = 'http://www.test.com'
		PageView.create(
            domain=dmn,
            url=turl
            )
		print(PageView.select().count())
		self.assertTrue(PageView.select().count() > 0)

