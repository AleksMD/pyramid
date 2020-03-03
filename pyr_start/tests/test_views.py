import unittest
import transaction
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy.pool import NullPool

from pyramid import testing
from .db_conf import TEST_DATABASE_CONFIG, ROOT_DATABASE_CONFIG


def dummy_request(dbsession):
    return testing.DummyRequest(dbsession=dbsession)


SQLALCHEMY_URL = (
            'postgresql://{user}:{password}@localhost:{port}/{db_name}'.format(
                user=TEST_DATABASE_CONFIG.get('user'),
                password=TEST_DATABASE_CONFIG.get('password'),
                db_name=TEST_DATABASE_CONFIG.get('database'),
                port=TEST_DATABASE_CONFIG.get('port')))


def create_test_database(conn):
    user = TEST_DATABASE_CONFIG.get('user')
    password = TEST_DATABASE_CONFIG.get('password')
    db_name = TEST_DATABASE_CONFIG.get('database')
    with conn.cursor() as cursor:
        cursor.execute(
            f"CREATE ROLE {user} WITH LOGIN CREATEDB PASSWORD '{password}'")
        cursor.execute(f"CREATE DATABASE {db_name}")
        cursor.execute(
            f"GRANT ALL PRIVILEGES ON DATABASE {db_name} to {user};")
        conn.commit()


def drop_test_database(conn):
    user = TEST_DATABASE_CONFIG.get('user')
    db_name = TEST_DATABASE_CONFIG.get('database')
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT * FROM pg_stat_activity"
                       f" WHERE datname='{db_name}';")
        print(cursor.fetchall())
        cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
        cursor.execute(
            f"SELECT 1 FROM pg_catalog.pg_user WHERE usename= '{user}'")
        if cursor.fetchone():
            cursor.execute(f"DROP ROLE {user}")
        conn.commit()


class BaseTest(unittest.TestCase):
    def setUp(self):
        from pyr_start.models import get_tm_session
        self.conn = psycopg2.connect(**ROOT_DATABASE_CONFIG)
        self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        drop_test_database(self.conn)
        create_test_database(self.conn)
        self.config = testing.setUp(
            settings={'sqlalchemy.url': SQLALCHEMY_URL,
                      'sqlalchemy.poolclass': NullPool})
        self.config.include('pyr_start.models')
        self.config.include('pyr_start.routes')

        session_factory = self.config.registry['dbsession_factory']
        self.session = get_tm_session(session_factory, transaction.manager)

        self.init_database()

    def init_database(self):
        from pyr_start.models.meta import Base
        session_factory = self.config.registry['dbsession_factory']
        engine = session_factory.kw['bind']
        Base.metadata.create_all(engine)

    def tearDown(self):
        self.session.close()
        testing.tearDown()
        transaction.abort()

    def makeUser(self, name, role, password='dummy'):
        from pyr_start.models import User
        user = User(name=name, role=role)
        user.set_password(password)
        return user

    def makePage(self, name, data, creator):
        from pyr_start.models import Page
        return Page(name=name, data=data, creator=creator)


class ViewWikiTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('..routes')

    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, request):
        from pyr_start.views.default import view_wiki
        return view_wiki(request)

    def test_it(self):
        request = testing.DummyRequest()
        response = self._callFUT(request)
        self.assertEqual(response.location, 'http://example.com/FrontPage')


class ViewPageTests(BaseTest):
    def _callFUT(self, request):
        from pyr_start.views.default import view_page
        return view_page(request)

    def test_it(self):
        from pyr_start.routes import PageResource

        user = self.makeUser('foo', 'editor')
        page = self.makePage('IDoExist', 'Hello CruelWorld IDoExist', user)
        self.session.add_all([page, user])

        request = dummy_request(self.session)
        request.context = PageResource(page)

        info = self._callFUT(request)
        self.assertEqual(info['page'], page)
        self.assertEqual(
            info['page_body'],
            '<div class="document">\n'
            '<p>Hello <a href="http://example.com/add_page/CruelWorld">'
            'CruelWorld</a> '
            '<a href="http://example.com/IDoExist">'
            'IDoExist</a>'
            '</p>\n</div>\n')
        self.assertEqual(info['edit_url'],
                         'http://example.com/IDoExist/edit_page')


class AddPageTests(BaseTest):
    def _callFUT(self, request):
        from pyr_start.views.default import add_page
        return add_page(request)

    def test_it_pageexists(self):
        from pyr_start.models import Page
        from pyr_start.routes import NewPage
        request = testing.DummyRequest({'form.submitted': True,
                                        'body': 'Hello yo!'},
                                       dbsession=self.session)

        request.user = self.makeUser('foo', 'editor')
        request.context = NewPage('AnotherPage')
        self._callFUT(request)
        pagecount = self.session.query(Page).filter_by(
            name='AnotherPage').count()
        self.assertGreater(pagecount, 0)

    def test_it_notsubmitted(self):
        from pyr_start.routes import NewPage
        request = dummy_request(self.session)
        request.user = self.makeUser('foo', 'editor')
        request.context = NewPage('AnotherPage')
        info = self._callFUT(request)
        self.assertEqual(info['pagedata'], '')
        self.assertEqual(info['save_url'],
                         'http://example.com/add_page/AnotherPage')

    def test_it_submitted(self):
        from pyr_start.models import Page
        from pyr_start.routes import NewPage
        request = testing.DummyRequest({'form.submitted': True,
                                        'body': 'Hello yo!'},
                                       dbsession=self.session)
        request.user = self.makeUser('foo', 'editor')
        request.context = NewPage('AnotherPage')
        self._callFUT(request)
        page = self.session.query(Page).filter_by(name='AnotherPage').one()
        self.assertEqual(page.data, 'Hello yo!')


class EditPageTests(BaseTest):
    def _callFUT(self, request):
        from pyr_start.views.default import edit_page
        return edit_page(request)

    def makeContext(self, page):
        from pyr_start.routes import PageResource
        return PageResource(page)

    def test_it_notsubmitted(self):
        user = self.makeUser('foo', 'editor')
        page = self.makePage('abc', 'hello', user)
        self.session.add_all([page, user])

        request = dummy_request(self.session)
        request.context = self.makeContext(page)
        info = self._callFUT(request)
        self.assertEqual(info['pagename'], 'abc')
        self.assertEqual(info['save_url'],
                         'http://example.com/abc/edit_page')

    def test_it_submitted(self):
        user = self.makeUser('foo', 'editor')
        page = self.makePage('abc', 'hello', user)
        self.session.add_all([page, user])
        request = testing.DummyRequest({'form.submitted': True,
                                        'body': 'Hello yo!'},
                                       dbsession=self.session)
        request.context = self.makeContext(page)
        response = self._callFUT(request)
        self.assertEqual(response.location, 'http://example.com/abc')
        self.assertEqual(page.data, 'Hello yo!')
