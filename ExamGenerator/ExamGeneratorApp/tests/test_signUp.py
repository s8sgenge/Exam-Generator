import random
import string

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase

from ..forms import SignUpForm


class Test_signUp(TestCase):
    @classmethod
    def setUpTestData(cls):
        credentials = {
            'username': 'test',
            'password': '1234'}
        User.objects.create_user(**credentials)

    '''
    check the labels of the table in the db
    '''

    def test_signUp_lable(self):
        sign = SignUpForm()
        self.assertTrue(sign.fields['username'].label == 'Username')
        self.assertTrue(sign.fields['name'].label == 'Name')
        self.assertTrue(sign.fields['firstname'].label == 'Firstname')
        self.assertTrue(sign.fields['password'].label == 'Password')
        self.assertTrue(sign.fields['mail'].label == 'Mail')

    '''
        Test valid data
    '''

    def test_valid_Username(self):
        sign = SignUpForm(
            data={'username': "DerCoolste", 'name': "tester", 'mail': "test@test.de", 'password': 1234,
                  'confirm_password': 1234, 'firstname': "test"})
        self.assertEquals(sign.is_valid(), True)

    def test_valid_Name(self):
        sign = SignUpForm(
            data={'username': "test", 'name': "Mick", 'mail': "test@test.de", 'password': 1234,
                  'confirm_password': 1234, 'firstname': "test"})
        self.assertEquals(sign.is_valid(), True)

    def test_valid_Firstname(self):
        sign = SignUpForm(
            data={'username': "test", 'name': "test", 'mail': "test@test.de", 'password': 1234,
                  'confirm_password': 1234, 'firstname': "Hans-Peter"})
        self.assertEquals(sign.is_valid(), True)

    def test_valid_Mail(self):
        sign = SignUpForm(
            data={'username': "test", 'name': "test", 'mail': "s8seproject@stud.uni-saarland.de", 'password': 1234,
                  'confirm_password': 1234, 'firstname': "test"})
        self.assertEquals(sign.is_valid(), True)

    def test_valid_Password(self):
        sign = SignUpForm(
            data={'username': "test", 'name': "test", 'mail': "test@test.de", 'password': "%779Pqq#a123uff",
                  'confirm_password': '%779Pqq#a123uff', 'firstname': "test"})
        self.assertEquals(sign.is_valid(), True)

    '''
    test unvalid or missing data
    '''

    def test_unvalid_Username(self):
        letters = string.ascii_lowercase
        rand = ''.join(random.choice(letters) for i in range(301))
        sign = SignUpForm(
            data={'username': rand, 'name': "test", 'mail': "test@test.de", 'password': 1234, 'confirm_password': 1234,
                  'firstname': "test"})
        self.assertEquals(sign.is_valid(), False)

    def test_missing_Username(self):
        sign = SignUpForm(
            data={'name': "test", 'mail': "test@test.de", 'password': 1234, 'confirm_password': 1234,
                  'firstname': "test"})
        self.assertEquals(sign.is_valid(), False)

    def test_unvalid_Name(self):
        letters = string.ascii_lowercase
        rand = ''.join(random.choice(letters) for i in range(301))
        sign = SignUpForm(
            data={'username': "test", 'name': rand, 'mail': "test@test.de", 'password': 1234, 'confirm_password': 1234,
                  'firstname': "test"})
        self.assertEquals(sign.is_valid(), False)

    def test_missing_Name(self):
        sign = SignUpForm(
            data={'username': "test", 'mail': "test@test.de", 'password': 1234, 'confirm_password': 1234,
                  'firstname': "test"})
        self.assertEquals(sign.is_valid(), False)

    def test_unvalid_Firstname(self):
        letters = string.ascii_lowercase
        rand = ''.join(random.choice(letters) for i in range(301))
        sign = SignUpForm(
            data={'username': "test", 'name': "test", 'mail': "test@test.de", 'password': 1234,
                  'confirm_password': 1234, 'firstname': rand})
        self.assertEquals(sign.is_valid(), False)

    def test_missing_Firstname(self):
        sign = SignUpForm(
            data={'username': "test", 'name': "test", 'mail': "test@test.de", 'password': 1234,
                  'confirm_password': 1234, })
        self.assertEquals(sign.is_valid(), False)

    def test_unvalid_Mail(self):
        letters = string.ascii_lowercase
        rand = ''.join(random.choice(letters) for i in range(301))
        sign = SignUpForm(
            data={'username': "test", 'name': "test", 'mail': rand, 'password': 1234, 'confirm_password': 1234,
                  'firstname': "test"})
        self.assertEquals(sign.is_valid(), False)

    def test_missing_Mail(self):
        sign = SignUpForm(
            data={'username': "test", 'name': "test", 'password': 1234, 'confirm_password': 1234, 'firstname': "test"})
        self.assertEquals(sign.is_valid(), False)

    def test_unvalid_Password(self):
        letters = string.ascii_lowercase
        rand = ''.join(random.choice(letters) for i in range(301))
        sign = SignUpForm(
            data={'username': "test", 'name': "test", 'mail': "test@test.de", 'password': rand,
                  'confirm_password': 1234, 'firstname': "test"})
        self.assertEquals(sign.is_valid(), False)

    def test_missing_Password(self):
        sign = SignUpForm(
            data={'username': "test", 'name': "test", 'mail': "test@test.de", 'confirm_password': 1234,
                  'firstname': "test"})
        self.assertEquals(sign.is_valid(), False)

    '''
    other tests
    '''

    def test_newValidUser(self):
        get_user_model().objects.create(username='HansiUrpils', last_name='Urpils', email='HansiUrpils@karlsburg.com',
                                        password=1234, first_name='Hans')

    def test_userAlreadyExsists(self):
        get_user_model().objects.create(username='HansiUrpils', last_name='Urpils', email='HansiUrpils@karlsburg.com',
                                        password=1234, first_name='Hans')
        with self.assertRaises(IntegrityError):
            get_user_model().objects.create(username='HansiUrpils', last_name='Urpils',
                                            email='HansiUrpils@karlsburg.com', password=1234, first_name='Hans')

    def test_userEmailalreadyExsists(self):
        get_user_model().objects.create(username='HansiUrpils', last_name='Urpils', email='HansiUrpils@karlsburg.com',
                                        password=1234, first_name='Hans')
        get_user_model().objects.create(username='HansiUrpilsa', last_name='Urpilsa', email='HansiUrpils@karlsburg.com',
                                        password=1234, first_name='Hansa')

    def test_userUsernamealreadyExsists(self):
        get_user_model().objects.create(username='testing', last_name='testera',
                                        email='testing@testing.testa', password=1234, first_name='testerera')
        with self.assertRaises(IntegrityError):
            get_user_model().objects.create(username='testing', last_name='tester',
                                            email='testing@testing.test', password=1234, first_name='testerer')
