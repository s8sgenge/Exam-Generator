from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse
from django.utils import timezone

from ..models import Content
from ..models import Exam
from ..models import Exercise
from ..models import ExerciseSolution
from ..models import ExerciseText
from ..models import FileDependency
from ..models import Header
from ..models import Topic


class ViewTest(TestCase):
    key_exercise_1 = -1
    key_exercise_2 = -1
    '''
        Setup the test database for the tests
        '''

    @classmethod
    def setUpTestData(cls):
        time = timezone.now()
        latexhead = "\\documentclass{article} \\usepackage[utf8]{inputenc} \\usepackage{graphicx} \\title{Exam}"
        latex = "\\begin{itemize}\item Jo-Max Baby:\\begin{itemize}\item topic overview $(\sim 20min)$\item lgin $(\sim 45min)$\end{itemize}"
        man = User.objects.create_user(username='test', password='test')
        man.save()
        file = FileDependency.objects.create(file='/media/filedependency/exercise1/bild.png')
        file.save()
        topic = Topic.objects.create(name='ER-Diagramm')
        topic.save()
        solution = ExerciseSolution.objects.create(versionGroup=None, language='German', latex_code=latex,
                                                   author=man)
        solution.files.add(file)
        solution.save()
        text = ExerciseText.objects.create(versionGroup=None, language='German', latex_code=latex, author=man)
        text.files.add(file)
        text.save()
        header = Header.objects.create(versionGroup=None, language='German', latex_code=latexhead, author=man)
        header.files.add(file)
        header.save()
        exam = Exam.objects.create(author=man, documentHead=header)
        exam.save()
        exercise1 = Exercise.objects.create(versionGroup=None, documentHead=header, modifiable=False, points=10,
                                            exerciseSolution=solution, exerciseText=text, topic=topic, date=time)
        exercise1.save()
        cls.key_exercise_1 = exercise1.id
        exercise2 = Exercise.objects.create(versionGroup=exercise1, documentHead=header, modifiable=False, points=10,
                                            exerciseSolution=solution, exerciseText=text, topic=topic, date=time)
        exercise2.save()
        cls.key_exercise_2 = exercise2.id
        content1 = Content.objects.create(exam=exam, exercise=exercise1, position=1)
        content1.save()
        content2 = Content.objects.create(exam=exam, exercise=exercise2, position=2)
        content2.save()

    '''
        setUp before each test
    '''

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='tester', password='test')
        self.group = Group(name="Employee")
        self.group.save()

    '''
        test if each url get reached (if the user got the permission)
        each view is tested with a login user with employee rights and not login user
    '''

    def test_view_topic_login(self):
        self.user.groups.add(self.group)
        self.user.save()
        self.client.login(username='tester', password='test')
        response = self.client.get('/topicOverview')
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('topic overview'))
        self.assertEqual(response.status_code, 200)

    def test_view_topic_notlogin(self):
        response = self.client.get('/topicOverview')
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('topic overview'))
        self.assertEqual(response.status_code, 302)

    def test_view_downloadpage_login(self):
        self.user.groups.add(self.group)
        self.user.save()
        self.client.login(username='tester', password='test')
        response = self.client.get('/downloadPage')
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('download page'))
        self.assertEqual(response.status_code, 302)

    def test_view_downloadpage_notlogin(self):
        response = self.client.get('/downloadPage')
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('download page'))
        self.assertEqual(response.status_code, 302)

    def test_view_examscreen_login(self):
        self.user.groups.add(self.group)
        self.user.save()
        self.client.login(username='tester', password='test')
        response = self.client.get('/examScreen')
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('exam detail view'))
        self.assertEqual(response.status_code, 200)

    def test_view_examscreen_notlogin(self):
        response = self.client.get('/examScreen')
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('exam detail view'))
        self.assertEqual(response.status_code, 302)

    def test_view_signUp_login(self):
        self.user.groups.add(self.group)
        self.user.save()
        self.client.login(username='tester', password='test')
        response = self.client.get('/signUp')
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('sign up'))
        self.assertEqual(response.status_code, 200)

    def test_view_signUp_notlogin(self):
        response = self.client.get('/signUp')
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('sign up'))
        self.assertEqual(response.status_code, 200)

    def test_view_uploadExercise_login(self):
        self.user.groups.add(self.group)
        self.user.save()
        self.client.login(username='tester', password='test')
        response = self.client.get('/uploadExercise')
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('upload exercise'))
        self.assertEqual(response.status_code, 200)

    def test_view_uploadExercise_notlogin(self):
        response = self.client.get('/uploadExercise')
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('upload exercise'))
        self.assertEqual(response.status_code, 302)

    def test_view_headerlist_login(self):
        self.user.groups.add(self.group)
        self.user.save()
        self.client.login(username='tester', password='test')
        response = self.client.get('/headers')
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('header list'))
        self.assertEqual(response.status_code, 200)

    def test_view_headerlist_notlogin(self):
        response = self.client.get('/headers')
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('header list'))
        self.assertEqual(response.status_code, 302)

    def test_view_index_login(self):
        self.user.groups.add(self.group)
        self.user.save()
        self.client.login(username='tester', password='test')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_view_index_notlogin(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 302)

    def test_topicExerciseList_login(self):
        self.user.groups.add(self.group)
        self.user.save()
        self.client.login(username='tester', password='test')
        response = self.client.get(reverse('topic exercise list', args=[1]))
        self.assertEquals(response.status_code, 200)
        response = self.client.get('/topic/1/exerciseList')
        self.assertEqual(response.status_code, 200)

    def test_topicExerciseList_notlogin(self):
        response = self.client.get(reverse('topic exercise list', args=[1]))
        self.assertEquals(response.status_code, 302)
        response = self.client.get('/topic/1/exerciseList')
        self.assertEqual(response.status_code, 302)

    def test_exercisedetail_login(self):
        self.user.groups.add(self.group)
        self.user.save()
        self.client.login(username='tester', password='test')
        response = self.client.get(reverse('exercise detail', args=[self.key_exercise_1]))
        self.assertEquals(response.status_code, 200)
        response = self.client.get(f'/exercise/{self.key_exercise_1}')
        self.assertEqual(response.status_code, 200)

    def test_exercisedetail_notlogin(self):
        response = self.client.get(reverse('exercise detail', args=[1]))
        self.assertEquals(response.status_code, 302)
        response = self.client.get('/exercise/1')
        self.assertEqual(response.status_code, 302)

    def test_prevVersion_login(self):
        self.user.groups.add(self.group)
        self.user.save()
        self.client.login(username='tester', password='test')
        response = self.client.get(reverse('prev version', args=[self.key_exercise_2]))
        self.assertEqual(response.status_code, 302)
        response = self.client.get(f'/exercise/{self.key_exercise_2}/prev')
        self.assertEqual(response.status_code, 302)

    def test_prevVersion_notlogin(self):
        response = self.client.get(reverse('prev version', args=[2]))
        self.assertEquals(response.status_code, 302)
        response = self.client.get('/exercise/2/prev')
        self.assertEqual(response.status_code, 302)

    def test_nextVersion_login(self):
        self.user.groups.add(self.group)
        self.user.save()
        self.client.login(username='tester', password='test')
        response = self.client.get(reverse('next version', args=[self.key_exercise_1]))
        self.assertEqual(response.status_code, 302)
        response = self.client.get(f'/exercise/{self.key_exercise_1}/next')
        self.assertEqual(response.status_code, 302)

    def test_nextVersion_notlogin(self):
        response = self.client.get(reverse('next version', args=[1]))
        self.assertEquals(response.status_code, 302)
        response = self.client.get('/exercise/1/next')
        self.assertEqual(response.status_code, 302)

    def test_addToExam_login(self):
        self.user.groups.add(self.group)
        self.user.save()
        self.client.login(username='tester', password='test')
        response = self.client.get(reverse('add exercise to exam', args=[self.key_exercise_1]))
        self.assertEqual(response.status_code, 302)
        response = self.client.get(f'/addToExam/{self.key_exercise_1}')
        self.assertEqual(response.status_code, 302)

    def test_addToExam_notlogin(self):
        response = self.client.get(reverse('add exercise to exam', args=[1]))
        self.assertEquals(response.status_code, 302)
        response = self.client.get('/addToExam/1')
        self.assertEqual(response.status_code, 302)
