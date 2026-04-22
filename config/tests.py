from django.test import SimpleTestCase
from django.urls import reverse

from .views import PAGE_TEMPLATES


class FrontendRoutingTests(SimpleTestCase):
    def test_page_routes_render_templates(self):
        for name in PAGE_TEMPLATES:
            response = self.client.get(reverse(f'page-{name}'))
            self.assertEqual(response.status_code, 200)

    def test_api_root_lists_backend_sections(self):
        response = self.client.get(reverse('api-root'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('auth', response.json())
        self.assertIn('triage', response.json())
