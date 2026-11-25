from django.test import TestCase

from core import models as core_models
from core.homepage_elements.featured import hooks, models as featured_models
from utils.testing import helpers


class FeaturedHomepageElementHookTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal, _journal_two = helpers.create_journals()
        cls.request = helpers.get_request(
            press=cls.press,
            journal=cls.journal,
        )
        cls.article = helpers.create_article(
            cls.journal,
            date_published=helpers.get_aware_datetime("2024-01-01"),
        )

    def test_hook_uses_stable_identifier_when_element_is_renamed(self):
        homepage_element = core_models.HomepageElement.objects.create(
            name="Editor's Picks",
            configure_url="featured_articles_setup",
            template_path="journal/homepage_elements/featured.html",
            object=self.journal,
            active=True,
        )
        featured = featured_models.FeaturedArticle.objects.create(
            article=self.article,
            journal=self.journal,
        )

        context = hooks.yield_homepage_element_context(
            self.request,
            core_models.HomepageElement.objects.filter(pk=homepage_element.pk),
        )

        self.assertIn("featured_articles", context)
        self.assertEqual(list(context["featured_articles"]), [featured])

    def test_hook_returns_empty_context_without_featured_element(self):
        other_element = core_models.HomepageElement.objects.create(
            name="Popular Articles",
            configure_url="popular_articles_setup",
            template_path="journal/homepage_elements/popular.html",
            object=self.journal,
            active=True,
        )

        context = hooks.yield_homepage_element_context(
            self.request,
            core_models.HomepageElement.objects.filter(pk=other_element.pk),
        )

        self.assertEqual(context, {})
