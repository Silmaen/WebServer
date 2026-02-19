"""test.py"""
from django.test import TestCase, Client
from django.urls import reverse


class MainTest(TestCase):
    def test_should_respond_for_www(self):
        client = Client()
        view = reverse("index")
        response = client.get(view)
        self.assertEqual(response.status_code, 200)
