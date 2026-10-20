"""Seed an "A11y Testing" journal for accessibility audits.

Creates a published journal with generated images everywhere Janeway shows
one: journal branding, issue covers, article banners and thumbnails, news
images and profile images for authors and the editorial team. About half of
the images are given editor-set alt text so audits can check both that text
and the fallbacks. Safe to re-run: existing records are reused and only
missing images are generated.
"""

import io
from datetime import timedelta
from types import SimpleNamespace

from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from comms import logic as comms_logic
from comms import models as comms_models
from core import files as core_files
from core import logic as core_logic
from core import models as core_models
from core.homepage_elements.carousel.models import Carousel
from core.homepage_elements.featured.models import FeaturedArticle
from core.templatetags.alt_text import encode_file_path
from journal import models as journal_models
from press import models as press_models
from submission import models as submission_models
from utils import install, setting_handler

JOURNAL_CODE = "a11y"
JOURNAL_NAME = "A11y Testing"
THEMES = ["clarity", "OLH", "material", "clean"]
HOMEPAGE_ELEMENTS = [
    "Carousel",
    "About",
    "Featured Articles",
    "Current Issue",
    "News",
]

EDITORIAL_TEAM = [
    (
        "Editors",
        [
            ("a11y.editor.okafor@example.org", "Adaeze", "Okafor", True, True),
            ("a11y.editor.weber@example.org", "Miriam", "Weber", True, False),
        ],
    ),
    (
        "Editorial Board",
        [
            ("a11y.board.tanaka@example.org", "Jun", "Tanaka", True, True),
            ("a11y.board.moreau@example.org", "Lucie", "Moreau", False, False),
            ("a11y.board.almasi@example.org", "Sara", "Almasi", True, False),
        ],
    ),
]

AUTHORS = [
    ("a11y.author.hughes@example.org", "Dylan", "Hughes", True),
    ("a11y.author.reyes@example.org", "Camila", "Reyes", True),
    ("a11y.author.nakamura@example.org", "Hiro", "Nakamura", False),
]

ISSUES = [
    (1, "1", "Seeing Clearly", True),
    (1, "2", "Beyond the Screen", False),
]

ARTICLES = [
    ("Alt text in scholarly publishing: a survey of practice", 0, 0, True, True),
    ("Screen readers and mathematical notation", 1, 0, True, False),
    ("Colour contrast in journal branding", 2, 0, False, False),
    ("Keyboard-only navigation of reading interfaces", 0, 1, True, False),
    ("Captioning figures for everyone", 1, 1, False, False),
    ("Designing accessible PDFs from JATS", 2, 1, True, True),
]

NEWS = [
    ("Welcome to A11y Testing", True, True),
    ("Call for papers: inclusive research methods", True, False),
    ("Editorial board update", False, False),
]

# Uploads smaller than settings.DEFAULT_CROP_SIZE trigger a warning that needs a web request.
BANNER_SIZE = (1600, 700)

PALETTE = ["#1b4965", "#5b3758", "#2d6a4f", "#9c2c2c", "#3d405b", "#6b4226"]


def make_image(label, size=(1200, 800), colour_index=0, fmt="PNG"):
    """A plain placeholder with a band of text naming what it is."""
    colour = PALETTE[colour_index % len(PALETTE)]
    image = Image.new("RGB", size, colour)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=max(18, size[1] // 12))
    box = draw.textbbox((0, 0), label, font=font)
    text_w, text_h = box[2] - box[0], box[3] - box[1]
    band_h = text_h * 3
    top = (size[1] - band_h) // 2
    draw.rectangle([0, top, size[0], top + band_h], fill="#ffffff")
    draw.text(
        ((size[0] - text_w) // 2, top + text_h),
        label,
        fill="#111111",
        font=font,
    )
    buffer = io.BytesIO()
    image.save(buffer, format=fmt)
    return buffer.getvalue()


def uploaded(name, **kwargs):
    return SimpleUploadedFile(name, make_image(**kwargs), content_type="image/png")


def set_alt_text(alt_text, obj=None, file_path=None):
    """Store alt text the way the back-office alt text button does."""
    if obj is not None:
        core_models.AltText.objects.update_or_create(
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk,
            defaults={"alt_text": alt_text},
        )
    else:
        core_models.AltText.objects.update_or_create(
            file_path=encode_file_path(file_path),
            defaults={"alt_text": alt_text},
        )


class Command(BaseCommand):
    help = (
        "Creates or refreshes the 'A11y Testing' journal used for accessibility audits."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--theme",
            choices=THEMES,
            default="clarity",
            help="Theme to set on the journal (default: clarity, the accessibility mode theme).",
        )

    def handle(self, *args, **options):
        self.press = press_models.Press.objects.first()
        if self.press is None:
            self.stderr.write("No press found. Run install_janeway first.")
            return

        self.owner = (
            core_models.Account.objects.filter(is_superuser=True).first()
            or core_models.Account.objects.filter(is_staff=True).first()
        )
        self.journal = self.setup_journal(options["theme"])
        self.request = SimpleNamespace(
            user=self.owner,
            journal=self.journal,
            press=self.press,
            model_content_type=ContentType.objects.get_for_model(self.journal),
            site_type=self.journal,
        )

        self.setup_journal_images()
        self.setup_editorial_team()
        authors = self.setup_authors()
        issues = self.setup_issues()
        articles = self.setup_articles(authors, issues)
        self.setup_news()
        self.setup_homepage(articles)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded '{JOURNAL_NAME}' with the {options['theme']} theme: "
                f"{self.journal.site_url()}"
            )
        )

    def setup_journal(self, theme):
        journal, created = journal_models.Journal.objects.get_or_create(
            code=JOURNAL_CODE,
            defaults={"sequence": self.press.next_journal_order()},
        )
        if created:
            call_command("install_plugins")
            install.update_issue_types(journal)
            journal.setup_directory()

        journal.name = JOURNAL_NAME
        journal.description = (
            "<p>A journal seeded with sample content for accessibility "
            "testing. Every image here has a matching record in the alt "
            "text system, and about half have editor-set alt text.</p>"
        )
        journal.save()
        setting_handler.save_setting("general", "journal_theme", journal, theme)
        setting_handler.save_setting(
            "general",
            "journal_description",
            journal,
            "Sample content for accessibility audits.",
        )
        return journal

    def setup_journal_images(self):
        journal = self.journal
        images = [
            (
                "default_cover_image",
                "Journal cover",
                (800, 1100),
                "Cover of A11y Testing: a teal field with the journal title",
            ),
            ("header_image", "Journal header", (1600, 300), "A11y Testing"),
            ("default_large_image", "Default banner", (1600, 600), None),
            ("default_profile_image", "Default profile", (400, 400), None),
        ]
        for index, (field, label, size, alt) in enumerate(images):
            image_field = getattr(journal, field)
            if not image_field:
                image_field.save(
                    f"a11y-{field}.png",
                    ContentFile(make_image(label, size=size, colour_index=index)),
                    save=True,
                )
            if alt:
                set_alt_text(alt, file_path=image_field)

        if not journal.thumbnail_image:
            core_logic.handle_default_thumbnail(
                SimpleNamespace(
                    user=self.owner,
                    journal=journal,
                    FILES={
                        "default_thumbnail": uploaded(
                            "a11y-thumbnail.png",
                            label="Thumbnail",
                            size=(400, 400),
                            colour_index=4,
                        )
                    },
                ),
                journal,
                None,
            )
            journal.refresh_from_db()
        set_alt_text(
            "A11y Testing logo: a white A on teal", obj=journal.thumbnail_image
        )

    def account(self, email, first, last, with_image, alt_text=None, colour_index=0):
        account, _ = core_models.Account.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
                "first_name": first,
                "last_name": last,
                "is_active": True,
            },
        )
        if with_image and not account.profile_image:
            account.profile_image.save(
                f"a11y-{first.lower()}.png",
                ContentFile(
                    make_image(
                        f"{first} {last}", size=(400, 400), colour_index=colour_index
                    )
                ),
                save=True,
            )
        if with_image and alt_text:
            set_alt_text(alt_text, file_path=account.profile_image)
        return account

    def setup_editorial_team(self):
        for group_index, (group_name, members) in enumerate(EDITORIAL_TEAM):
            group, _ = core_models.EditorialGroup.objects.get_or_create(
                journal=self.journal,
                name=group_name,
                defaults={"sequence": group_index, "display_profile_images": True},
            )
            for member_index, (email, first, last, with_image, with_alt) in enumerate(
                members
            ):
                alt = (
                    f"{first} {last} smiling, photographed outdoors"
                    if with_alt
                    else None
                )
                account = self.account(
                    email, first, last, with_image, alt, member_index + group_index
                )
                core_models.EditorialGroupMember.objects.get_or_create(
                    group=group,
                    user=account,
                    defaults={"sequence": member_index},
                )

    def setup_authors(self):
        authors = []
        for index, (email, first, last, with_image) in enumerate(AUTHORS):
            alt = (
                f"Headshot of {first} {last} against a plain wall"
                if index == 0
                else None
            )
            authors.append(self.account(email, first, last, with_image, alt, index + 2))
        return authors

    def setup_issues(self):
        issue_type = journal_models.IssueType.objects.get(
            journal=self.journal, code="issue"
        )
        issues = []
        for index, (volume, number, title, with_alt) in enumerate(ISSUES):
            issue, _ = journal_models.Issue.objects.get_or_create(
                journal=self.journal,
                volume=volume,
                issue=number,
                defaults={
                    "issue_title": title,
                    "issue_type": issue_type,
                    "date": timezone.now() - timedelta(days=60 * (len(ISSUES) - index)),
                    "issue_description": f"<p>Issue {number}: {title}.</p>",
                },
            )
            for field, label, size in [
                ("cover_image", f"Issue {number} cover", (800, 1100)),
                ("large_image", f"Issue {number} banner", (1600, 600)),
            ]:
                image_field = getattr(issue, field)
                if not image_field:
                    image_field.save(
                        f"a11y-issue-{number}-{field}.png",
                        ContentFile(
                            make_image(label, size=size, colour_index=index + 1)
                        ),
                        save=True,
                    )
            if with_alt:
                set_alt_text(
                    f"Cover of issue {number}, {title}: an eye drawn in white line",
                    file_path=issue.cover_image,
                )
            issues.append(issue)

        self.journal.current_issue = issues[-1]
        self.journal.save()
        return issues

    def setup_articles(self, authors, issues):
        section = submission_models.Section.objects.filter(journal=self.journal).first()
        articles = []
        for index, (
            title,
            author_index,
            issue_index,
            with_images,
            with_alt,
        ) in enumerate(ARTICLES):
            author = authors[author_index]
            article, created = submission_models.Article.objects.get_or_create(
                journal=self.journal,
                title=title,
                defaults={
                    "section": section,
                    "abstract": f"<p>An abstract for “{title}”.</p>",
                    "owner": author,
                    "correspondence_author": author,
                    "stage": submission_models.STAGE_PUBLISHED,
                    "date_submitted": timezone.now() - timedelta(days=200 - index),
                    "date_accepted": timezone.now() - timedelta(days=120 - index),
                    "date_published": timezone.now() - timedelta(days=90 - index * 10),
                    "primary_issue": issues[issue_index],
                    "article_agreement": "Seeded for accessibility testing.",
                },
            )
            if created:
                author.snapshot_as_author(article)
                issues[issue_index].articles.add(article)

            if with_images and not article.large_image_file:
                core_logic.handle_article_large_image_file(
                    uploaded(
                        f"a11y-article-{index}-banner.png",
                        label=f"Article {index + 1} banner",
                        size=BANNER_SIZE,
                        colour_index=index,
                    ),
                    article,
                    self.request,
                )
            if with_images and not article.thumbnail_image_file:
                core_logic.handle_article_thumb_image_file(
                    uploaded(
                        f"a11y-article-{index}-thumb.png",
                        label=f"Article {index + 1}",
                        size=(400, 400),
                        colour_index=index,
                    ),
                    article,
                    self.request,
                )
            article.refresh_from_db()
            if with_alt and article.large_image_file:
                set_alt_text(
                    f"Illustration for “{title}”", obj=article.large_image_file
                )
                set_alt_text(
                    f"Thumbnail for “{title}”", obj=article.thumbnail_image_file
                )
            articles.append(article)
        return articles

    def setup_news(self):
        content_type = ContentType.objects.get_for_model(self.journal)
        for index, (title, with_image, with_alt) in enumerate(NEWS):
            item, created = comms_models.NewsItem.objects.get_or_create(
                content_type=content_type,
                object_id=self.journal.pk,
                title=title,
                defaults={
                    "body": f"<p>{title}. Seeded for accessibility testing.</p>",
                    "posted_by": self.owner,
                    "posted": timezone.now() - timedelta(days=index * 7),
                    "start_display": (
                        timezone.now() - timedelta(days=index * 7)
                    ).date(),
                },
            )
            if with_image and not item.large_image_file:
                new_file = comms_logic.handle_uploaded_file(
                    self.request,
                    uploaded(
                        f"a11y-news-{index}.png",
                        label=f"News {index + 1}",
                        size=BANNER_SIZE,
                        colour_index=index + 3,
                    ),
                )
                item.large_image_file = new_file
                item.save()
            if with_alt and item.large_image_file:
                set_alt_text(
                    f"Photograph accompanying “{title}”", obj=item.large_image_file
                )

    def setup_homepage(self, articles):
        if not self.journal.carousel:
            self.journal.carousel = Carousel.objects.create(
                mode="mixed", latest_articles=True, latest_news=True
            )
            self.journal.save()

        for sequence, article in enumerate(articles[:3]):
            FeaturedArticle.objects.get_or_create(
                journal=self.journal,
                article=article,
                defaults={"sequence": sequence, "added_by": self.owner},
            )

        content_type = ContentType.objects.get_for_model(self.journal)
        elements = core_models.HomepageElement.objects.filter(
            content_type=content_type,
            object_id=self.journal.pk,
        )
        for element in elements:
            if element.name in HOMEPAGE_ELEMENTS:
                element.active = True
                element.sequence = HOMEPAGE_ELEMENTS.index(element.name)
            else:
                element.active = False
            element.save()
