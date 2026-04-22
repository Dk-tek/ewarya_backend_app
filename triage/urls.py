from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .views import (
    TriageFlowDetailView,
    TriageFlowView,
    TriageOptionDetailView,
    TriageOptionTransitionDetailView,
    TriageOptionTransitionView,
    TriageOptionView,
    TriageQuestionDetailView,
    TriageQuestionView,
    TriageSessionAnswerView,
    TriageSessionDetailView,
    TriageSessionListView,
    TriageSessionStartView,
)


@api_view(['GET'])
def triage_api_root(request):
    return Response(
        {
            'flows': request.build_absolute_uri('/api/triage/flows/'),
            'questions': request.build_absolute_uri('/api/triage/questions/'),
            'options': request.build_absolute_uri('/api/triage/options/'),
            'transitions': request.build_absolute_uri('/api/triage/transitions/'),
            'sessions': request.build_absolute_uri('/api/triage/sessions/'),
            'start_session': request.build_absolute_uri('/api/triage/sessions/start/'),
        }
    )


urlpatterns = [
    path('', triage_api_root, name='triage-api-root'),
    path('flows/', TriageFlowView.as_view(), name='triage-flows'),
    path('flows/<int:flow_id>/', TriageFlowDetailView.as_view(), name='triage-flow-detail'),
    path('questions/', TriageQuestionView.as_view(), name='triage-questions'),
    path('questions/<int:question_id>/', TriageQuestionDetailView.as_view(), name='triage-question-detail'),
    path('options/', TriageOptionView.as_view(), name='triage-options'),
    path('options/<int:option_id>/', TriageOptionDetailView.as_view(), name='triage-option-detail'),
    path('transitions/', TriageOptionTransitionView.as_view(), name='triage-transitions'),
    path('transitions/<int:transition_id>/', TriageOptionTransitionDetailView.as_view(), name='triage-transition-detail'),
    path('sessions/', TriageSessionListView.as_view(), name='triage-sessions'),
    path('sessions/start/', TriageSessionStartView.as_view(), name='triage-session-start'),
    path('sessions/<int:session_id>/', TriageSessionDetailView.as_view(), name='triage-session-detail'),
    path('sessions/<int:session_id>/answer/', TriageSessionAnswerView.as_view(), name='triage-session-answer'),
]
