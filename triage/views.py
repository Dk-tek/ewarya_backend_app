from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import TriageFlow, TriageOption, TriageOptionTransition, TriageQuestion, TriageSession
from .serializers import (
    TriageFlowSerializer,
    TriageOptionSerializer,
    TriageOptionTransitionSerializer,
    TriageQuestionSerializer,
    TriageSessionAnswerCreateSerializer,
    TriageSessionSerializer,
    TriageSessionStartSerializer,
)


class TriageFlowView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        flows = TriageFlow.objects.prefetch_related('questions__options__transition').all().order_by('name', 'version')
        serializer = TriageFlowSerializer(flows, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = TriageFlowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Triage flow created successfully.', 'flow': serializer.data}, status=status.HTTP_201_CREATED)


class TriageFlowDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, flow_id):
        try:
            return TriageFlow.objects.prefetch_related('questions__options__transition').get(id=flow_id)
        except TriageFlow.DoesNotExist:
            return None

    def get(self, request, flow_id):
        flow = self.get_object(flow_id)
        if not flow:
            return Response({'detail': 'Triage flow not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(TriageFlowSerializer(flow).data, status=status.HTTP_200_OK)

    def patch(self, request, flow_id):
        flow = self.get_object(flow_id)
        if not flow:
            return Response({'detail': 'Triage flow not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = TriageFlowSerializer(flow, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Triage flow updated successfully.', 'flow': serializer.data}, status=status.HTTP_200_OK)


class TriageQuestionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        flow_id = request.query_params.get('flow_id')
        questions = TriageQuestion.objects.prefetch_related('options__transition').all().order_by('flow_id', 'display_order', 'id')
        if flow_id:
            questions = questions.filter(flow_id=flow_id)
        return Response(TriageQuestionSerializer(questions, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = TriageQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Triage question created successfully.', 'question': serializer.data}, status=status.HTTP_201_CREATED)


class TriageQuestionDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, question_id):
        try:
            return TriageQuestion.objects.prefetch_related('options__transition').get(id=question_id)
        except TriageQuestion.DoesNotExist:
            return None

    def get(self, request, question_id):
        question = self.get_object(question_id)
        if not question:
            return Response({'detail': 'Triage question not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(TriageQuestionSerializer(question).data, status=status.HTTP_200_OK)

    def patch(self, request, question_id):
        question = self.get_object(question_id)
        if not question:
            return Response({'detail': 'Triage question not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = TriageQuestionSerializer(question, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Triage question updated successfully.', 'question': serializer.data}, status=status.HTTP_200_OK)


class TriageOptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        question_id = request.query_params.get('question_id')
        options = TriageOption.objects.select_related('question').prefetch_related('transition').all().order_by('question_id', 'option_order', 'id')
        if question_id:
            options = options.filter(question_id=question_id)
        return Response(TriageOptionSerializer(options, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = TriageOptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Triage option created successfully.', 'option': serializer.data}, status=status.HTTP_201_CREATED)


class TriageOptionDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, option_id):
        try:
            return TriageOption.objects.select_related('question').prefetch_related('transition').get(id=option_id)
        except TriageOption.DoesNotExist:
            return None

    def get(self, request, option_id):
        option = self.get_object(option_id)
        if not option:
            return Response({'detail': 'Triage option not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(TriageOptionSerializer(option).data, status=status.HTTP_200_OK)

    def patch(self, request, option_id):
        option = self.get_object(option_id)
        if not option:
            return Response({'detail': 'Triage option not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = TriageOptionSerializer(option, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Triage option updated successfully.', 'option': serializer.data}, status=status.HTTP_200_OK)


class TriageOptionTransitionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        option_id = request.query_params.get('option_id')
        transitions = TriageOptionTransition.objects.select_related('option', 'next_question').all().order_by('id')
        if option_id:
            transitions = transitions.filter(option_id=option_id)
        return Response(TriageOptionTransitionSerializer(transitions, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = TriageOptionTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Triage transition created successfully.', 'transition': serializer.data}, status=status.HTTP_201_CREATED)


class TriageOptionTransitionDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, transition_id):
        try:
            return TriageOptionTransition.objects.select_related('option', 'next_question').get(id=transition_id)
        except TriageOptionTransition.DoesNotExist:
            return None

    def get(self, request, transition_id):
        transition = self.get_object(transition_id)
        if not transition:
            return Response({'detail': 'Triage transition not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(TriageOptionTransitionSerializer(transition).data, status=status.HTTP_200_OK)

    def patch(self, request, transition_id):
        transition = self.get_object(transition_id)
        if not transition:
            return Response({'detail': 'Triage transition not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = TriageOptionTransitionSerializer(transition, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Triage transition updated successfully.', 'transition': serializer.data}, status=status.HTTP_200_OK)


class TriageSessionStartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = TriageSessionStartSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        session = serializer.save()
        return Response({'message': 'Triage session started successfully.', 'session': TriageSessionSerializer(session).data}, status=status.HTTP_201_CREATED)


class TriageSessionListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        sessions = (
            TriageSession.objects.filter(user=request.user)
            .select_related('flow', 'family_member', 'current_question')
            .prefetch_related('answers__question', 'answers__option', 'current_question__options')
        )
        status_filter = request.query_params.get('status')
        if status_filter:
            sessions = sessions.filter(status=status_filter)
        return Response(TriageSessionSerializer(sessions, many=True).data, status=status.HTTP_200_OK)


class TriageSessionDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, session_id):
        try:
            return (
                TriageSession.objects.filter(user=request.user)
                .select_related('flow', 'family_member', 'current_question')
                .prefetch_related('answers__question', 'answers__option', 'current_question__options')
                .get(id=session_id)
            )
        except TriageSession.DoesNotExist:
            return None

    def get(self, request, session_id):
        session = self.get_object(request, session_id)
        if not session:
            return Response({'detail': 'Triage session not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(TriageSessionSerializer(session).data, status=status.HTTP_200_OK)


class TriageSessionAnswerView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, session_id):
        try:
            return TriageSession.objects.select_related('current_question', 'flow').get(id=session_id, user=request.user)
        except TriageSession.DoesNotExist:
            return None

    def post(self, request, session_id):
        session = self.get_object(request, session_id)
        if not session:
            return Response({'detail': 'Triage session not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = TriageSessionAnswerCreateSerializer(data=request.data, context={'request': request, 'session': session})
        serializer.is_valid(raise_exception=True)
        session = serializer.save()
        session = (
            TriageSession.objects.filter(id=session.id)
            .select_related('flow', 'family_member', 'current_question')
            .prefetch_related('answers__question', 'answers__option', 'current_question__options')
            .get()
        )
        return Response({'message': 'Answer saved successfully.', 'session': TriageSessionSerializer(session).data}, status=status.HTTP_200_OK)
