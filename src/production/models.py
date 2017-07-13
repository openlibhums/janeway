__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.db import models
from django.utils import timezone


class ProductionAssignment(models.Model):
    article = models.OneToOneField('submission.Article')
    production_manager = models.ForeignKey('core.Account', null=True, on_delete=models.SET_NULL)
    editor = models.ForeignKey('core.Account', null=True, on_delete=models.SET_NULL, related_name='prod_editor')
    assigned = models.DateTimeField(default=timezone.now)
    notified = models.BooleanField(default=False)
    closed = models.DateField(blank=True, null=True)

    accepted_by_manager = models.ForeignKey('TypesetTask', null=True, blank=True)

    class Meta:
        unique_together = ('article', 'production_manager')

    def typeset_tasks(self):
        return self.typesettask_set.all()

    def active_typeset_tasks(self):
        return self.typesettask_set.filter(completed__isnull=True)

    def completed_typeset_tasks(self):
        return self.typesettask_set.filter(completed__isnull=False)


class TypesetTask(models.Model):
    assignment = models.ForeignKey(ProductionAssignment)
    typesetter = models.ForeignKey('core.Account', null=True, on_delete=models.SET_NULL)
    assigned = models.DateTimeField(default=timezone.now)
    notified = models.BooleanField(default=False)
    accepted = models.DateTimeField(blank=True, null=True)

    typeset_task = models.TextField(blank=True, null=True, verbose_name="Typesetting Task")
    files_for_typesetting = models.ManyToManyField('core.File', related_name='files_for_typesetting')
    galleys_loaded = models.ManyToManyField('core.File', related_name='galleys_loaded')
    note_from_typesetter = models.TextField(blank=True, null=True, verbose_name='Note to Editor')
    completed = models.DateTimeField(blank=True, null=True)

    editor_reviewed = models.BooleanField(default=False)

    @property
    def is_active(self):
        if self.assigned and not self.completed:
            return True
        else:
            return False

    def status(self):
        if self.assigned and not self.accepted and not self.completed:
            return {'slug': 'assigned', 'friendly': 'Awaiting response'}
        elif self.assigned and self.accepted and not self.completed:
            return {'slug': 'accepted', 'friendly': 'Task accepted, underway'}
        elif self.assigned and not self.accepted and self.completed:
            return {'slug': 'declined', 'friendly': 'Task declined'}
        elif self.completed and not self.editor_reviewed:
            return {'slug': 'completed', 'friendly': 'Completed on {0}<br/>Awaiting manager review'.format(
                self.completed.strftime("%Y-%m-%d %H:%M"))}
        elif self.completed and self.editor_reviewed:
            return {'slug': 'closed', 'friendly': 'Task closed'}
