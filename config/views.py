from django.shortcuts import render
from django.urls import reverse
from rest_framework.decorators import api_view
from rest_framework.response import Response


PAGE_TEMPLATES = {
    'dashboard': 'dashboard.html',
    'consultations': 'consultations.html',
    'doctors': 'doctors.html',
    'patients': 'patients.html',
    'analytics': 'analytics.html',
    'settings': 'settings.html',
    'login': 'login.html',
    'register': 'register.html',
    'hc-auth': 'hc-auth.html',
    'hc-profile': 'hc-profile.html',
    'hc-family': 'hc-family.html',
    'hc-builder': 'hc-builder.html',
    'hc-triage': 'hc-triage.html',
    'hc-api': 'hc-api.html',
}


def render_page(request, page='dashboard'):
    return render(request, PAGE_TEMPLATES[page])


@api_view(['GET'])
def api_root(request):
    return Response(
        {
            'auth': request.build_absolute_uri(reverse('auth-api-root')),
            'triage': request.build_absolute_uri(reverse('triage-api-root')),
            'pages': {
                name: request.build_absolute_uri(reverse(f'page-{name}'))
                for name in PAGE_TEMPLATES
            },
        }
    )
