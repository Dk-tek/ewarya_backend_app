from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User

from .models import FlagChoices, TriageFlow, TriageOption, TriageOptionTransition, TriageQuestion


class TriageSessionAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='triage_user',
            password='secret123',
            phone_number='9999999999',
        )
        self.client.force_authenticate(self.user)

    def _create_flow(self):
        flow = TriageFlow.objects.create(name='Adult Triage', code='adult-triage')
        q1 = TriageQuestion.objects.create(
            flow=flow,
            code='breathing-severe',
            text='Are you having severe breathing difficulty?',
            is_start_question=True,
            display_order=1,
        )
        q2 = TriageQuestion.objects.create(
            flow=flow,
            code='chest-pain',
            text='Do you also have chest pain?',
            display_order=2,
        )
        q3 = TriageQuestion.objects.create(
            flow=flow,
            code='sweating',
            text='Are you sweating heavily?',
            display_order=3,
        )

        q1_yes = TriageOption.objects.create(question=q1, code='yes', label='Yes')
        q1_no = TriageOption.objects.create(question=q1, code='no', label='No')
        q2_yes = TriageOption.objects.create(question=q2, code='yes', label='Yes')
        q2_no = TriageOption.objects.create(question=q2, code='no', label='No', flag_effect=FlagChoices.GREEN)
        q3_yes = TriageOption.objects.create(question=q3, code='yes', label='Yes')
        q3_no = TriageOption.objects.create(question=q3, code='no', label='No', flag_effect=FlagChoices.YELLOW)

        TriageOptionTransition.objects.create(option=q1_yes, end_flag=FlagChoices.RED, end_message='Immediate emergency.')
        TriageOptionTransition.objects.create(option=q1_no, next_question=q2)
        TriageOptionTransition.objects.create(option=q2_yes, next_question=q3)
        TriageOptionTransition.objects.create(option=q3_yes, end_flag=FlagChoices.RED, end_message='Cardiac red flag path.')

        return {
            'flow': flow,
            'q1_yes': q1_yes,
            'q1_no': q1_no,
            'q2_yes': q2_yes,
            'q2_no': q2_no,
            'q3_yes': q3_yes,
            'q3_no': q3_no,
        }

    def test_single_answer_can_end_session_with_red_flag(self):
        data = self._create_flow()
        start_response = self.client.post(reverse('triage-session-start'), {'flow_id': data['flow'].id}, format='json')

        self.assertEqual(start_response.status_code, status.HTTP_201_CREATED)
        session_id = start_response.data['session']['id']

        answer_response = self.client.post(
            reverse('triage-session-answer', args=[session_id]),
            {'option_id': data['q1_yes'].id},
            format='json',
        )

        self.assertEqual(answer_response.status_code, status.HTTP_200_OK)
        self.assertEqual(answer_response.data['session']['status'], 'COMPLETED')
        self.assertEqual(answer_response.data['session']['final_flag'], 'RED')
        self.assertEqual(len(answer_response.data['session']['answers']), 1)
        self.assertEqual(
            answer_response.data['session']['answers'][0]['question_text_snapshot'],
            'Are you having severe breathing difficulty?',
        )

    def test_multiple_answers_can_reach_red_flag_and_preserve_history(self):
        data = self._create_flow()
        start_response = self.client.post(reverse('triage-session-start'), {'flow_id': data['flow'].id}, format='json')
        session_id = start_response.data['session']['id']

        self.client.post(reverse('triage-session-answer', args=[session_id]), {'option_id': data['q1_no'].id}, format='json')
        self.client.post(reverse('triage-session-answer', args=[session_id]), {'option_id': data['q2_yes'].id}, format='json')
        final_response = self.client.post(
            reverse('triage-session-answer', args=[session_id]),
            {'option_id': data['q3_yes'].id},
            format='json',
        )

        self.assertEqual(final_response.status_code, status.HTTP_200_OK)
        self.assertEqual(final_response.data['session']['final_flag'], 'RED')
        self.assertEqual(final_response.data['session']['status'], 'COMPLETED')
        self.assertEqual(len(final_response.data['session']['answers']), 3)
        self.assertEqual(
            [answer['option_label_snapshot'] for answer in final_response.data['session']['answers']],
            ['No', 'Yes', 'Yes'],
        )
