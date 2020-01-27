from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase

from ..models import Content
from ..models import Exam
from ..models import Exercise
from ..models import ExerciseSolution
from ..models import ExerciseText
from ..models import FileDependency
from ..models import Header
from ..models import Topic


class ModelTest(TestCase):
    '''
    Setup the test database for the tests
    '''

    @classmethod
    def setUpTestData(cls):
        latextext = "\\begin{itemize}\item Jo-Max Baby:\\begin{itemize}\item topic overview $(\sim 20min)$\item lgin $(\sim 45min)$\end{itemize}"
        latexsol = "\\begin{soltionbox}This is the solution\end{solutionbox}"
        latexhead = "\\documentclass{article} \\usepackage[utf8]{inputenc} \\usepackage{graphicx} \\title{Exam}"
        user = User.objects.create(username='HansiUrpils', email='hansi@urpils.com')
        topic = Topic.objects.create(name='ER-Diagramm')
        User.objects.create_user(username='tester', password='test')
        file = FileDependency.objects.create(file='/media/filedependency/exercise1/bild.png')
        solution = ExerciseSolution.objects.create(versionGroup=None, language='German', latex_code=latexsol,
                                                   author=user)
        solution.files.add(file)
        text = ExerciseText.objects.create(versionGroup=None, language='German', latex_code=latextext, author=user)
        text.files.add(file)
        header = Header.objects.create(versionGroup=None, language='German', latex_code=latexhead, author=user)
        header.files.add(file)
        exercise1 = Exercise.objects.create(versionGroup=None, documentHead=header, modifiable=False, points=10,
                                            exerciseSolution=solution, exerciseText=text, topic=topic)
        exercise2 = Exercise.objects.create(versionGroup=exercise1, documentHead=header, modifiable=False, points=10,
                                            exerciseSolution=solution, exerciseText=text, topic=topic)
        exam = Exam.objects.create(author=user, documentHead=header)
        Content.objects.create(exam=exam, exercise=exercise2, position=1)

    '''
    test if each table is created correctly
    one or two attributes get testet for each model
    '''

    def test_user(self):
        user = User.objects.get(username='HansiUrpils')
        self.assertEquals(user.email, 'hansi@urpils.com')

    def test_topic(self):
        topic = Topic.objects.get(id=1)
        name = topic.name
        self.assertEquals(name, "ER-Diagramm")
        self.assertFalse(name == "ER")
        with self.assertRaises(IntegrityError):
            Topic.objects.create(name='ER-Diagramm')

    def test_file(self):
        file = FileDependency.objects.get(id=1)
        path = file.file
        self.assertEquals(path, '/media/filedependency/exercise1/bild.png')

    def test_header(self):
        header = Header.objects.get(id=1)
        lang = header.language
        self.assertEquals(lang, 'German')

    def test_exercisesolution(self):
        solution = ExerciseSolution.objects.get(id=1)
        text = solution.latex_code
        latexsol = "\\begin{soltionbox}This is the solution\end{solutionbox}"
        self.assertEquals(text, latexsol)

    def test_exercisetext(self):
        exercise = ExerciseText.objects.get(id=1)
        text = exercise.latex_code
        latextext = "\\begin{itemize}\item Jo-Max Baby:\\begin{itemize}\item topic overview $(\sim 20min)$\item lgin $(\sim 45min)$\end{itemize}"
        self.assertEquals(text, latextext)

    def test_exercise(self):
        exercise = Exercise.objects.get(id=1)
        sol = exercise.exerciseSolution.latex_code
        text = exercise.exerciseText.latex_code
        latextext = "\\begin{itemize}\item Jo-Max Baby:\\begin{itemize}\item topic overview $(\sim 20min)$\item lgin $(\sim 45min)$\end{itemize}"
        latexsol = "\\begin{soltionbox}This is the solution\end{solutionbox}"
        self.assertEquals(text, latextext)
        self.assertEquals(sol, latexsol)

    def test_exam(self):
        exam = Exam.objects.get(id=1)
        author = exam.author.username
        head = exam.documentHead
        latexhead = "\\documentclass{article} \\usepackage[utf8]{inputenc} \\usepackage{graphicx} \\title{Exam}"
        name = 'HansiUrpils'
        self.assertEquals(name, author)
        self.assertEquals(head.latex_code, latexhead)

    def test_content(self):
        content = Content.objects.get(id=1)
        position = content.position
        self.assertEquals(position, 1)
