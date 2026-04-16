from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from accounts.models import FamilyMember


class FlagChoices(models.TextChoices):
    NONE = 'NONE', 'None'
    GREEN = 'GREEN', 'Green'
    YELLOW = 'YELLOW', 'Yellow'
    RED = 'RED', 'Red'


class SessionStatusChoices(models.TextChoices):
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'


class TriageFlow(models.Model):
    name = models.CharField(max_length=150)
    code = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name', 'version', 'id')

    def __str__(self) -> str:
        return f'{self.name} v{self.version}'


class TriageQuestion(models.Model):
    flow = models.ForeignKey(TriageFlow, on_delete=models.CASCADE, related_name='questions')
    code = models.SlugField(max_length=100)
    text = models.TextField()
    category = models.CharField(max_length=100, blank=True)
    help_text = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_start_question = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('display_order', 'id')
        constraints = [
            models.UniqueConstraint(fields=('flow', 'code'), name='unique_question_code_per_flow'),
        ]

    def __str__(self) -> str:
        return f'{self.flow.code}: {self.code}'


class TriageOption(models.Model):
    question = models.ForeignKey(TriageQuestion, on_delete=models.CASCADE, related_name='options')
    code = models.SlugField(max_length=100)
    label = models.CharField(max_length=255)
    option_order = models.PositiveIntegerField(default=0)
    flag_effect = models.CharField(max_length=10, choices=FlagChoices.choices, default=FlagChoices.NONE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('option_order', 'id')
        constraints = [
            models.UniqueConstraint(fields=('question', 'code'), name='unique_option_code_per_question'),
        ]

    def __str__(self) -> str:
        return f'{self.question.code}: {self.label}'


class TriageOptionTransition(models.Model):
    option = models.OneToOneField(TriageOption, on_delete=models.CASCADE, related_name='transition')
    next_question = models.ForeignKey(
        TriageQuestion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incoming_transitions',
    )
    end_flag = models.CharField(max_length=10, choices=FlagChoices.choices, blank=True, null=True)
    end_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('id',)

    def clean(self):
        if not self.next_question and not self.end_flag:
            raise ValidationError('Transition must define a next question or an end flag.')
        if self.end_flag == FlagChoices.NONE:
            raise ValidationError({'end_flag': 'End flag cannot be NONE.'})
        if self.next_question and self.next_question.flow_id != self.option.question.flow_id:
            raise ValidationError({'next_question': 'Next question must belong to the same flow.'})

    def __str__(self) -> str:
        if self.next_question:
            return f'{self.option} -> {self.next_question.code}'
        return f'{self.option} -> {self.end_flag}'


class TriageSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='triage_sessions')
    family_member = models.ForeignKey(
        FamilyMember,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='triage_sessions',
    )
    flow = models.ForeignKey(TriageFlow, on_delete=models.PROTECT, related_name='sessions')
    current_question = models.ForeignKey(
        TriageQuestion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='active_sessions',
    )
    status = models.CharField(max_length=20, choices=SessionStatusChoices.choices, default=SessionStatusChoices.IN_PROGRESS)
    final_flag = models.CharField(max_length=10, choices=FlagChoices.choices, blank=True, null=True)
    final_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-started_at', '-id')

    def clean(self):
        if self.family_member and self.family_member.user_id != self.user_id:
            raise ValidationError({'family_member': 'Family member must belong to the same user.'})
        if self.current_question and self.current_question.flow_id != self.flow_id:
            raise ValidationError({'current_question': 'Current question must belong to the selected flow.'})

    def __str__(self) -> str:
        return f'Session #{self.pk} - {self.flow.code}'


class TriageSessionAnswer(models.Model):
    session = models.ForeignKey(TriageSession, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(TriageQuestion, on_delete=models.PROTECT, related_name='session_answers')
    option = models.ForeignKey(TriageOption, on_delete=models.PROTECT, related_name='session_answers')
    answer_order = models.PositiveIntegerField()
    question_text_snapshot = models.TextField()
    option_label_snapshot = models.CharField(max_length=255)
    option_flag_snapshot = models.CharField(max_length=10, choices=FlagChoices.choices, blank=True, null=True)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('answer_order', 'id')
        constraints = [
            models.UniqueConstraint(fields=('session', 'question'), name='unique_question_per_session'),
            models.UniqueConstraint(fields=('session', 'answer_order'), name='unique_answer_order_per_session'),
        ]

    def clean(self):
        if self.question.flow_id != self.session.flow_id:
            raise ValidationError({'question': 'Question must belong to the same flow as the session.'})
        if self.option.question_id != self.question_id:
            raise ValidationError({'option': 'Option must belong to the selected question.'})

    def __str__(self) -> str:
        return f'Session #{self.session_id} - {self.question.code}'
