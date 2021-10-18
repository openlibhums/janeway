from django import forms
from django.contrib import messages
from django.utils import timezone
from django.contrib.admin.widgets import FilteredSelectMultiple

from core.homepage_elements.carousel import models
from journal import models as journal_models
from submission import models as submission_models
from comms import models as comms_models


class CarouselForm(forms.ModelForm):
    """
    A form that modifies carousel settings for a journal.
    """

    carousel_article_limit = forms.IntegerField(
        required=True,
        label='Maximum number of articles to show',
    )
    carousel_news_limit = forms.IntegerField(
        required=True,
        label='Maximum number of news items to show',
    )
    carousel_latest_articles = forms.BooleanField(
        required=False,
        label='Display the latest published articles',
    )
    carousel_articles = forms.ModelMultipleChoiceField(
        queryset=submission_models.Article.objects.none(),
        required=False,
        widget=FilteredSelectMultiple("Article", False, attrs={'rows': '2'})
    )
    carousel_latest_news = forms.BooleanField(
        required=False,
        label='Display the latest news items',
    )
    carousel_news = forms.ModelMultipleChoiceField(
        queryset=comms_models.NewsItem.objects.none(),
        required=False,
        widget=FilteredSelectMultiple(
            "News Article",
            False,
            attrs={'rows': '2'},
        )
    )
    carousel_current_issue = forms.BooleanField(
        required=False,
        label='Display the current issue',
    )
    carousel_issues = forms.ModelMultipleChoiceField(
        queryset=journal_models.Issue.objects.none(),
        required=False,
        widget=FilteredSelectMultiple("Issue", False, attrs={'rows': '2'})
    )

    class Meta:
        model = models.Carousel
        fields = ('latest_articles', 'latest_news', 'exclude', 'current_issue')


    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)

        article_list, news_list, issues_list = self.load(request)

        super(CarouselForm, self).__init__(*args, **kwargs)

        if request.site_type and request.site_type.carousel is not None:
            self.initial['carousel_articles'] = article_list
            self.initial['carousel_article_limit'] = request.site_type.carousel.article_limit
            self.initial['carousel_news_limit'] = request.site_type.carousel.news_limit
            self.initial['carousel_news'] = news_list
            self.initial['carousel_issues'] = issues_list

        published_articles = submission_models.Article.objects.filter(
            stage=submission_models.STAGE_PUBLISHED,
            date_published__lte=timezone.now()
        )

        if request.journal:
            published_articles = published_articles.filter(
                journal=request.journal
            )

        self.fields['carousel_articles'].queryset = published_articles

        news_items = comms_models.NewsItem.objects.filter(
            content_type=request.model_content_type,
            object_id=request.site_type.pk,
        )

        self.fields['carousel_news'].queryset = news_items
        self.fields['carousel_issues'].queryset = request.site_type.issues

    def load(self, request):
        # if no carousel set, create one
        if request.site_type and request.site_type.carousel is None:
            return (
                [],
                submission_models.Article.objects.none(),
                journal_models.Issue.objects.none(),
            )

        articles = request.site_type.carousel.articles.all()
        article_list = []
        news_list = []

        for article in articles:
            article_list.append(article.pk)

        for item in request.site_type.carousel.news_articles.all():
            news_list.append(item.pk)

        issues_list = list(
            request.site_type.carousel.issues.values_list("id", flat=True)
        )

        return article_list, news_list, issues_list

    def save(self, request, commit=True):
        instance = super().save(commit=True)
        article_limit = self.cleaned_data["carousel_article_limit"]
        news_limit = self.cleaned_data["carousel_news_limit"]
        list_of_articles = self.cleaned_data["carousel_articles"]
        list_of_news = self.cleaned_data["carousel_news"]
        list_of_issues = self.cleaned_data["carousel_issues"]

        instance.article_limit = article_limit
        instance.news_limit = news_limit

        instance.articles.clear()
        instance.news_articles.clear()
        instance.issues.clear()

        for article in list_of_articles:
            instance.articles.add(article)

        for news in list_of_news:
            instance.news_articles.add(news)

        for issue in list_of_issues:
            instance.issues.add(issue)

        if commit:
            instance.save()
            super().save(commit=commit)

        if request.site_type.carousel is None and commit:
            request.site_type.carousel = instance
            request.site_type.save()

        messages.add_message(
            request,
            messages.SUCCESS,
            'Journal carousel settings saved',
        )

