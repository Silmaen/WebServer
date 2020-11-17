"""test.py"""
from django.test import TestCase, Client
from django.urls import reverse


url_vhost = "www.urls_base"


class MainTest(TestCase):
    def test_should_respond_for_www(self):
        client = Client(HTTP_HOST="www.argawaen.net")
        view = reverse("index", urlconf=url_vhost)
        response = client.get(view)
        self.assertEqual(response.status_code, 200)

    def test_should_not_respond_for_drone(self):
        client = Client(HTTP_HOST="drone.argawaen.net")
        view = reverse("index", urlconf=url_vhost)
        response = client.get(view)
        self.assertEqual(response.status_code, 404)

    def test_should_not_respond_for_testsubject(self):
        client = Client(HTTP_HOST="testsubject.argawaen.net")
        view = reverse("index", urlconf=url_vhost)
        response = client.get(view)
        self.assertEqual(response.status_code, 404)

    def test_should_not_respond_for_ayoaron(self):
        client = Client(HTTP_HOST="ayoaron.argawaen.net")
        view = reverse("index", urlconf=url_vhost)
        response = client.get(view)
        self.assertEqual(response.status_code, 404)
