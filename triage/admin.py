from django.contrib import admin

from .models import (
    TriageFlow,
    TriageOption,
    TriageOptionTransition,
    TriageQuestion,
    TriageSession,
    TriageSessionAnswer,
)


class TriageOptionInline(admin.TabularInline):
    model = TriageOption
    extra = 0


@admin.register(TriageFlow)
class TriageFlowAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'version', 'is_active', 'created_at')
    search_fields = ('name', 'code')


@admin.register(TriageQuestion)
class TriageQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'flow', 'category', 'display_order', 'is_start_question', 'is_active')
    list_filter = ('flow', 'category', 'is_start_question', 'is_active')
    search_fields = ('code', 'text')
    inlines = [TriageOptionInline]


@admin.register(TriageOption)
class TriageOptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'label', 'question', 'flag_effect', 'option_order', 'is_active')
    list_filter = ('flag_effect', 'is_active')
    search_fields = ('label', 'code', 'question__code')


@admin.register(TriageOptionTransition)
class TriageOptionTransitionAdmin(admin.ModelAdmin):
    list_display = ('id', 'option', 'next_question', 'end_flag')
    list_filter = ('end_flag',)
    search_fields = ('option__label', 'option__code', 'next_question__code')


class TriageSessionAnswerInline(admin.TabularInline):
    model = TriageSessionAnswer
    extra = 0
    readonly_fields = (
        'answer_order',
        'question',
        'option',
        'question_text_snapshot',
        'option_label_snapshot',
        'option_flag_snapshot',
        'answered_at',
    )


@admin.register(TriageSession)
class TriageSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'family_member', 'flow', 'status', 'final_flag', 'started_at', 'completed_at')
    list_filter = ('status', 'final_flag', 'flow')
    search_fields = ('user__username', 'user__phone_number', 'family_member__name', 'flow__code')
    readonly_fields = ('started_at', 'updated_at', 'completed_at')
    inlines = [TriageSessionAnswerInline]
