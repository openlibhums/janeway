from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.urls.base import clear_script_prefix

from journal import models
from journal.tests.utils import make_test_journal
from press.models import Press
from utils.testing import helpers
from utils import setting_handler
from core import models as core_models
from submission import models as submission_models


class TestJournalSite(TestCase):

    def setUp(self):
        self.press = Press(domain="sitetestpress.org")
        self.press.save()
        self.journal_domain = 'fetesting.janeway.systems'
        self.article_title = 'Test article: a test article'
        journal_kwargs = dict(
            code="fetests",
            domain=self.journal_domain,
        )
        self.journal = make_test_journal(**journal_kwargs)
        helpers.create_roles(['Author', 'Reviewer'])
        self.author = helpers.create_user(
            'author@janeway.systems',
            ['author'],
            self.journal,
            **{'first_name': 'New', 'last_name': 'Author'},
        )
        self.new_user = helpers.create_user(
            'new_user@janeway.systems',
            ['author'],
            self.journal,
            **{'is_active': True}
        )
        self.published_article = helpers.create_article(
            journal=self.journal,
            title=self.article_title,
            stage="Published",
            abstract="test_abstract",
            date_published=timezone.now(),
        )
        keyword, c = submission_models.Keyword.objects.get_or_create(word='Test')
        self.published_article.keywords.add(keyword)
        self.published_article.authors.add(
            self.author,
        )
        self.published_article.snapshot_authors()

        # create two issue types for testing
        issue_type = models.IssueType.objects.create(
            journal=self.journal,
            code='issue',
        )
        collection_type = models.IssueType.objects.create(
            journal=self.journal,
            code='collection',
        )
        self.issue, c = models.Issue.objects.get_or_create(
            journal=self.journal,
            volume="4",
            issue="4",
            defaults={
                'date': timezone.now(),
                'issue_type': issue_type,
            }
        )
        self.issue.articles.add(self.published_article)
        self.collection, c = models.Issue.objects.get_or_create(
            journal=self.journal,
            volume='0',
            issue='0',
            issue_type=collection_type,
            defaults={
                'date': timezone.now(),
                'issue_title': 'Test Collection'
            }
        )
        self.collection.articles.add(self.published_article)

        self.editorial_group, c = core_models.EditorialGroup.objects.get_or_create(
            name='Test Editor Group',
            journal=self.journal,
            press=self.press,
            sequence=1,
        )
        core_models.EditorialGroupMember.objects.create(
            group=self.editorial_group,
            user=self.author,
            sequence=1,
        )
        clear_script_prefix()

    def test_flat_front_end_pages(self):
        flat_pages_to_test = [
            'website_index',
            'journal_articles',
            'search',
            'journal_submissions',
            'editorial_team',
            'contact',
            'journal_issues',
            'journal_collections_type',
        ]

        for page in flat_pages_to_test:
            response = self.client.get(reverse(page), SERVER_NAME=self.journal_domain)
            self.assertEqual(response.status_code, 200)

    def test_issue_page(self):
        response = self.client.get(
            reverse(
                'journal_issue',
                kwargs={
                    'issue_id': self.issue.pk,
                }
            ),
            SERVER_NAME=self.journal_domain
        )
        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertContains(
            response,
            'Volume 4'
        )
        self.assertContains(
            response,
            self.article_title
        )

    def test_become_reviewer_page(self):
        self.client.force_login(
            self.new_user,
        )
        response = self.client.get(
            reverse(
                'become_reviewer',
            ),
            SERVER_NAME=self.journal_domain
        )
        self.assertEqual(
            response.status_code,
            200,
        )
        self.client.post(
            reverse(
                'become_reviewer',
            ),
            data={
                'action': 'go',
            },
            SERVER_NAME=self.journal_domain
        )
        response = self.client.get(
            reverse(
                'become_reviewer',
            ),
            SERVER_NAME=self.journal_domain
        )
        self.assertEqual(
            response.status_code,
            200
        )
        self.assertTrue(
            self.new_user.check_role(self.journal, 'reviewer')
        )

    def test_collection_page(self):
        response = self.client.get(
            reverse(
                'journal_collection',
                kwargs={
                    'collection_id': self.collection.pk,
                }
            ),
            SERVER_NAME=self.journal_domain
        )
        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertContains(
            response,
            'Test Collection'
        )
        self.assertContains(
            response,
            self.article_title
        )

    def test_editorial_team_group_page(self):
        response = self.client.get(
            reverse(
                'editorial_team_group',
                kwargs={
                    'group_id': self.editorial_group.pk,
                }
            ),
            SERVER_NAME=self.journal_domain,
        )
        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertContains(
            response,
            'New Author'
        )

    def test_authors_page(self):
        response = self.client.get(
            reverse(
                'authors',
            ),
            SERVER_NAME=self.journal_domain
        )
        self.assertEqual(
            response.status_code,
            200,
        )

    def test_keywords_page(self):
        setting_handler.save_setting(
            'general',
            'keyword_list_page',
            self.journal,
            value=True,
        )
        response = self.client.get(
            reverse(
                'keywords',
            ),
            SERVER_NAME=self.journal_domain
        )
        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertContains(
            response,
            'Test',
        )

    def test_article_page(self):
        response = self.client.get(
            reverse(
                'article_view',
                kwargs={
                    'identifier_type': 'id',
                    'identifier': self.published_article.pk,
                }
            ),
            SERVER_NAME=self.journal_domain
        )
        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertContains(
            response,
            self.article_title,
        )

    def test_search_includes_article(self):
        url = '{}?article_search=Test&sort=relevance'.format(
            reverse(
                'search',
            )
        )
        response = self.client.get(
            url,
            SERVER_NAME=self.journal_domain
        )
        self.assertEqual(
            response.status_code,
            200
        )
        self.assertContains(
            response,
            self.article_title,
        )

    def test_search_excludes_artucle(self):
        url = '{}?article_search=Janeway&sort=relevance'.format(
            reverse(
                'search',
            )
        )
        response = self.client.get(
            url,
            SERVER_NAME=self.journal_domain
        )
        self.assertEqual(
            response.status_code,
            200
        )
        self.assertNotContains(
            response,
            self.article_title,
        )
