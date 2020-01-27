import random
import string

from django.contrib.auth.models import User
from django.test import TestCase

from ..forms import LoginForm


class Test_Login(TestCase):
    @classmethod
    def setUpTestData(cls):
        credentials = {
            'username': 'test',
            'password': '1234'}
        User.objects.create_user(**credentials)

    def test_login_label(self):
        login = LoginForm()
        self.assertTrue(login.fields['username'].label == 'Username')
        self.assertTrue(login.fields['password'].label == 'Password')

    def test_max_username_length(self):
        letters = string.ascii_lowercase
        string_with_301_chars = ''.join(random.choice(letters) for i in range(301))
        login = LoginForm(data={'username': string_with_301_chars, 'password': "1234"})
        self.assertEquals(login.is_valid(), False)

    def test_max_password_length(self):
        letters = string.ascii_lowercase
        string_with_301_chars = ''.join(random.choice(letters) for i in range(301))
        login = LoginForm(data={'username': "1234", 'password': string_with_301_chars})
        self.assertEquals(login.is_valid(), False)

    def test_only_username(self):
        login = LoginForm(data={'username': "test"})
        self.assertEquals(login.is_valid(), False)

    def test_only_password(self):
        login = LoginForm(data={'password': "test"})
        self.assertEquals(login.is_valid(), False)

    def test_valid_input(self):
        login = LoginForm(data={'username': "test", 'password': "1234"})
        self.assertEquals(login.is_valid(), True)
