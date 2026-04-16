from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from accounts.models import FamilyMember

from .models import (
    FlagChoices,
    SessionStatusChoices,
    TriageFlow,
    TriageOption,
    TriageOptionTransition,
    TriageQuestion,
    TriageSession,
    TriageSessionAnswer,
)


class TriageOptionTransitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriageOptionTransition
        fields = (
            'id',
            'option',
            'next_question',
            'end_flag',
            'end_message',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate(self, attrs):
        option = attrs.get('option') or self.instance.option
        next_question = attrs.get('next_question', getattr(self.instance, 'next_question', None))
        end_flag = attrs.get('end_flag', getattr(self.instance, 'end_flag', None))

        if not next_question and not end_flag:
            raise serializers.ValidationError('Transition must define a next question or an end flag.')
        if end_flag == FlagChoices.NONE:
            raise serializers.ValidationError({'end_flag': 'End flag cannot be NONE.'})
        if next_question and next_question.flow_id != option.question.flow_id:
            raise serializers.ValidationError({'next_question': 'Next question must be in the same flow.'})
        return attrs


class TriageOptionSerializer(serializers.ModelSerializer):
    transition = TriageOptionTransitionSerializer(read_only=True)

    class Meta:
        model = TriageOption
        fields = (
            'id',
            'question',
            'code',
            'label',
            'option_order',
            'flag_effect',
            'is_active',
            'transition',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'transition', 'created_at', 'updated_at')


class TriageQuestionSerializer(serializers.ModelSerializer):
    options = TriageOptionSerializer(many=True, read_only=True)

    class Meta:
        model = TriageQuestion
        fields = (
            'id',
            'flow',
            'code',
            'text',
            'category',
            'help_text',
            'display_order',
            'is_start_question',
            'is_active',
            'options',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'options', 'created_at', 'updated_at')

    def validate(self, attrs):
        flow = attrs.get('flow') or getattr(self.instance, 'flow', None)
        is_start = attrs.get('is_start_question', getattr(self.instance, 'is_start_question', False))

        if flow and is_start:
            qs = TriageQuestion.objects.filter(flow=flow, is_start_question=True)
            if self.instance:
                qs = qs.exclude(id=self.instance.id)
            if qs.exists():
                raise serializers.ValidationError({'is_start_question': 'Only one start question is allowed per flow.'})

        return attrs


class TriageFlowSerializer(serializers.ModelSerializer):
    questions = TriageQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = TriageFlow
        fields = (
            'id',
            'name',
            'code',
            'description',
            'version',
            'is_active',
            'questions',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'questions', 'created_at', 'updated_at')


class TriageQuestionCardSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()

    class Meta:
        model = TriageQuestion
        fields = ('id', 'code', 'text', 'category', 'help_text', 'display_order', 'options')

    def get_options(self, obj):
        options = obj.options.filter(is_active=True).order_by('option_order', 'id')
        return [
            {
                'id': option.id,
                'code': option.code,
                'label': option.label,
                'flag_effect': option.flag_effect,
            }
            for option in options
        ]


class TriageSessionAnswerSerializer(serializers.ModelSerializer):
    question_code = serializers.CharField(source='question.code', read_only=True)
    option_code = serializers.CharField(source='option.code', read_only=True)

    class Meta:
        model = TriageSessionAnswer
        fields = (
            'id',
            'answer_order',
            'question',
            'question_code',
            'question_text_snapshot',
            'option',
            'option_code',
            'option_label_snapshot',
            'option_flag_snapshot',
            'answered_at',
        )
        read_only_fields = fields


class TriageSessionSerializer(serializers.ModelSerializer):
    current_question = TriageQuestionCardSerializer(read_only=True)
    answers = TriageSessionAnswerSerializer(many=True, read_only=True)
    flow_name = serializers.CharField(source='flow.name', read_only=True)
    patient_name = serializers.SerializerMethodField()
    family_member_name = serializers.CharField(source='family_member.name', read_only=True)

    class Meta:
        model = TriageSession
        fields = (
            'id',
            'user',
            'family_member',
            'family_member_name',
            'patient_name',
            'flow',
            'flow_name',
            'current_question',
            'status',
            'final_flag',
            'final_message',
            'started_at',
            'completed_at',
            'updated_at',
            'answers',
        )
        read_only_fields = fields

    def get_patient_name(self, obj):
        if obj.family_member:
            return obj.family_member.name
        full_name = f'{obj.user.first_name} {obj.user.last_name}'.strip()
        return full_name or obj.user.username


class TriageSessionStartSerializer(serializers.Serializer):
    flow_id = serializers.PrimaryKeyRelatedField(queryset=TriageFlow.objects.filter(is_active=True), source='flow')
    family_member_id = serializers.PrimaryKeyRelatedField(
        queryset=FamilyMember.objects.all(),
        source='family_member',
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        family_member = attrs.get('family_member')
        user = self.context['request'].user
        if family_member and family_member.user_id != user.id:
            raise serializers.ValidationError({'family_member_id': 'Family member does not belong to the logged-in user.'})
        return attrs

    def _get_start_question(self, flow: TriageFlow):
        question = flow.questions.filter(is_active=True, is_start_question=True).order_by('display_order', 'id').first()
        if question:
            return question
        return flow.questions.filter(is_active=True).order_by('display_order', 'id').first()

    def create(self, validated_data):
        flow = validated_data['flow']
        start_question = self._get_start_question(flow)
        if not start_question:
            raise serializers.ValidationError({'flow_id': 'This flow has no active questions.'})

        return TriageSession.objects.create(
            user=self.context['request'].user,
            family_member=validated_data.get('family_member'),
            flow=flow,
            current_question=start_question,
        )


class TriageSessionAnswerCreateSerializer(serializers.Serializer):
    option_id = serializers.PrimaryKeyRelatedField(queryset=TriageOption.objects.filter(is_active=True), source='option')

    def validate(self, attrs):
        session: TriageSession = self.context['session']
        option: TriageOption = attrs['option']

        if session.status != SessionStatusChoices.IN_PROGRESS:
            raise serializers.ValidationError('This triage session is already completed.')
        if not session.current_question:
            raise serializers.ValidationError('This session does not have an active current question.')
        if option.question_id != session.current_question_id:
            raise serializers.ValidationError({'option_id': 'Selected option does not belong to the current question.'})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        session: TriageSession = self.context['session']
        option: TriageOption = validated_data['option']
        question = session.current_question
        transition = getattr(option, 'transition', None)

        final_flag = None
        final_message = ''
        next_question = None

        if transition:
            final_flag = transition.end_flag
            final_message = transition.end_message
            next_question = transition.next_question if transition.next_question and transition.next_question.is_active else None
        elif option.flag_effect != FlagChoices.NONE:
            final_flag = option.flag_effect

        if not next_question and not final_flag:
            raise serializers.ValidationError({'option_id': 'This option does not have a next question or final flag configured.'})

        answer_order = session.answers.count() + 1
        TriageSessionAnswer.objects.create(
            session=session,
            question=question,
            option=option,
            answer_order=answer_order,
            question_text_snapshot=question.text,
            option_label_snapshot=option.label,
            option_flag_snapshot=final_flag or (option.flag_effect if option.flag_effect != FlagChoices.NONE else None),
        )

        if final_flag:
            session.status = SessionStatusChoices.COMPLETED
            session.final_flag = final_flag
            session.final_message = final_message
            session.current_question = None
            session.completed_at = timezone.now()
        else:
            session.current_question = next_question

        session.save(
            update_fields=[
                'status',
                'final_flag',
                'final_message',
                'current_question',
                'completed_at',
                'updated_at',
            ]
        )
        return session
