__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.db import models
from django.utils import timezone

from events import logic as event_logic
from utils import setting_handler
from submission import models as submission_models


class ProofingAssignment(models.Model):
    article = models.OneToOneField(
        'submission.Article',
        on_delete=models.CASCADE,
    )
    proofing_manager = models.ForeignKey('core.Account', null=True, on_delete=models.SET_NULL)
    editor = models.ForeignKey(
        'core.Account',
        null=True,
        related_name='proofing_editor',
        on_delete=models.SET_NULL,
    )
    assigned = models.DateTimeField(default=timezone.now)
    notified = models.BooleanField(default=False)
    completed = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('article', 'proofing_manager')

    @property
    def current_proofing_round_number(self):
        try:
            return self.proofinground_set.all().order_by('-number')[0].number
        except IndexError:
            return 0

    def current_proofing_round(self):
        try:
            return self.proofinground_set.all().order_by('-number')[0]
        except IndexError:
            return None

    def add_new_proofing_round(self):
        new_round_number = self.current_proofing_round_number + 1
        return ProofingRound.objects.create(assignment=self,
                                            number=new_round_number)

    def user_is_manager(self, user):
        if user == self.proofing_manager:
            return True
        return False

    def __str__(self):
        return 'Proofing Assignment {pk}'.format(pk=self.pk)


class ProofingRound(models.Model):
    assignment = models.ForeignKey(
        ProofingAssignment,
        on_delete=models.CASCADE,
    )
    number = models.PositiveIntegerField(default=1)
    date_started = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ('-number',)

    def __str__(self):
        return "Round #{0} for Article {1}".format(self.number, self.assignment.article.title)

    @property
    def has_active_tasks(self):
        if self.proofingtask_set.filter(completed__isnull=True):
            return True
        else:
            return False

    @property
    def active_proofreaders(self):
        return [task.proofreader for task in self.proofingtask_set.all()]

    @property
    def typeset_tasks(self):
        typeset_tasks = list()
        for p_task in self.proofingtask_set.all():
            for t_task in p_task.typesetterproofingtask_set.all():
                typeset_tasks.append(t_task)

        return typeset_tasks

    def delete_round_relations(self, request, article, tasks, corrections):

        for task in tasks:
            if not task.completed:
                kwargs = {
                    'article': article,
                    'proofing_task': task,
                    'request': request,
                }
                event_logic.Events.raise_event(
                    event_logic.Events.ON_CANCEL_PROOFING_TASK,
                    task_object=article,
                    **kwargs,
                )
                task.delete()

        for correction in corrections:
            if not correction.completed and not correction.cancelled:
                kwargs = {
                    'article': article,
                    'correction': correction,
                    'request': request,
                }
                event_logic.Events.raise_event(
                    event_logic.Events.ON_CORRECTIONS_CANCELLED,
                    task_object=article,
                    **kwargs,
                )
                correction.delete()

    def can_add_another_proofreader(self, journal):
        """
        Checks if this round can have another proofreader.
        :param journal: Journal object
        :return: Boolean, True or False
        """

        limit = setting_handler.get_setting(
            'general',
            'max_proofreaders',
            journal,
        ).processed_value

        if not limit == 0:

            current_num_proofers = ProofingTask.objects.filter(
                round=self,
            ).count()

            if current_num_proofers >= limit:
                return False

        return True


class ActiveProofingTaskManager(models.Manager):
    def get_queryset(self):
        return super(ActiveProofingTaskManager, self).get_queryset().exclude(
            round__assignment__article__stage=submission_models.STAGE_ARCHIVED,
        )


class ProofingTask(models.Model):
    round = models.ForeignKey(ProofingRound, on_delete=models.CASCADE,)
    proofreader = models.ForeignKey('core.Account', null=True, on_delete=models.SET_NULL)
    assigned = models.DateTimeField(default=timezone.now)
    notified = models.BooleanField(default=False)
    due = models.DateTimeField(default=None, verbose_name="Date Due")
    accepted = models.DateTimeField(blank=True, null=True)
    completed = models.DateTimeField(blank=True, null=True)
    cancelled = models.BooleanField(default=False)
    acknowledged = models.DateTimeField(blank=True, null=True)

    task = models.TextField(verbose_name="Proofing Task")
    galleys_for_proofing = models.ManyToManyField('core.Galley')
    proofed_files = models.ManyToManyField('core.File')
    notes = models.ManyToManyField('proofing.Note')

    objects = models.Manager()
    active_objects = ActiveProofingTaskManager()

    def __str__(self):
        return "{0} proofing {1} in round {2}".format(self.proofreader.full_name(),
                                                      self.round.assignment.article.title,
                                                      self.round.number)

    @property
    def assignment(self):
        return self.round.assignment

    def typesetter_tasks(self):
        return self.typesetterproofingtask_set.all()

    def status(self):
        if self.cancelled:
            return {'slug': 'cancelled', 'friendly': 'Task cancelled'}
        elif self.assigned and not self.accepted and not self.completed:
            return {'slug': 'assigned', 'friendly': 'Awaiting response'}
        elif self.assigned and self.accepted and not self.completed:
            return {'slug': 'accepted', 'friendly': 'Task accepted, underway'}
        elif self.assigned and not self.accepted and self.completed:
            return {'slug': 'declined', 'friendly': 'Task declined'}
        elif self.completed:
            return {'slug': 'completed', 'friendly': 'Task completed'}

    def galley_files(self):
        return [galley.file for galley in self.galleys_for_proofing.all()]

    def actor(self):
        return self.proofreader

    def review_comments(self):
        comment_text = ''
        for note in self.notes.all().order_by('galley'):
            comment_text = comment_text + "Comment by: {0} for Galley {1}<br>{2}<br>".format(note.creator.full_name(),
                                                                                             note.galley,
                                                                                             note.text)

        return comment_text

    def reset(self):
        self.completed = None
        self.cancelled = False
        self.accepted = None
        self.save()


class ActiveTypesetterProofingTaskManager(models.Manager):
    def get_queryset(self):
        return super(ActiveTypesetterProofingTaskManager, self).get_queryset().exclude(
            proofing_task__round__assignment__article__stage=submission_models.STAGE_ARCHIVED,
        )


class TypesetterProofingTask(models.Model):
    proofing_task = models.ForeignKey(ProofingTask, on_delete=models.CASCADE)
    typesetter = models.ForeignKey('core.Account', null=True, on_delete=models.SET_NULL)
    assigned = models.DateTimeField(default=timezone.now)
    notified = models.BooleanField(default=False)
    due = models.DateTimeField(blank=True, null=True)
    accepted = models.DateTimeField(blank=True, null=True)
    completed = models.DateTimeField(blank=True, null=True)
    cancelled = models.BooleanField(default=False)
    acknowledged = models.DateTimeField(blank=True, null=True)

    task = models.TextField(verbose_name="Typesetter Task")
    galleys = models.ManyToManyField('core.Galley')
    files = models.ManyToManyField('core.File')
    notes = models.TextField(verbose_name="Correction Note", blank=True, null=True)

    objects = models.Manager()
    active_objects = ActiveTypesetterProofingTaskManager()

    class Meta:
        verbose_name = 'Correction Task'

    def __str__(self):
        return "Correction Task Proof ID: {0}, Proofreader {1}, Due: {2}".format(self.proofing_task.pk,
                                                                                 self.typesetter.full_name(),
                                                                                 self.due)

    def status(self):
        if self.cancelled:
            return {'slug': 'cancelled', 'friendly': 'Cancelled'}
        elif self.assigned and not self.accepted and not self.completed:
            return {'slug': 'assigned', 'friendly': 'Awaiting response'}
        elif self.assigned and self.accepted and not self.completed:
            return {'slug': 'accepted', 'friendly': 'Underway'}
        elif self.assigned and not self.accepted and self.completed:
            return {'slug': 'declined', 'friendly': 'Declined'}
        elif self.completed:
            return {'slug': 'completed', 'friendly': 'Completed'}

    def actor(self):
        return self.typesetter


class Note(models.Model):
    galley = models.ForeignKey('core.Galley', on_delete=models.CASCADE)
    creator = models.ForeignKey('core.Account', related_name='proofing_note_creator',
                                null=True, on_delete=models.SET_NULL)
    text = models.TextField()
    date_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date_time',)

    def __str__(self):
        return "{0} - {1} {2}".format(self.pk, self.creator.full_name(), self.galley)
