import os
from django.contrib.staticfiles.testing import StaticLiveServerTestCase 
from playwright.sync_api import sync_playwright, expect
import time
from datetime import datetime

from django.test import TestCase
from django.urls import reverse
from django.core.management import call_command
from django.conf import settings

from .models import (
	FicheDetection, 
	OrganismeNuisible, 
	NumeroFiche, 
	Unite, 
	Administration, 
	StatutEvenement, 
	StatutReglementaire,
	Contexte
)


class HomePageTests(StaticLiveServerTestCase): 
	@classmethod 
	def setUpClass(cls): 
		os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
		super().setUpClass() 
		cls.playwright = sync_playwright().start() 
		cls.browser = cls.playwright.chromium.launch() 

	@classmethod 
	def tearDownClass(cls): 
		cls.browser.close() 
		cls.playwright.stop() 
		super().tearDownClass() 

	def test_seves_in_title(self): 
		page = self.browser.new_page() 
		page.goto(self.live_server_url)
		self.assertIn('Sèves', page.inner_text('h1'))
		page.close()


class FicheDetectionListViewTests(StaticLiveServerTestCase):
	@classmethod
	def setUpClass(cls):
		os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
		super().setUpClass()
		cls.playwright = sync_playwright().start()
		cls.browser = cls.playwright.chromium.launch()

	@classmethod
	def tearDownClass(cls):
		cls.browser.close()
		cls.playwright.stop()
		super().tearDownClass()

	def test_url(self):
		page = self.browser.new_page()
		page.goto(f'{self.live_server_url}/sv/fiches-detection/')
		self.assertEqual(page.url, f'{self.live_server_url}/sv/fiches-detection/')
		page.close()

	def test_no_fiches(self):
		page = self.browser.new_page()
		page.goto(f'{self.live_server_url}/sv/fiches-detection/')
		# Liste des fiches détection en h1
		self.assertIn('Liste des fiches détection', page.inner_text('h1'))
		self.assertIn('Aucune fiche de détection', page.inner_text('body'))
		page.close()
