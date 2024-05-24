__copyright__ = "Copyright 2022 Birkbeck, University of London"
__author__ = "Martin Paul Eve, Andy Byers, Mauro Sanchez and Joseph Muller"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck, University of London"

from django.contrib.contenttypes.models import ContentType
from django.contrib import admin
from django.template.defaultfilters import truncatewords_html
from core.model_utils import DateTimePickerInput, DateTimePickerModelField
from utils import models as utils_models
from discussion import models as discussion_models
from review import models as review_models
from identifiers import models as identifier_models
from copyediting import models as copyediting_models
from submission import models as submission_models
from journal import models as journal_models
from cron import models as cron_models
from core import models as core_models
from repository import models as repository_models
from press import models as press_models
from comms import models as comms_models


class JanewayModelAdmin(admin.ModelAdmin):
    formfield_overrides = {
        DateTimePickerModelField: {
            "widget": DateTimePickerInput
        },
    }


class ArticleFKModelAdmin(JanewayModelAdmin):
    """
    An abstract ModelAdmin base class for objects
    that relate to Article with a foreign key `article`.
    Adds a _journal function for use in list_display.
    Adds an _article function that truncates long titles,
    for use in list_display.
    """

    def _journal(self, obj):
        return obj.article.journal if obj and obj.article else ''

    def _article(self, obj):
        return truncatewords_html(str(obj.article), 5) if obj else ''

    def _author(self, obj):
        return obj.article.correspondence_author if obj else ''


class PreprintFKModelAdmin(JanewayModelAdmin):
    """
    An abstract ModelAdmin base class for objects
    that relate to Preprint with a foreign key `preprint`.
    Adds a _repository function for use in list_display.
    Adds an _preprint function that truncates long titles,
    for use in list_display.
    """

    def _repository(self, obj):
        return obj.preprint.repository if obj else ''

    def _preprint(self, obj):
        return truncatewords_html(str(obj.preprint), 5) if obj else ''


class AccountInterestInline(admin.TabularInline):
    model = core_models.Account.interest.through
    extra = 0
    raw_id_fields = ('account',)


class PostInline(admin.TabularInline):
    model = discussion_models.Post
    extra = 0
    raw_id_fields = ('owner', 'thread')
    exclude = ('read_by',)
    ordering = ('posted',)


class ReviewAssignmentAnswerInline(admin.TabularInline):
    model = review_models.ReviewAssignmentAnswer
    extra = 0


class RevisionActionInline(admin.TabularInline):
    model = review_models.RevisionRequest.actions.through
    extra = 0
    raw_id_fields = ('revisionaction',)


class ToAddressInline(admin.TabularInline):
    model = utils_models.ToAddress
    extra = 0


class IdentifierCrossrefStatusInline(admin.TabularInline):
    model = identifier_models.CrossrefStatus
    extra = 0
    filter_horizontal = ('deposits',)


class DepositCrossrefStatusInline(admin.TabularInline):
    model = identifier_models.CrossrefStatus.deposits.through
    extra = 0
    raw_id_fields = ('crossrefstatus',)


class AuthorReviewInline(admin.TabularInline):
    model = copyediting_models.AuthorReview
    exclude = ('files_updated',)
    extra = 0


class ArticleInline(admin.TabularInline):
    model = submission_models.Article
    extra = 0
    fields = ('title', 'correspondence_author', 'journal')
    readonly_fields = ('title', 'correspondence_author', 'journal')
    fk_name = 'primary_issue'


class FundersArticleInline(admin.TabularInline):
    model = submission_models.Article.funders.through
    extra = 0


class ArticleOrderingInline(admin.TabularInline):
    model = journal_models.ArticleOrdering
    extra = 0
    raw_id_fields = ('article', 'issue', 'section')


class CronTaskInline(admin.TabularInline):
    model = cron_models.CronTask
    extra = 0
    raw_id_fields = ('article',)


class IdentifierInline(admin.TabularInline):
    model = identifier_models.Identifier
    extra = 0
    raw_id_fields = ('article',)


class NoteInline(admin.TabularInline):
    model = submission_models.Note
    extra = 0
    raw_id_fields = ('article', 'creator')


class FieldAnswerInline(admin.TabularInline):
    model = submission_models.FieldAnswer
    extra = 0
    raw_id_fields = ('article',)


class ArticleStageLogInline(admin.TabularInline):
    model = submission_models.ArticleStageLog
    extra = 0


class KeywordArticleInline(admin.TabularInline):
    model = submission_models.KeywordArticle
    extra = 0
    raw_id_fields = ('article', 'keyword')


class GalleyInline(admin.TabularInline):
    model = core_models.Galley
    extra = 0
    fields = ('file', 'public', 'label', 'type', 'sequence')
    raw_id_fields = ('article', 'file', 'css_file',
                     'images', 'xsl_file')


class IssueGalleyInline(admin.TabularInline):
    model = journal_models.IssueGalley
    extra = 0
    raw_id_fields = ('file',)


class SectionOrderingInline(admin.TabularInline):
    model = journal_models.SectionOrdering
    extra = 0
    raw_id_fields = ('section', 'issue')


class PasswordResetInline(admin.TabularInline):
    model = core_models.PasswordResetToken
    extra = 0


class AccountRoleInline(admin.TabularInline):
    model = core_models.AccountRole
    extra = 0


class SettingInline(admin.TabularInline):
    model = core_models.Setting
    extra = 0


class SettingValueInline(admin.TabularInline):
    model = core_models.SettingValue
    extra = 0
    fields = ('journal', 'value')


class FileInline(admin.TabularInline):
    model = core_models.File
    extra = 0
    fields = ('journal', 'value')


class EditorialGroupMemberInline(admin.TabularInline):
    model = core_models.EditorialGroupMember
    extra = 0
    raw_id_fields = ('user',)


class StaffGroupMemberInline(admin.TabularInline):
    model = press_models.StaffGroupMember
    extra = 0
    exclude = ('alternate_title', 'publications')
    raw_id_fields = ('user',)


class WorkflowLogInline(admin.TabularInline):
    model = core_models.WorkflowLog
    extra = 0
    raw_id_fields = ('element', 'article',)


class RepositoryRoleInline(admin.TabularInline):
    model = repository_models.RepositoryRole
    extra = 0


class CommentInline(admin.TabularInline):
    model = repository_models.Comment
    extra = 0
    raw_id_fields = ('reply_to', 'preprint', 'author')
    ordering = ('date_time',)


class RepositoryFieldAnswerInline(admin.TabularInline):
    model = repository_models.RepositoryFieldAnswer
    extra = 0
    raw_id_fields = ('field', 'preprint',)


class PreprintVersionInline(admin.TabularInline):
    model = repository_models.PreprintVersion
    extra = 0
    raw_id_fields = ('preprint', 'file', 'moderated_version')
    exclude = ('abstract', 'published_doi')


class KeywordPreprintInline(admin.TabularInline):
    model = repository_models.KeywordPreprint
    extra = 0
    raw_id_fields = ('preprint', 'keyword')


class PreprintFileInline(admin.TabularInline):
    model = repository_models.PreprintFile
    extra = 0
    raw_id_fields = ('preprint',)


class PreprintSupplementaryFileInline(admin.TabularInline):
    model = repository_models.PreprintSupplementaryFile
    extra = 0
    raw_id_fields = ('preprint',)


class PreprintAuthorInline(admin.TabularInline):
    model = repository_models.PreprintAuthor
    extra = 0
    raw_id_fields = ('preprint', 'account')


class VersionQueueInline(admin.TabularInline):
    model = repository_models.VersionQueue
    extra = 0
    raw_id_fields = ('preprint', 'file')
    exclude = ('abstract', 'published_doi')


class RepositoryReviewInline(admin.TabularInline):
    model = repository_models.Review
    extra = 0
    raw_id_fields = ('preprint', 'manager', 'reviewer')
    fields = ('manager', 'reviewer', 'date_due',
              'date_accepted', 'date_completed', 'status')


class NewsItemInline(admin.TabularInline):
    model = comms_models.NewsItem.tags.through
    extra = 0
    raw_id_fields = ('newsitem',)


class JournalFilterBase(admin.SimpleListFilter):
    """
    A base class for other journal filters
    """

    title = 'journal'
    parameter_name = 'journal'

    def lookups(self, request, model_admin):
        return (
            (journal.id, journal)
            for journal in journal_models.Journal.objects.all()
        )


class ArticleIDJournalFilter(JournalFilterBase):
    """
    A journal filter for objects that just store article ids,
    like core.File.
    """
    def queryset(self, request, queryset):
        journal_pk = request.GET.get('journal', None)
        if not journal_pk:
            return queryset
        articles = submission_models.Article.objects.filter(
            journal__pk=journal_pk,
        )
        return queryset.filter(article_id__in=articles)


class FileArticleIDJournalFilter(JournalFilterBase):
    """
    A journal filter for objects related to files,
    like core.SupplementaryFile.
    """
    def queryset(self, request, queryset):
        journal_pk = request.GET.get('journal', None)
        if not journal_pk:
            return queryset
        articles = submission_models.Article.objects.filter(
            journal__pk=journal_pk,
        )
        return queryset.filter(file__article_id__in=articles)


class SentReminderJournalFilter(JournalFilterBase):
    """
    A journal filter for SentReminder, which stores object IDs and types.
    """
    def queryset(self, request, queryset):
        journal_pk = request.GET.get('journal', None)
        if not journal_pk or not queryset:
            return queryset
        if queryset.first().type == 'review':
            model = review_models.ReviewAssignment
        elif queryset.first().type == 'accepted-review':
            model = review_models.ReviewAssignment
        elif queryset.first().type == 'revisions':
            model = review_models.RevisionRequest
        else:
            return queryset

        objects = model.objects.filter(
            article__journal__pk=journal_pk,
        )
        return queryset.filter(object_id__in=objects)


class GenericRelationJournalFilter(JournalFilterBase):
    """
    A journal list filter for objects that are connected to
    the journal by a Generic Foreign Key.
    An example is cms.NavigationItem.
    """
    def queryset(self, request, queryset):
        journal_pk = request.GET.get('journal', None)
        if not journal_pk:
            return queryset
        journal = journal_models.Journal.objects.get(id=journal_pk)
        content_type = ContentType.objects.get_for_model(journal)
        return queryset.filter(
            object_id=journal_pk,
            content_type=content_type,
        )


class GenericRelationPressFilter(admin.SimpleListFilter):
    """
    Provides a press list filter for objects that are connected to
    the press by a Generic Foreign Key.
    An example is cms.NavigationItem.
    """

    title = 'press'
    parameter_name = 'press'

    def lookups(self, request, model_admin):
        return (
            (press.id, press.name)
            for press in press_models.Press.objects.all()
        )

    def queryset(self, request, queryset):
        press_pk = request.GET.get('press', None)
        if not press_pk:
            return queryset
        press = press_models.Press.objects.get(id=press_pk)
        content_type = ContentType.objects.get_for_model(press)
        return queryset.filter(
            object_id=press_pk,
            content_type=content_type,
        )


class GenericRelationArticleJournalFilter(JournalFilterBase):
    """
    Provides a journal list filter for objects that are separated from the
    journal by a Generic Foreign Key and an article-journal relationship.
    An example is utils.LogEntry.
    """

    def queryset(self, request, queryset):
        journal_pk = request.GET.get('journal', None)
        if not journal_pk:
            return queryset
        articles = submission_models.Article.objects.filter(
            journal__id=journal_pk
        )
        if not articles:
            return queryset.none()
        content_type = ContentType.objects.get_for_model(articles.first())
        return queryset.filter(
            object_id__in=[article.pk for article in articles],
            content_type=content_type,
        )


class GenericRelationPreprintRepositoryFilter(admin.SimpleListFilter):
    """
    Provides a repository list filter for objects that are separated from the
    repository by a Generic Foreign Key and a preprint-repository relationship.
    An example is utils.LogEntry.
    """

    title = 'repository'
    parameter_name = 'repository'

    def lookups(self, request, model_admin):
        return (
            (repository.id, repository.short_name)
            for repository in repository_models.Repository.objects.all()
        )

    def queryset(self, request, queryset):
        repo_pk = request.GET.get('repository', None)
        if not repo_pk:
            return queryset
        preprints = repository_models.Preprint.objects.filter(
            repository__id=repo_pk
        )
        if not preprints:
            return queryset.none()
        content_type = ContentType.objects.get_for_model(preprints.first())
        return queryset.filter(
            object_id__in=[preprint.pk for preprint in preprints],
            content_type=content_type,
        )
