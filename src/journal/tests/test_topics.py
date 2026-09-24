__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import re

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from journal import logic, models
from submission import models as submission_models
from utils import setting_handler
from utils.shared import clear_cache
from utils.testing import helpers


class TopicTestMixin:
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        helpers.create_roles(["editor", "author"])
        cls.editor = helpers.create_editor(cls.journal_one)
        cls.editor.is_active = True
        cls.editor.save()

        cls.section_a = helpers.create_section(
            cls.journal_one, name="Section A", plural="Section As", sequence=0
        )
        cls.section_b = helpers.create_section(
            cls.journal_one, name="Section B", plural="Section Bs", sequence=1
        )
        cls.topic_x = models.Topic.objects.create(
            journal=cls.journal_one, title="Topic X"
        )
        cls.topic_y = models.Topic.objects.create(
            journal=cls.journal_one, title="Topic Y"
        )

        published = dict(
            stage=submission_models.STAGE_PUBLISHED,
            date_published=timezone.now() - timezone.timedelta(days=1),
        )
        cls.a_y = helpers.create_article(
            cls.journal_one,
            title="A-Y",
            section=cls.section_a,
            topic=cls.topic_y,
            **published,
        )
        cls.a_x = helpers.create_article(
            cls.journal_one,
            title="A-X",
            section=cls.section_a,
            topic=cls.topic_x,
            **published,
        )
        cls.a_none = helpers.create_article(
            cls.journal_one,
            title="A-None",
            section=cls.section_a,
            **published,
        )
        cls.b_x = helpers.create_article(
            cls.journal_one,
            title="B-X",
            section=cls.section_b,
            topic=cls.topic_x,
            **published,
        )
        cls.issue = helpers.create_issue(
            cls.journal_one,
            vol=1,
            number=1,
            articles=[cls.a_y, cls.a_x, cls.a_none, cls.b_x],
        )
        for order, article in enumerate([cls.a_y, cls.a_x, cls.a_none]):
            models.ArticleOrdering.objects.update_or_create(
                issue=cls.issue,
                section=cls.section_a,
                article=article,
                defaults={"order": order},
            )


class TestIssueTopicOrdering(TopicTestMixin, TestCase):
    def sorted_titles(self, grouping):
        return [
            article.title
            for article in self.issue.get_sorted_articles(grouping=grouping)
        ]

    def test_section_grouping_ignores_topics(self):
        self.assertEqual(
            self.sorted_titles(models.ARTICLE_GROUPING_SECTION),
            ["A-Y", "A-X", "A-None", "B-X"],
        )

    def test_section_topic_grouping(self):
        self.assertEqual(
            self.sorted_titles(models.ARTICLE_GROUPING_SECTION_TOPIC),
            ["A-None", "A-X", "A-Y", "B-X"],
        )

    def test_topic_grouping(self):
        self.assertEqual(
            self.sorted_titles(models.ARTICLE_GROUPING_TOPIC),
            ["A-X", "B-X", "A-Y", "A-None"],
        )

    def test_topic_grouping_respects_issue_topic_order(self):
        self.issue.set_topic_order([self.topic_y, self.topic_x])
        self.assertEqual(
            self.sorted_titles(models.ARTICLE_GROUPING_TOPIC),
            ["A-Y", "A-X", "B-X", "A-None"],
        )

    def test_topic_section_grouping(self):
        self.issue.set_section_order([self.section_b, self.section_a])
        self.assertEqual(
            self.sorted_titles(models.ARTICLE_GROUPING_TOPIC_SECTION),
            ["B-X", "A-X", "A-Y", "A-None"],
        )

    def test_ungrouped_follows_article_order_only(self):
        models.ArticleOrdering.objects.filter(
            issue=self.issue, article=self.b_x
        ).update(order=0)
        models.ArticleOrdering.objects.filter(
            issue=self.issue, article=self.a_y
        ).update(order=5)
        self.assertEqual(
            self.sorted_titles(models.ARTICLE_GROUPING_UNGROUPED),
            ["B-X", "A-X", "A-None", "A-Y"],
        )

    def test_topic_grouping_sorts_by_article_order_across_sections(self):
        models.ArticleOrdering.objects.filter(
            issue=self.issue, article=self.b_x
        ).update(order=0)
        self.assertEqual(
            self.sorted_titles(models.ARTICLE_GROUPING_TOPIC),
            ["B-X", "A-X", "A-Y", "A-None"],
        )

    def test_get_sorted_sections(self):
        self.assertEqual(
            list(self.issue.get_sorted_sections()),
            [self.section_a, self.section_b],
        )
        self.issue.set_section_order([self.section_b, self.section_a])
        self.assertEqual(
            list(self.issue.get_sorted_sections()),
            [self.section_b, self.section_a],
        )

    def test_auto_sort_numbers_articles_across_the_issue(self):
        self.issue.order_articles_in_sections(sort_field="title", order="asc")
        self.assertEqual(
            self.sorted_titles(models.ARTICLE_GROUPING_UNGROUPED),
            ["A-None", "A-X", "A-Y", "B-X"],
        )
        self.assertEqual(
            self.sorted_titles(models.ARTICLE_GROUPING_TOPIC),
            ["A-X", "B-X", "A-Y", "A-None"],
        )

    def test_grouping_defaults_to_journal_setting(self):
        self.journal_one.issue_article_grouping = models.ARTICLE_GROUPING_TOPIC
        self.journal_one.save()
        self.issue.refresh_from_db()
        self.assertEqual(
            [a.title for a in self.issue.get_sorted_articles()],
            self.sorted_titles(models.ARTICLE_GROUPING_TOPIC),
        )

    def test_all_topics(self):
        self.assertEqual(
            list(self.issue.all_topics),
            [self.topic_x, self.topic_y],
        )
        self.issue.set_topic_order([self.topic_y, self.topic_x])
        self.assertEqual(
            list(self.issue.all_topics),
            [self.topic_y, self.topic_x],
        )


class TestGroupIssueArticles(TopicTestMixin, TestCase):
    def group(self, grouping):
        return logic.group_issue_articles(
            self.issue.get_sorted_articles(grouping=grouping),
            grouping,
        )

    def test_section_grouping(self):
        groups = self.group(models.ARTICLE_GROUPING_SECTION)
        self.assertEqual(
            [group.heading for group in groups],
            ["Section As", "Section B"],
        )
        self.assertEqual(groups[0].next, self.section_b)
        self.assertEqual(groups[1].previous, self.section_a)
        self.assertEqual(len(groups[0].subgroups), 1)
        self.assertEqual(groups[0].subgroups[0].heading, "")
        self.assertEqual(groups[0].subgroups[0].article_count, 3)

    def test_section_topic_grouping(self):
        groups = self.group(models.ARTICLE_GROUPING_SECTION_TOPIC)
        self.assertEqual(
            [
                [(sub.heading, len(sub.articles)) for sub in group.subgroups]
                for group in groups
            ],
            [[("", 1), ("Topic X", 1), ("Topic Y", 1)], [("Topic X", 1)]],
        )
        # Groups without a topic are never a neighbour to move next to
        subgroups = groups[0].subgroups
        self.assertIsNone(subgroups[1].previous)
        self.assertEqual(subgroups[1].next, self.topic_y)

    def test_topic_section_grouping(self):
        groups = self.group(models.ARTICLE_GROUPING_TOPIC_SECTION)
        self.assertEqual(
            [group.heading for group in groups],
            ["Topic X", "Topic Y", ""],
        )
        self.assertEqual(
            [sub.heading for sub in groups[0].subgroups],
            ["Section A", "Section B"],
        )
        # The group without a topic is last and never a neighbour
        self.assertIsNone(groups[1].next)

    def test_ungrouped(self):
        groups = self.group(models.ARTICLE_GROUPING_UNGROUPED)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].heading, "")
        self.assertEqual(groups[0].subgroups[0].article_count, 4)

    def test_issue_article_label(self):
        cases = {
            models.ARTICLE_GROUPING_SECTION: ["Topic X", "", "Topic X"],
            models.ARTICLE_GROUPING_SECTION_TOPIC: ["Topic X", "", "Topic X"],
            models.ARTICLE_GROUPING_TOPIC: ["Section A", "Section A", "Section B"],
            models.ARTICLE_GROUPING_TOPIC_SECTION: [
                "Section A",
                "Section A",
                "Section B",
            ],
            models.ARTICLE_GROUPING_UNGROUPED: [
                "Section A \u2022 Topic X",
                "Section A",
                "Section B \u2022 Topic X",
            ],
        }
        for grouping, expected in cases.items():
            with self.subTest(grouping=grouping):
                self.assertEqual(
                    [
                        logic.issue_article_label(article, grouping)
                        for article in (self.a_x, self.a_none, self.b_x)
                    ],
                    expected,
                )

    def test_move_in_order(self):
        self.assertEqual(logic.move_in_order([1, 2, 3], 3, 1), [3, 1, 2])
        self.assertEqual(logic.move_in_order([1, 2, 3], 1, 3, after=True), [2, 3, 1])


@override_settings(URL_CONFIG="domain")
class TestTopicViews(TopicTestMixin, TestCase):
    def setUp(self):
        self.client.force_login(self.editor)
        self.server_name = self.journal_one.domain

    def test_topic_list(self):
        response = self.client.get(
            reverse("core_manager_topics"), SERVER_NAME=self.server_name
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Topic X")

    def test_topic_list_requires_permission(self):
        author = helpers.create_author(self.journal_one)
        author.is_active = True
        author.save()
        self.client.force_login(author)
        response = self.client.get(
            reverse("core_manager_topics"), SERVER_NAME=self.server_name
        )
        self.assertNotEqual(response.status_code, 200)

    def test_create_topic(self):
        response = self.client.post(
            reverse("core_manager_topic_add"),
            {"title": "Topic Z", "public_submissions": "on"},
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("showMessage", response["HX-Trigger"])
        self.assertTrue(
            models.Topic.objects.filter(
                journal=self.journal_one,
                title="Topic Z",
                public_submissions=True,
            ).exists()
        )

    def test_create_topic_requires_title(self):
        response = self.client.post(
            reverse("core_manager_topic_add"),
            {"title": ""},
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/manager/topics/topic_form.html")
        self.assertEqual(models.Topic.objects.count(), 2)

    def test_edit_topic(self):
        response = self.client.post(
            reverse("core_manager_topic_edit", kwargs={"topic_id": self.topic_x.pk}),
            {"title": "Topic X2"},
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 200)
        self.topic_x.refresh_from_db()
        self.assertEqual(self.topic_x.title, "Topic X2")
        self.assertFalse(self.topic_x.public_submissions)

    def test_cannot_edit_topic_from_another_journal(self):
        other_topic = models.Topic.objects.create(
            journal=self.journal_two, title="Other"
        )
        response = self.client.post(
            reverse("core_manager_topic_edit", kwargs={"topic_id": other_topic.pk}),
            {"title": "Hijacked"},
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_empty_topic(self):
        empty_topic = models.Topic.objects.create(
            journal=self.journal_one, title="Empty"
        )
        response = self.client.delete(
            reverse("core_manager_topic_edit", kwargs={"topic_id": empty_topic.pk}),
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(models.Topic.objects.filter(pk=empty_topic.pk).exists())

    def test_cannot_delete_topic_with_articles(self):
        response = self.client.delete(
            reverse("core_manager_topic_edit", kwargs={"topic_id": self.topic_x.pk}),
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("warning", response["HX-Trigger"])
        self.assertTrue(models.Topic.objects.filter(pk=self.topic_x.pk).exists())

    def test_sort_issue_topics_legacy_redirect(self):
        response = self.client.post(
            reverse("manage_sort_issue_topics", kwargs={"issue_id": self.issue.pk}),
            {"down": self.topic_x.pk},
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            list(self.issue.all_topics),
            [self.topic_y, self.topic_x],
        )

    def test_sort_issue_topics_htmx(self):
        self.journal_one.issue_article_grouping = models.ARTICLE_GROUPING_TOPIC
        self.journal_one.save()
        response = self.client.post(
            reverse("manage_sort_issue_topics", kwargs={"issue_id": self.issue.pk}),
            {"move": self.topic_y.pk, "before": self.topic_x.pk},
            SERVER_NAME=self.server_name,
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/elements/issue/table_of_contents.html")
        self.assertEqual(
            list(self.issue.all_topics),
            [self.topic_y, self.topic_x],
        )
        content = response.content.decode()
        self.assertLess(content.index("Topic Y"), content.index("Topic X"))

    def test_sort_issue_sections_htmx(self):
        response = self.client.post(
            reverse("manage_sort_issue_sections", kwargs={"issue_id": self.issue.pk}),
            {"move": self.section_a.pk, "after": self.section_b.pk},
            SERVER_NAME=self.server_name,
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(self.issue.get_sorted_sections()),
            [self.section_b, self.section_a],
        )

    def test_sort_issue_ignores_invalid_targets(self):
        other_topic = models.Topic.objects.create(
            journal=self.journal_two, title="Other"
        )
        for data in (
            {"move": other_topic.pk, "before": self.topic_x.pk},
            {"move": "nope", "before": self.topic_x.pk},
            {"up": self.topic_x.pk},
        ):
            with self.subTest(data=data):
                response = self.client.post(
                    reverse(
                        "manage_sort_issue_topics",
                        kwargs={"issue_id": self.issue.pk},
                    ),
                    data,
                    SERVER_NAME=self.server_name,
                    HTTP_HX_REQUEST="true",
                )
                self.assertEqual(response.status_code, 200)
                self.assertFalse(models.TopicOrdering.objects.exists())

    def test_issue_manager_renders_for_every_grouping(self):
        for grouping, _label in models.ARTICLE_GROUPING_CHOICES:
            with self.subTest(grouping=grouping):
                self.journal_one.issue_article_grouping = grouping
                self.journal_one.save()
                response = self.client.get(
                    reverse("manage_issues_id", kwargs={"issue_id": self.issue.pk}),
                    SERVER_NAME=self.server_name,
                )
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "B-X")

    def test_topic_articles_page(self):
        response = self.client.get(
            reverse(
                "core_manager_topic_articles", kwargs={"topic_id": self.topic_x.pk}
            ),
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A-X")
        self.assertContains(response, "B-X")
        self.assertNotContains(response, "A-Y")

    def post_topic_articles(self, topic, data):
        return self.client.post(
            reverse("core_manager_topic_articles", kwargs={"topic_id": topic.pk}),
            data,
            SERVER_NAME=self.server_name,
            HTTP_HX_REQUEST="true",
        )

    def test_move_articles_to_another_topic(self):
        response = self.post_topic_articles(
            self.topic_x,
            {
                "action": "move",
                "topic": self.topic_y.pk,
                "articles": [self.a_x.pk, self.b_x.pk],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("success", response["HX-Trigger"])
        self.assertEqual(self.topic_x.article_set.count(), 0)
        self.assertEqual(self.topic_y.article_set.count(), 3)

    def test_clear_articles_topic(self):
        response = self.post_topic_articles(
            self.topic_x,
            {"action": "clear", "articles": [self.a_x.pk]},
        )
        self.assertEqual(response.status_code, 200)
        self.a_x.refresh_from_db()
        self.b_x.refresh_from_db()
        self.assertIsNone(self.a_x.topic)
        self.assertEqual(self.b_x.topic, self.topic_x)

    def test_bulk_action_only_affects_the_topic_articles(self):
        self.post_topic_articles(
            self.topic_x,
            {"action": "clear", "articles": [self.a_y.pk]},
        )
        self.a_y.refresh_from_db()
        self.assertEqual(self.a_y.topic, self.topic_y)

    def test_cannot_move_articles_to_another_journal_topic(self):
        other_topic = models.Topic.objects.create(
            journal=self.journal_two, title="Other"
        )
        response = self.post_topic_articles(
            self.topic_x,
            {"action": "move", "topic": other_topic.pk, "articles": [self.a_x.pk]},
        )
        self.assertIn("warning", response["HX-Trigger"])
        self.a_x.refresh_from_db()
        self.assertEqual(self.a_x.topic, self.topic_x)

    def test_bulk_action_without_selection(self):
        response = self.post_topic_articles(self.topic_x, {"action": "clear"})
        self.assertIn("warning", response["HX-Trigger"])
        self.assertEqual(self.topic_x.article_set.count(), 2)

    def test_configurator_links_to_topic_manager(self):
        response = self.client.get(
            reverse("submission_configurator"), SERVER_NAME=self.server_name
        )
        self.assertContains(
            response,
            'href="{}" target="_blank"'.format(reverse("core_manager_topics")),
        )


@override_settings(URL_CONFIG="domain")
class TestIssueTocArticleEdit(TopicTestMixin, TestCase):
    def setUp(self):
        self.client.force_login(self.editor)
        self.server_name = self.journal_one.domain

    def edit_url(self, article):
        return reverse(
            "issue_toc_article_edit",
            kwargs={"issue_id": self.issue.pk, "article_id": article.pk},
        )

    def test_edit_row(self):
        response = self.client.get(
            self.edit_url(self.a_x),
            SERVER_NAME=self.server_name,
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "admin/elements/issue/toc_article_edit_row.html"
        )
        self.assertContains(response, 'class="filter-select"', count=2)
        self.assertContains(response, "Section B")
        self.assertContains(response, "No topic")

    def test_cancel_renders_the_row(self):
        response = self.client.get(
            reverse(
                "issue_toc_article_row",
                kwargs={"issue_id": self.issue.pk, "article_id": self.a_x.pk},
            ),
            SERVER_NAME=self.server_name,
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/elements/issue/toc_article_row.html")

    def test_confirm_updates_article_and_refreshes_toc(self):
        response = self.client.post(
            self.edit_url(self.a_x),
            {"section": self.section_b.pk, "topic": ""},
            SERVER_NAME=self.server_name,
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/elements/issue/table_of_contents.html")
        self.assertIn("showMessage", response["HX-Trigger"])
        self.a_x.refresh_from_db()
        self.assertEqual(self.a_x.section, self.section_b)
        self.assertIsNone(self.a_x.topic)
        # The article order moves with the article to its new section
        self.assertTrue(
            models.ArticleOrdering.objects.filter(
                issue=self.issue, article=self.a_x, section=self.section_b
            ).exists()
        )
        self.assertIn(
            self.a_x,
            [
                article
                for article in self.issue.get_sorted_articles()
                if article.article_order is not None
            ],
        )

    def test_invalid_choice_rerenders_the_row(self):
        other_section = helpers.create_section(self.journal_two, name="Other")
        response = self.client.post(
            self.edit_url(self.a_x),
            {"section": other_section.pk, "topic": self.topic_y.pk},
            SERVER_NAME=self.server_name,
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["HX-Retarget"], "#articles-{}".format(self.a_x.pk))
        self.a_x.refresh_from_db()
        self.assertEqual(self.a_x.section, self.section_a)
        self.assertEqual(self.a_x.topic, self.topic_x)

    def test_article_must_be_in_the_issue(self):
        other_article = helpers.create_article(self.journal_one, title="Elsewhere")
        response = self.client.get(
            self.edit_url(other_article),
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 404)


@override_settings(URL_CONFIG="domain")
class TestIssuePageSubgroupLabels(TopicTestMixin, TestCase):
    THEMES = ("OLH", "material", "clean", "clarity")

    def setUp(self):
        self.server_name = self.journal_one.domain

    def get_issue_page(self, theme, grouping):
        setting_handler.save_setting(
            "general", "journal_theme", self.journal_one, theme
        )
        clear_cache()
        self.journal_one.issue_article_grouping = grouping
        self.journal_one.save()
        response = self.client.get(
            reverse("journal_issue", kwargs={"issue_id": self.issue.pk}),
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def headings(self, content):
        return [
            heading.strip()
            for heading in re.findall(
                r'<h2 class="(?:em|section-title)">(.*?)</h2>', content, re.S
            )
        ]

    def labels(self, content):
        return re.findall(r'<h3 class="article-subgroup">(.*?)</h3>', content)

    def assertIssuePage(self, grouping, headings, labels):
        for theme in self.THEMES:
            with self.subTest(theme=theme, grouping=grouping):
                content = self.get_issue_page(theme, grouping)
                self.assertEqual(self.headings(content), headings)
                self.assertEqual(self.labels(content), labels)

    def test_section(self):
        self.assertIssuePage(
            models.ARTICLE_GROUPING_SECTION,
            ["Section As", "Section B"],
            ["Topic Y", "Topic X", "Topic X"],
        )

    def test_topic(self):
        self.assertIssuePage(
            models.ARTICLE_GROUPING_TOPIC,
            ["Topic X", "Topic Y", "Other articles"],
            ["Section A", "Section B", "Section A", "Section A"],
        )

    def test_section_then_topic(self):
        self.assertIssuePage(
            models.ARTICLE_GROUPING_SECTION_TOPIC,
            ["Section As", "Section B"],
            ["Topic X", "Topic Y", "Topic X"],
        )

    def test_topic_then_section(self):
        self.assertIssuePage(
            models.ARTICLE_GROUPING_TOPIC_SECTION,
            ["Topic X", "Topic Y", "Other articles"],
            ["Section A", "Section B", "Section A", "Section A"],
        )

    def test_ungrouped(self):
        self.assertIssuePage(
            models.ARTICLE_GROUPING_UNGROUPED,
            [],
            [
                "Section A \u2022 Topic Y",
                "Section A \u2022 Topic X",
                "Section A",
                "Section B \u2022 Topic X",
            ],
        )

    def test_no_other_articles_heading_when_all_articles_have_a_topic(self):
        self.a_none.topic = self.topic_y
        self.a_none.save()
        self.assertIssuePage(
            models.ARTICLE_GROUPING_TOPIC,
            ["Topic X", "Topic Y"],
            ["Section A", "Section B", "Section A", "Section A"],
        )
