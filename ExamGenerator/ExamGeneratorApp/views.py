import codecs
import datetime
import os
import re
import shutil
import subprocess
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User, Group
from django.core.files.storage import DefaultStorage
from django.db.models import Q
from django.forms import modelformset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_protect
from django.views.generic import UpdateView, ListView, DetailView, TemplateView

from .forms import SignUpForm, UploadForm, ExerciseDetailForm, LoginForm
from .forms import TopicForm, HeaderForm, ExamForm
from .models import *


def get_or_create_default_header(user):
    """
    Used when first creating an exam for a user since it has to have a header.
    :param user:
    :return:
    """
    return Header.objects.get_or_create(name='Empty Default', defaults={'author': user,
                                                                        'latex_code': '\\documentclass[a4paper,german,oneside]{article}\n'
                                                                                      'This is the empty default header, please specify a header when rendering.\n\\begin{document}'})[
        0]


def create_template_context(request):
    """
    Builds the context used in template.html, and thus on every other page as well. Mostly for the dropdown topic menu.
    :param request:
    :return:
    """
    Group.objects.get_or_create(name='Employee')
    exam_topics = []
    if request.user.is_authenticated:
        user = request.user
        exams = Exam.objects.filter(author=user)
        if len(exams) != 0:
            exam = exams.latest('creationDate')
            exercises = Exercise.objects.filter(exam=exam).order_by('content__position')
            for exercise in exercises:
                exam_topics.append(exercise.topic)

    topics = Topic.objects.all()
    template_context = {
        'topics': topics.order_by('name'),
        'LoginForm': LoginForm(),
        'examTopics': exam_topics
    }
    return template_context.copy()


def can_change_rights(user):
    return user.is_superuser or user.is_staff


def has_permission(user):
    groups = list(user.groups.all())
    if len(groups) == 0 and not (user.is_superuser or user.is_staff):
        return False
    else:
        group = list(Group.objects.filter(name='Employee'))[0]
        return group in groups or user.is_superuser or user.is_staff


def clear_user_temp(user):
    """
    Deletes all files in  a user's temp directory.
    :param user:
    :return:
    """
    work_dir = Path("ExamGenerator/media/temp/%s" % user.username).absolute()
    if os.path.isdir(work_dir):
        files = os.listdir(work_dir)
        shutil.rmtree(work_dir)
        os.makedirs(work_dir)


def render_pdf(user, exercises, content_tuples=None, header=None, include_disclaimer=False, files=None,
               include_solutions=False,
               document_name=None, clean_directory=True, timeout=25):
    """
    Creates a PDF file based on arguments in the user's temp folder. To do this pdflatex command is executed.
    Pdflatex has to be installed on the system to work. If the command times out, a file called err_log.txt is created,
    containing the stdout of the process from the first "Error:" onwards
    :param user: the user making the request
    :param exercises: iterable of exercises. Always has priority over content_tuples
    :param content_tuples: list of tuples (exerciseTex,solutionTex). Ignored if exercises is not None
    :param header: a header object to be used as documenthead
    :param include_disclaimer: whether or not to include the disclaimer. Only works if disclaimer is surrounded
    by %begin_disclaimer %end_disclaimer
    :param files: file iterable of additional file dependencies
    :param include_solutions: whether or not the solutions are to be included in the pdf. Recommended to have a
    withoutsolutions command in the latex header and comment it with %. Also works if exercise cleanly split exercise
    text and solution on database level
    :param document_name: output file name
    :param clean_directory: deletes all files in the user's temp directory if True
    :param timeout: timout for the pdflatex process
    :return: True if pdlatex finished, False if timeout occurred
     """

    # prepare temp directory
    storage = DefaultStorage()
    if clean_directory:
        clear_user_temp(user)
    work_dir = Path("ExamGenerator/media/temp/%s" % user.username)
    if not document_name:
        document_name = 'document.tex'
    document_path = os.path.join(work_dir, document_name)
    if not os.path.isdir(work_dir):
        os.makedirs(work_dir)
    if not os.path.exists(document_path):
        open(document_path, 'w', encoding="utf-8").close()

    # load header
    if not header:
        # this should open a backup header stored as a file on the server. File not included in repository.

        # default_header_file = open(storage.path('default_header'), encoding='utf-8')
        # default_header = default_header_file.read()
        # default_header_file.close()
        # header_tex = default_header
        # shutil.copy(os.path.join(settings.MEDIA_ROOT, "CS-UdS-logo.jpg"), work_dir)
        pass
    else:
        # copy header dependencies to temp folder
        header_dependencies_dir = settings.MEDIA_ROOT + '/headers/header' + str(header.id)
        if os.path.exists(header_dependencies_dir):
            header_files = os.listdir(header_dependencies_dir)
            for f in header_files:
                shutil.copy(os.path.join(header_dependencies_dir, f),
                            work_dir)
        header_tex = header.latex_code

    # try to use a comment like this to exclude solutions
    if not include_solutions:
        header_tex = header_tex.replace('%\\withoutsolutions', '\\withoutsolutions')

    # exclude disclaimer using the comment 'tags' it's supposed to have
    if not include_disclaimer:
        header_tex = re.sub(r'%begin_disclaimer.*%end_disclaimer', '%begin_disclaimer\n%end_disclaimer', header_tex,
                            1,
                            re.DOTALL | re.MULTILINE)

    # put files from argument in temp
    if files:
        for file in files:
            storage.save(
                settings.MEDIA_ROOT + '/temp/' + user.username + '/' + str(
                    file.name), file)

    # create content, i.e. string together exercise latex
    content = ''
    if not content_tuples:
        content_tuples = []
    if exercises:
        for exercise in exercises:
            # copy dependencies
            exercise_dependencies_dir = settings.MEDIA_ROOT + '/exercises/exercise' + str(
                exercise.id) + '/file_dependencies'
            if os.path.exists(exercise_dependencies_dir):
                files = os.listdir(exercise_dependencies_dir)
                for f in files:
                    shutil.copy(os.path.join(exercise_dependencies_dir, f),
                                work_dir)
                    # create tuples of text and solution
            exercise_tex = ''
            solution_tex = ''
            if exercise.exerciseText is not None:
                exercise_tex = exercise.exerciseText.latex_code
            if exercise.exerciseSolution is not None:
                solution_tex = exercise.exerciseSolution.latex_code
            content_tuples.append((exercise_tex, solution_tex))

    # string it all together according to args
    for tuple in content_tuples:
        content = content + tuple[0] + '\n'
        if include_solutions:
            content = content + tuple[1] + '\n'

    if 0 == len(content):
        content = content + "\nNo exercises"

    # put together the latex document
    document = header_tex + "\n\n" + content + "\n\\end{document}"

    # try to adjust the score tabular (Customer specific)
    try:
        document = adjust_header(document, header.language, exercises)
    except AttributeError:
        pass

    # create the actual file and write the content
    file = codecs.open(document_path, "w", "utf-8")
    file.write(document)
    file.close()

    # run pdflatex. nonstopmode hits enter on every input request pdflatex has on the terminal
    try:
        subprocess.run(['pdflatex', '-interaction=nonstopmode', document_name],
                       cwd=str(
                           work_dir.absolute()), timeout=timeout, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
        return True
    except subprocess.TimeoutExpired as e:
        # if a timeout is encountered we write the output into our own log. Otherwise we'll always use the log file
        # created by a properly finishing pdflatex process
        err = e.stdout.decode('utf8').partition('Error:')[2]
        err_log_path = os.path.join(work_dir, 'err_log.txt')
        err_log = open(err_log_path, 'w', encoding="utf-8")
        err_log.write(err)
        err_log.close()
        return False


def find_right_tabular(keyphrase, tex_code):
    """
    (Customer specific)
    Searches for the tabular to replace.
    :param keyphrase: The keyphrase is used to find the right tabular to replace. Keyphrase should be a phrase which is
                      somewhere between "\begin{tabular}" and "\end{tabular}" and furthermore the keyphrase should be
                      unique.
    :param tex_code: The tex code of the created exam.
    :return: Tuple(the tabular to be replaced as a String,True) or Tuple("",False) #the second value of the tuple
             indicates, whether the search was successful or not.
    """
    index_max_points = tex_code.find(keyphrase)
    if index_max_points < 0:
        return "", False

    all_occurrences_of_tabular = [m.start() for m in re.finditer('tabular', tex_code)]

    start_of_tabular = 0
    end_of_tabular = float('inf')
    for occurrence_index in range(len(all_occurrences_of_tabular)):
        if index_max_points > all_occurrences_of_tabular[occurrence_index] > start_of_tabular:
            start_of_tabular = all_occurrences_of_tabular[occurrence_index]

        if index_max_points < all_occurrences_of_tabular[occurrence_index] < end_of_tabular:
            end_of_tabular = all_occurrences_of_tabular[occurrence_index]

    if start_of_tabular != 0 and end_of_tabular != float('inf'):
        return tex_code[start_of_tabular:end_of_tabular], True
    else:
        return "", False


def create_new_tabular(language, exercises):
    """
    (Customer specific)
    Creates the score tabular for the created exam.
    :param language: The language flag of the created exam (English,German)
    :param exercises: The exercises which are part of the created exam
    :return: Tuple(the tex code of the adapted score tabular,True) or Tuple("",False) #the second value of the tuple
             indicates, whether the creation was successful or not
    """
    count_exercises = len(exercises)

    if language == 'German':
        new_tabular = "tabular}{|c| "

        for i in range(count_exercises):
            new_tabular += "|c"

        new_tabular += "| |c|}\n\t\hline\n\t" + "\\" + "textbf{Aufgabe}"

        for i in range(count_exercises):
            new_tabular += (" & " + "\\" + "textbf{" + str(i + 1) + "}")

        new_tabular += (" & \\textbf{$\sum$} " + "\\" + "\\ " + "\hline\n\t\\textbf{Maximale Punkte} ")

        sum_of_all_points = 0
        for i in range(count_exercises):
            new_tabular += f" & {exercises[i].points}"
            sum_of_all_points += exercises[i].points

        new_tabular += f" & {sum_of_all_points} \\\\ \\hline\n\t"
        new_tabular += "\\textbf{Erreichte Punkte}"

        for i in range(count_exercises + 1):
            new_tabular += " & \\quad"

        new_tabular += "  \\\\ \\hline\n  \\end{"

        return new_tabular, True

    elif language == 'English':
        new_tabular = "tabular}{ | l | "

        for i in range(count_exercises):
            new_tabular += "|c"

        new_tabular += "| |c|}\n\t\hline\n\t" + "\\" + "textbf{Question}"

        for i in range(count_exercises):
            new_tabular += (" & " + "\\" + "textbf{" + str(i + 1) + "}")

        new_tabular += (" & \\textbf{$\sum$} " + "\\" + "\\ " + "\hline\n\t\\textbf{Points in 1st Round} ")

        for i in range(count_exercises):
            new_tabular += " & "

        new_tabular += " &  \\\\ \\hline\n\t"
        new_tabular += "\\textbf{Final Points}"

        for i in range(count_exercises + 1):
            new_tabular += " & "

        new_tabular += "  \\\\ \\hline\n  \\end{"

        return new_tabular, True

    else:
        return "", False


def adjust_header(tex_code, language, exercises):
    """
    (Customer specific)
    Adapts the score tabular of the created exam, if possible.
    :param tex_code: The tex code of the created exam
    :param language: The language flag of the created exam (English,German)
    :param exercises: The exercises which are part of the created exam
    :return: the tex code of the exam with the adapted score tabular
    """
    if language == 'German':
        tabular_to_replace, found = find_right_tabular("Maximale Punkte", tex_code)

        if not found:
            return tex_code

        new_tabular, worked = create_new_tabular(language, exercises)
        if worked:
            return tex_code.replace(tabular_to_replace, new_tabular)

    elif language == 'English':
        tabular_to_replace, found = find_right_tabular("Final Points", tex_code)

        if not found:
            return tex_code

        new_tabular, worked = create_new_tabular(language, exercises)
        if worked:
            return tex_code.replace(tabular_to_replace, new_tabular)

    # always return old code if something didn't work
    return tex_code


def context_add_err_log(context, user, context_key):
    """
    Adds the contents of err_log.txt to the context if the file exists
    :param context: The context to modify
    :param user: The user making the request
    :param context_key: Key for the entry in context dict
    :return: nothing
    """
    storage = DefaultStorage()
    if storage.exists('temp/%s/err_log.txt' % user.username):
        err_log_file = open(storage.path('temp/%s/err_log.txt' % user.username), encoding='utf-8')
        err = err_log_file.read()
        err_log_file.close()
        context.update({context_key: err})


def render_log_info(user, filename, context=None):
    """
    Returns selected data from the .log file created by the pdflatex command.
    :param user: user making the request
    :param filename: name of the .log file
    :param context: If not None, context dictionary will be updated with the three values the function returns
    :return: number of occurrences of "Error:", number of occurrences of "Warning:", the part of the log after the first
     "Error:"
    """
    storage = DefaultStorage()
    if storage.exists('temp/%s/%s' % (user.username, filename)):
        log_file = open(storage.path('temp/%s/%s' % (user.username, filename)), encoding='utf-8')
        log = log_file.read()
        log_file.close()
        error_count = log.count('Error:')
        warning_count = log.count('Warning:')
        _, e, rest = log.partition('Error:')
        errors = e + rest
        errors, _, _ = errors.rpartition('Here is how much of TeX\'s memory you used:')
        if context is not None:
            if error_count is not None:
                context.update({'error_count': error_count})
            if warning_count is not None:
                context.update({'warning_count': warning_count})
            if errors is not None:
                context.update({'errors': errors})
        return error_count, warning_count, errors
    return None, None, None


@login_required
@user_passes_test(has_permission, login_url='/permissionDenied')
def previous_version_view(request, pk):
    """
    Redirects to the most recent previous version of an exercise, or itself if there is none
    :param request:
    :param pk: the primary key of the current exercise
    """
    exercise = get_object_or_404(Exercise, pk=pk)
    prev = exercise

    if exercise.versionGroup is not None:
        versions_qs = Exercise.objects.filter(Q(versionGroup=exercise.versionGroup.pk) | Q(pk=exercise.versionGroup.pk),
                                              date__lt=exercise.date)
        if versions_qs.exists():
            prev = versions_qs.latest('date')

    return redirect('exercise detail', pk=prev.pk)


@login_required
@user_passes_test(has_permission, login_url='/permissionDenied')
def next_version_view(request, pk):
    """
    Redirects to the least recent successive version of an exercise, or itself if there is none
    :param request:
    :param pk: the primary key of the current exercise
    """
    exercise = get_object_or_404(Exercise, pk=pk)
    if exercise.versionGroup is None:
        versions_qs = Exercise.objects.filter(versionGroup=exercise.pk)
    else:
        versions_qs = Exercise.objects.filter(Q(versionGroup=exercise.versionGroup.pk) | Q(pk=exercise.versionGroup.pk),
                                              date__gt=exercise.date)
    next_exercise = exercise
    if versions_qs.exists():
        next_exercise = versions_qs.earliest('date')
    return redirect('exercise detail', pk=next_exercise.pk)


def pdf_render_and_copy(user, exercise, clean_temp=True):
    """
    Renders a PDF of the exercise and copies the pdf file to the exercises directory.
    :param user: the user is needed to user the appropriate temp folder
    :param exercise: the exercise to render
    :param clean_temp: deletes all files in user's temp if True
    :return: returns True if the exercise was rendered, False otherwise
    """
    rendered = render_pdf(user, [exercise], include_solutions=True, header=exercise.documentHead,
                          clean_directory=clean_temp)
    if not rendered:
        return False
    else:
        work_dir = Path("ExamGenerator/media/temp/%s" % user.username)
        pdf_path = os.path.join(work_dir, 'document.pdf')

        exercise_path = settings.MEDIA_ROOT + '/exercises/exercise' + str(
            exercise.id)
        if not os.path.exists(exercise_path):
            os.makedirs(exercise_path)
        shutil.copy(pdf_path, exercise_path)
        return True


def copy_dependencies_to_workdir(user, exercise):
    """
    Copies the dependencies of an exercise to the user's temp folder.
    """

    work_dir = Path("ExamGenerator/media/temp/%s" % user.username)
    if not os.path.isdir(work_dir):
        os.makedirs(work_dir)
    exercise_dependencies_dir = settings.MEDIA_ROOT + '/exercises/exercise' + str(
        exercise.id) + '/file_dependencies'
    if os.path.exists(exercise_dependencies_dir):
        files = os.listdir(exercise_dependencies_dir)
        for f in files:
            shutil.copy(os.path.join(exercise_dependencies_dir, f),
                        work_dir)


def copy_dependencies(source_exercise, target_exercise):
    """
    Copies the dependencies of one exercise to the folder of the other exercise
    """
    source_exercise_dependencies_dir = settings.MEDIA_ROOT + '/exercises/exercise' + str(
        source_exercise.id) + '/file_dependencies'
    target_exercise_dependencies_dir = settings.MEDIA_ROOT + '/exercises/exercise' + str(
        target_exercise.id) + '/file_dependencies'
    if not os.path.exists(source_exercise_dependencies_dir):
        return
    if not os.path.exists(target_exercise_dependencies_dir):
        os.makedirs(target_exercise_dependencies_dir)
    for file in os.listdir(source_exercise_dependencies_dir):
        shutil.copy(os.path.join(source_exercise_dependencies_dir, file), target_exercise_dependencies_dir)


@login_required
@xframe_options_exempt
@user_passes_test(has_permission, login_url='/permissionDenied')
def exercise_detail_view(request, pk):
    """
    The detail view of a single exercise.
    :param request: current request
    :param pk: Primary key of the exercise
    """
    # Get the exercise and related objects
    exercise = get_object_or_404(Exercise, pk=pk)
    exercise_text_snippet = None
    solution_snippet = None
    redirect_to = pk
    if exercise.exerciseSolution:
        id_solution = exercise.exerciseSolution.pk
        solution_snippet = ExerciseSolution.objects.get(id=id_solution)
        solution_tex = solution_snippet.latex_code
    else:
        solution_tex = ''
    if exercise.exerciseText:
        id_exercise = exercise.exerciseText.pk
        exercise_text_snippet = ExerciseText.objects.get(id=id_exercise)

    # Initialize form
    data = {
        'header_choices': exercise.documentHead,
        'exerciseTex': exercise_text_snippet.latex_code,
        'solutionTex': solution_tex,
    }
    form = ExerciseDetailForm(initial=data)
    # the basic context
    context = {
        'form': form,
        'exerciseText': exercise_text_snippet,
        'solutionText': solution_snippet,
        'exercise': exercise,
        'pdfPath': '%sexercises/exercise%s/document.pdf?time=%s' % (
            settings.MEDIA_URL, exercise.pk, datetime.datetime.now())
    }
    context.update(create_template_context(request))

    if request.method == "POST":
        # If a POST request, get form data and create new exercise based on current one. Note that it isn't saved yet
        form = ExerciseDetailForm(request.POST, initial=data)
        new_exercise = Exercise(topic=exercise.topic, modifiable=exercise.modifiable,
                                points=exercise.points, versionGroup=exercise.getVersionGroup(),
                                documentHead=exercise.documentHead, exerciseText=exercise_text_snippet,
                                exerciseSolution=solution_snippet)

        if form.is_valid():
            # if nothing changed just redirect
            if not form.has_changed():
                return redirect('exercise detail', pk=pk)
            if request.POST.get('render_pdf'):
                # take the form data and file dependencies and render it into pdf
                exercise_tex = form.cleaned_data.get('exerciseTex')
                solution_tex = form.cleaned_data.get('solutionTex')
                document_head = form.cleaned_data.get('header_choices')
                clear_user_temp(request.user)
                copy_dependencies_to_workdir(request.user, exercise)
                uploaded = render_pdf(request.user, None, [(exercise_tex, solution_tex)], header=document_head,
                                      include_solutions=True, clean_directory=False)
                if not uploaded:
                    context_add_err_log(context, request.user, 'timeout_error')
                else:
                    # set initial data for form to input used for rendering, set pdf path to temp folder and render page
                    data = {
                        'header_choices': document_head,
                        'exerciseTex': exercise_tex,
                        'solutionTex': solution_tex,
                    }
                    form = ExerciseDetailForm(initial=data)
                    context.update({'pdfPath': '%stemp/%s/document.pdf' % (settings.MEDIA_URL, request.user.username),
                                    'form': form})
                    render_log_info(request.user, 'document.log', context)
                return render(request, 'exerciseDetail.html', context)
            # we get here when the user clicked on one of the 'save' buttons
            new_exercise_text = None
            new_solution = None
            redirect_to = exercise.pk
            # get all the changed data, create corresponding objects and update them in the new exercise
            if 'header_choices' in form.changed_data:
                new_document_head = form.cleaned_data.get('header_choices')

                new_exercise.documentHead = new_document_head

            if 'exerciseTex' in form.changed_data:
                input_tex = form.cleaned_data.get('exerciseTex')
                new_exercise_text = ExerciseText(language=exercise_text_snippet.language,
                                                 latex_code=input_tex,
                                                 versionGroup=exercise_text_snippet.getVersionGroup(),
                                                 author=request.user)
                new_exercise_text.save()

                new_exercise.exerciseText = new_exercise_text

            if 'solutionTex' in form.changed_data:
                input_tex = form.cleaned_data.get('solutionTex')
                if input_tex != '':
                    version_group = None
                    if solution_snippet:
                        version_group = solution_snippet.getVersionGroup()
                    new_solution = ExerciseSolution(language=exercise_text_snippet.language,
                                                    latex_code=input_tex,
                                                    versionGroup=version_group,
                                                    author=request.user)
                    new_solution.save()

                else:
                    new_solution = None
                new_exercise.exerciseSolution = new_solution

            # set  redirect target to new exercise
            new_exercise.save()
            redirect_to = new_exercise.pk

            # render pdf
            clear_user_temp(request.user)
            copy_dependencies_to_workdir(request.user, exercise)
            uploaded = pdf_render_and_copy(request.user, new_exercise, clean_temp=False)
            if not uploaded:
                # delete created objects from database if process timed out
                new_exercise.delete()
                new_exercise = None
                if new_solution:
                    new_solution.delete()
                if new_exercise_text:
                    new_exercise_text.delete()
                redirect_to = pk
            else:
                # copy file dependencies for newly created exercise
                if exercise != new_exercise:
                    copy_dependencies(exercise, new_exercise)
                # if save and replace, find old exercise in exam and replace with new one
                if request.POST.get('save_and_replace'):
                    exam_qs = Exam.objects.filter(author=request.user)
                    exam = None
                    if (len(exam_qs) > 0) & (new_exercise is not None):
                        exam = exam_qs.latest('creationDate')
                    else:
                        redirect('add exercise to exam', pk=redirect_to)
                    contains_exercise = exercise in exam.exercises.all()
                    if contains_exercise:
                        content_obj = Content.objects.filter(exam=exam, exercise=exercise)[0]
                        content_obj.exercise = new_exercise
                        content_obj.save()
                        return redirect('exam detail view')

            return redirect('exercise detail', pk=redirect_to)

        else:
            return redirect('exercise detail', pk=redirect_to)

    else:

        return render(request, 'exerciseDetail.html', context)


@login_required
@user_passes_test(has_permission, login_url='/permissionDenied')
def add_exercise_to_exam_view(request, pk):
    """
    Adds an exercise with primary key :param pk to the user's current exam.
    :param request:
    :param pk:
    :return: redirects to exam detail view
    """
    author = request.user
    exercise = get_object_or_404(Exercise, pk=pk)
    exam_qs = Exam.objects.filter(author=author)
    exam = None
    if len(exam_qs) == 0:
        exam = Exam.objects.create(author=author, documentHead=get_or_create_default_header(request.user))
        Content.objects.create(exam=exam, exercise=exercise, position=0)
    else:
        exam = exam_qs.latest('creationDate')
        exercise_count = Content.objects.filter(exam=exam).count()
        Content.objects.create(exam=exam, exercise=exercise, position=exercise_count)

    return redirect('exam detail view')


class LogView(TemplateView):
    """
    Displays the render log currently in the user's temp folder
    """
    template_name = 'renderLog.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(create_template_context(self.request))
        storage = DefaultStorage()
        user = self.request.user
        filename = 'document.log'
        if storage.exists('temp/%s/%s' % (user.username, filename)):
            log_file = open(storage.path('temp/%s/%s' % (user.username, filename)), encoding='utf-8')
            log = log_file.read()
            log_file.close()
            context.update({'log': log})
        else:
            context.update({'log': 'Could not find log'})
        return context


@method_decorator(login_required, name='dispatch')
class TopicExerciseListView(UserPassesTestMixin, ListView):
    """
    Displays all exercises of a given topic
    """
    model = Exercise
    paginate_by = 10
    template_name = 'exerciseList.html'
    context_object_name = 'exercises'

    def get_queryset(self):
        queryset = Exercise.objects.filter(topic=self.kwargs.get('pk')).order_by('-pk')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(create_template_context(self.request))
        return context

    def test_func(self):
        user = self.request.user
        groups = list(user.groups.all())
        group = list(Group.objects.filter(name='Employee'))[0]
        return group in groups or user.is_superuser or user.is_staff

    def handle_no_permission(self):
        return redirect('/permissionDenied')


@method_decorator(login_required, name='dispatch')
class HeaderListView(UserPassesTestMixin, ListView):
    """
    Displays all headers as a list
    """
    model = Header

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(create_template_context(self.request))
        return context

    def test_func(self):
        user = self.request.user
        groups = list(user.groups.all())
        group = list(Group.objects.filter(name='Employee'))[0]
        return group in groups or user.is_superuser or user.is_staff

    def handle_no_permission(self):
        return redirect('/permissionDenied')


@method_decorator(login_required, name='dispatch')
class HeaderUpdateView(UserPassesTestMixin, UpdateView):
    """
    This view handles editing of existing headers
    """
    model = Header
    form_class = HeaderForm
    template_name = 'header_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(create_template_context(self.request))
        return context

    def form_valid(self, form):
        return super().form_valid(form)

    def test_func(self):
        user = self.request.user
        groups = list(user.groups.all())
        group = list(Group.objects.filter(name='Employee'))[0]
        return group in groups or user.is_superuser or user.is_staff

    def handle_no_permission(self):
        return redirect('/permissionDenied')


@method_decorator(login_required, name='dispatch')
class HeaderDetailView(UserPassesTestMixin, DetailView):
    """
    Shows a header in detail
    """
    model = Header

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(create_template_context(self.request))
        return context

    def test_func(self):
        user = self.request.user
        groups = list(user.groups.all())
        group = list(Group.objects.filter(name='Employee'))[0]
        return group in groups or user.is_superuser or user.is_staff

    def handle_no_permission(self):
        return redirect('/permissionDenied')


@login_required
def index_view(request):
    context = {
        'error': "<div class=\"error-msg\" style=\"margin: 10px 0; padding: 10px;border-radius: 3px 3px 3px 3px;color:"
                 " #D8000C;background-color: #FFBABA;\"><i style=\"margin-right: 5px;\" class=\"fa fa-times-circle\">"
                 "</i>Wrong username or password.</div></div>"
    }
    context.update(create_template_context(request))
    return render(request, 'welcome.html', context)


def permission_denied_view(request):
    context = {
        'error': "<div class=\"error-msg\" style=\"margin: 10px 0; padding: 10px;border-radius: 3px 3px 3px 3px;color:"
                 " #D8000C;background-color: #FFBABA;\"><i style=\"margin-right: 5px;\" class=\"fa fa-times-circle\">"
                 "</i>Wrong username or password.</div></div>"
    }
    context.update(create_template_context(request))
    return render(request, 'permissionDenied.html', context)


@user_passes_test(can_change_rights)
def user_permissions_view(request):
    """
    Authorized user (admin or staff) can change the permission groups of other users on this page.
    :param request:
    :return:
    """
    user_form_set = modelformset_factory(User, fields=['groups'], extra=0)
    if request.method == 'POST':
        formset = user_form_set(request.POST)
        if formset.is_valid():
            formset.save()
            return redirect('user permissions')

    formset = user_form_set()
    context = create_template_context(request)
    context.update({'formset': formset})
    return render(request, 'userPermissions.html', context)


@login_required
@user_passes_test(has_permission, login_url='/permissionDenied')
def download_page_view(request):
    """
    The download page. Users can download PDFs and a zip Folder containing LaTeX and fileDependencies of their created exam.
    :param request:
    :return:
    """

    # Get the user's current exam
    exam_qs = Exam.objects.filter(author=request.user)
    if exam_qs.exists():
        exam = exam_qs.latest('creationDate')
    else:
        return redirect('exam detail view')
    # Get associated data
    exercises = Exercise.objects.filter(exam=exam).order_by('content__position')

    header = exam.documentHead
    context = create_template_context(request)
    # Render
    rendered = render_pdf(request.user, exercises, header=header, include_disclaimer=True, include_solutions=True,
                          document_name='ExamWithSolution.tex')
    if not rendered:
        context_add_err_log(context, request.user, 'err_with_solution')
    else:
        # Only render without solutions if rendering with solutions didn't throw time out exception
        rendered = render_pdf(request.user, exercises, header=header, include_disclaimer=True,
                              document_name='ExamWithoutSolution.tex', clean_directory=False)
        if not rendered:
            context_add_err_log(context, request.user, 'err_without_solution')

    directory_without_solution = Path(
        '%s/temp/%s/ExamWithoutSolution/' % (settings.MEDIA_ROOT, request.user.username)).absolute()
    directory_with_solution = Path(
        '%s/temp/%s/ExamWithSolution/' % (settings.MEDIA_ROOT, request.user.username)).absolute()

    if not os.path.exists(str(directory_without_solution)):
        os.makedirs(str(directory_without_solution))

    if not os.path.exists(str(directory_with_solution)):
        os.makedirs(str(directory_with_solution))

    for exercise in exercises:
        dependency_path = str(
            Path('%s/exercises/exercise%s/file_dependencies' % (settings.MEDIA_ROOT, str(exercise.id))))

        if os.path.exists(dependency_path):
            for file in os.listdir(dependency_path):
                copyPath = str(Path(str(dependency_path) + "/" + file))
                shutil.copy(copyPath, str(directory_without_solution))
                shutil.copy(copyPath, str(directory_with_solution))

    header_dependencies = '%s/headers/header%s' % (settings.MEDIA_ROOT, str(header.id))

    if os.path.exists(header_dependencies):
        for file in os.listdir(header_dependencies):
            copyPath = str(Path(str(header_dependencies) + "/" + file))
            shutil.copy(copyPath, str(directory_without_solution))
            shutil.copy(copyPath, str(directory_with_solution))

    # Link all created files
    exam_without_solution = '%stemp/%s/ExamWithoutSolution.pdf' % (settings.MEDIA_URL, request.user.username)
    exam_with_solution = '%stemp/%s/ExamWithSolution.pdf' % (settings.MEDIA_URL, request.user.username)
    latex_without_solution = Path(
        'ExamGenerator%stemp/%s/ExamWithoutSolution.tex' % (settings.MEDIA_URL, request.user.username)).absolute()
    latex_with_solution = Path(
        'ExamGenerator%stemp/%s/ExamWithSolution.tex' % (settings.MEDIA_URL, request.user.username)).absolute()

    shutil.copy(latex_without_solution, directory_without_solution)
    shutil.copy(latex_with_solution, directory_with_solution)

    zip_without_solution = '%s/temp/%s/ExamWithoutSolution' % (settings.MEDIA_URL, request.user.username)
    zip_with_solution = '%s/temp/%s/ExamWithSolution' % (settings.MEDIA_URL, request.user.username)

    shutil.make_archive(str(Path('ExamGenerator' + zip_without_solution).absolute()), 'zip', directory_without_solution)

    shutil.make_archive(str(Path('ExamGenerator' + zip_with_solution).absolute()), 'zip', directory_with_solution)

    context.update({'PDFWithSolution': exam_with_solution,
                    'PDFWithoutSolution': exam_without_solution,
                    'LatexWithSolution': zip_with_solution + '.zip',
                    'LatexWithoutSolution': zip_without_solution + '.zip'})
    return render(request, 'downloadPage.html', context)


@login_required
@user_passes_test(has_permission, login_url='/permissionDenied')
def remove_from_exam(request, position):
    """
    Removes the exercise at :param position from the user's current exam.
    :param request:
    :return: redirects to exam detail view
    """
    # Get the current exam
    exam_qs = Exam.objects.filter(author=request.user)
    if exam_qs.exists():
        current_exam = exam_qs.latest('creationDate')
    else:
        return redirect('exam detail view')
    # Remove exercise
    exercises = Content.objects.filter(exam=current_exam)
    exercises.filter(position=position).delete()
    # Decrement position of all following exercises by one
    following_exercises = exercises.filter(position__gt=position)
    for exercise in following_exercises:
        exercise.position -= 1
        exercise.save()
    return redirect('exam detail view')


@user_passes_test(has_permission, login_url='/permissionDenied')
@login_required
def exam_detail_view(request):
    """
    Displays the user's current exam. Users can change the exam's header.
    :param request:
    :return:
    """
    author = request.user
    exams_of_author = Exam.objects.filter(author=author)
    exam = None
    refresh_str = request.GET.get('refresh', 'False')
    context = {}
    if refresh_str == 'True':
        refresh = True
    else:
        refresh = False
    if len(exams_of_author) > 0:
        exam = exams_of_author.order_by('-creationDate')[0]
    else:
        exam = Exam(author=author, documentHead=get_or_create_default_header(request.user))
    content_exercises = Content.objects.filter(exam=exam).order_by('position')

    exam_form = ExamForm(initial={'documentHead': exam.documentHead})

    if request.method == "POST":
        exam_form = ExamForm(request.POST)
        if exam_form.is_valid():
            new_exam_header = exam_form.cleaned_data.get('documentHead')
            exam.documentHead = new_exam_header
            exam.save()
            url = reverse('exam detail view') + '?render=True'
            return redirect(url)

    if request.GET.get('render'):
        exercises = Exercise.objects.filter(exam=exam).order_by('content__position')
        exam_header = None
        if exam.documentHead:
            exam_header = exam.documentHead
        rendered = render_pdf(request.user, exercises, include_solutions=True, header=exam_header, document_name='exam')
        if not rendered:
            context_add_err_log(context, request.user, 'timeout_error')
        render_log_info(request.user, 'exam.log', context)

    context.update({
        'exercises': content_exercises,
        'exam_form': exam_form
    })
    context.update(create_template_context(request))
    storage = DefaultStorage()
    rendered = storage.exists('%s/temp/%s/exam.pdf' % (settings.MEDIA_ROOT, request.user))
    if rendered:
        context.update({'pdfPath': '%stemp/%s/%s?time=%s' % (
            settings.MEDIA_URL, request.user.username, 'exam.pdf', datetime.datetime.now())})
    return render(request, 'examScreen.html', context)


@csrf_protect
def sign_up_view(request):
    """
    Handles creation of new users.
    :param request:
    :return:
    """
    response = ""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        response = "Form was not filled out correctly"

        context = {
            'form': form}

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            confirm_password = form.cleaned_data.get('confirm_password')
            name = form.cleaned_data.get('name')
            mail = form.cleaned_data.get('mail')
            firstname = form.cleaned_data.get('firstname')
            users = User.objects.all()
            if password != confirm_password:
                form = SignUpForm(initial={'username': username,
                                           'name': name,
                                           'mail': mail,
                                           'firstname': firstname
                                           })
                context = {
                    'form': form,
                    'success': "<div class=\"error-msg\" style=\"margin: 10px 0; padding: 10px;border-radius: 3px 3px 3px 3px;color:"
                               " #D8000C;background-color: #FFBABA;\"><i style=\"margin-right: 5px;\" class=\"fa fa-times-circle\">"
                               "</i>Password confirmation failed.</div>"

                }
                context.update(create_template_context(request))
                return render(request, 'signUp.html', context)

            found = False
            response = "User already exists"

            for user in users:
                if user.username == username:
                    found = True
                    context.update({
                        'success': "<div class=\"error-msg\" style=\"margin: 10px 0; padding: 10px;border-radius: 3px 3px 3px 3px;color:"
                                   " #D8000C;background-color: #FFBABA;\"><i style=\"margin-right: 5px;\" class=\"fa fa-times-circle\">"
                                   "</i>User " + username + " already exists.</div>"})
                    break

            if not found:
                created_user = User.objects.create_user(username=username, email=mail, password=password,
                                                        last_name=name,
                                                        first_name=firstname)
                created_user.is_staff = False
                created_user.is_superuser = False

                context.update({
                    'success': "<div class=\"success-msg\" style=\" width: 275px;margin: 10px 0; padding: 10px;border-radius:"
                               " 3px 3px 3px 3px;color: #270;background-color: #DFF2BF;\"><i style=\"margin-right: 5px;\" "
                               "class=\"fa fa-check\"></i>Successfully created User " + username + ".</div></div>"})

        context.update(create_template_context(request))

        return render(request, 'signUp.html', context)

    else:
        form = SignUpForm()

        context = {
            'form': form,
            'response': response,
            'topics': Topic.objects.all()
        }
        context.update(create_template_context(request))

        return render(request, 'signUp.html', context)


@login_required
@user_passes_test(has_permission, login_url='/permissionDenied')
def topic_overview_view(request):
    """
    Displays all topics and if an exercise of a topic is currently in the user's exam.
    :param request:
    :return:
    """
    user = request.user
    exam_qs = Exam.objects.filter(author=user)
    exam_topics = []

    if exam_qs.exists():
        exam = exam_qs.latest('creationDate')
        exercise_qs = Exercise.objects.filter(exam=exam)
        if exercise_qs.exists():
            exercise_qs = exercise_qs.order_by('content__position')
        for exercise in exercise_qs:
            exam_topics.append(exercise.topic)

    context = {
        'examTopics': exam_topics
    }
    context.update(create_template_context(request))

    return render(request, 'topicOverview.html', context)


@login_required
@user_passes_test(has_permission, login_url='/permissionDenied')
def upload_exercise_view(request):
    """
    Handles the upload of headers and exercises as well as the creation of topics.
    Files are renamed on upload to avoid conflicts when rendering the exam.
    :param request:
    :return:
    """
    context = create_template_context(request).copy()
    headers = Header.objects.all()
    header_form = HeaderForm()
    context.update({'headers': headers, 'header_form': header_form})
    topics = Topic.objects.all()
    form = UploadForm()
    topic_form = TopicForm()
    response = ""

    if request.method == 'POST':
        # This simply creates a topic object with the form data
        if request.POST.get('submit_topic'):
            topic_form = TopicForm(request.POST or None)
            if topic_form.is_valid():
                topic_form.save()
                context.update({'imported_topic': True})
            else:
                context.update({'not_imported_topic': True})
        # This creates a header object from the form data
        elif request.POST.get('submit_header'):
            header_form = HeaderForm(request.POST or None, request.FILES or None)
            if header_form.is_valid():
                header = header_form.save(commit=False)
                # add the user to it as author
                header.author = request.user
                header.save()
                # get the file dependencies
                files = request.FILES.getlist('header_files')
                storage = DefaultStorage()
                for file in files:
                    # rename them, checking for occurrences with and without file type (i.e. .jpg etc) specified in
                    # the latex
                    new_file_name = 'header-%d-%s' % (header.id, file.name)
                    new_file_name_no_type, _, _ = new_file_name.rpartition('.')
                    new_file_name_no_type = '{' + new_file_name_no_type + '}'
                    name_no_type, _, _ = file.name.rpartition('.')
                    alt_file_name = '{' + name_no_type + '}'
                    header.latex_code = header.latex_code.replace(alt_file_name, new_file_name_no_type)
                    header.latex_code = header.latex_code.replace(file.name, new_file_name)
                    header.save()
                    # store them in the corresponding header folder
                    storage.save(
                        settings.MEDIA_ROOT + '/headers/header' + str(header.id) + '/' + new_file_name
                        , file)
                context.update({'imported_header': True})
            else:
                context.update({'not_imported_header': True})

        else:
            # the remaining possible post requests are for importing or rendering an exercise
            # importing only ever happens after rendering
            form = UploadForm(request.POST, request.FILES or None)
            if form.is_valid():
                # get data from form
                points = form.cleaned_data.get('points')
                solution_tex = form.cleaned_data.get('solutionTex')
                exercise_tex = form.cleaned_data.get('exerciseTex')
                header = form.cleaned_data.get('header_choices')

                if request.POST.get('submit_exercise'):
                    # get some more form data in case of import
                    topic = form.cleaned_data.get('topic_choices')
                    language = form.cleaned_data.get('languages')
                    modifiable = True

                    if form.cleaned_data.get('modifyable') != 'Yes':
                        modifiable = False

                    exercise_solution = None
                    # create solution object
                    if solution_tex:
                        exercise_solution = ExerciseSolution(latex_code=solution_tex,
                                                             language=language,
                                                             author=request.user)
                        exercise_solution.save()
                    # create exercise text object
                    exercise_text = ExerciseText(latex_code=exercise_tex,
                                                 language=language,
                                                 author=request.user)

                    exercise_text.save()

                    # create exercise object
                    exercise = Exercise(modifiable=modifiable, exerciseText=exercise_text,
                                        exerciseSolution=exercise_solution,
                                        topic=topic, points=points, documentHead=header)

                    exercise.save()
                    # get the file dependencies
                    work_dir = Path("ExamGenerator/media/temp/%s/" % request.user.username)
                    storage = DefaultStorage()
                    if os.path.isdir(work_dir):

                        # files are copied from temp folder, since it was rendered before
                        storage_work_dir = ("temp/%s/" % request.user.username)
                        exercise_path = Path(
                            "ExamGenerator/media/exercises/exercise%d/" % exercise.pk)
                        if not os.path.exists(exercise_path):
                            os.makedirs(exercise_path)
                        # copy the pdf to the exercise's folder
                        shutil.copy(os.path.join(work_dir, 'document.pdf'), exercise_path)
                        exercise_path = os.path.join(exercise_path, "file_dependencies/")
                        if not os.path.exists(exercise_path):
                            os.makedirs(exercise_path)
                        paths, files = storage.listdir(storage_work_dir)

                        # copy and rename all files and their occurrences in the tex
                        for file in files:
                            if file.startswith('exer-'):
                                tex_file_name = file.replace('exer-', '')
                                new_file_name = 'exer-%d-%s' % (exercise.id, tex_file_name)
                                new_file_name_no_type, _, _ = new_file_name.rpartition('.')
                                new_file_name_no_type = '{' + new_file_name_no_type + '}'
                                name_no_type, _, _ = tex_file_name.rpartition('.')
                                alt_file_name = '{' + name_no_type + '}'
                                dst_path = Path(settings.MEDIA_ROOT + '/exercises/exercise' + str(
                                    exercise.id) + '/file_dependencies/' + new_file_name)
                                src_path = os.path.join(work_dir, file)
                                shutil.copy(src_path, dst_path)
                                exercise_text.latex_code = exercise_text.latex_code.replace(alt_file_name,
                                                                                            new_file_name_no_type)
                                exercise_text.latex_code = exercise_text.latex_code.replace(tex_file_name,
                                                                                            new_file_name)
                                exercise_text.save()
                                if exercise_solution is not None:
                                    exercise_solution.latex_code = exercise_solution.latex_code.replace(tex_file_name,
                                                                                                        new_file_name)
                                    exercise_solution.latex_code = exercise_solution.latex_code.replace(alt_file_name,
                                                                                                        new_file_name_no_type)
                                    exercise_solution.save()

                        context.update({'imported': True})

                # render a pdf of the given latex and files
                elif request.POST.get('render_exercise'):
                    files = request.FILES.getlist('fileDependencies')
                    render_pdf(request.user, None, [(exercise_tex, solution_tex)], header=header,
                               files=files, include_solutions=True)
                    storage = DefaultStorage()
                    # rename the files for easier recognition when importing after this
                    for file in files:
                        file_name = "exer-" + file.name
                        storage.save(
                            "%s/temp/%s/%s" % (settings.MEDIA_ROOT, request.user, file_name), file)
                    render_log_info(request.user, 'document.log', context)
                    context_add_err_log(context, request.user, 'error')
                    context.update({'rendered': True})
                    context.update({'not_imported': True})
                    context.update({'pdf_path': "%stemp/%s/document.pdf?time=%s" % (
                        settings.MEDIA_URL, request.user.username, datetime.datetime.now())})

    context_base = {
        'upload': form,
        'response': response,
        'topic_form': topic_form
    }
    context.update(context_base)

    return render(request, 'uploadExercise.html', context)


@login_required
@user_passes_test(has_permission, login_url='/permissionDenied')
def new_exam_view(request):
    Exam.objects.create(author=request.user, documentHead=get_or_create_default_header(request.user))
    return redirect('index')


@login_required
@user_passes_test(has_permission, login_url='/permissionDenied')
def change_order_view(request):
    """
    Swaps the position of two exercises within the exam. The indices are given as query parameters in the url like this:
    ?oldInedx=X&newIndex=Y. Indices start at 0. The position of an exercise within in the exam is stored in the
    'Content' relation
    :param request:
    :return: In any case a redirect to the exam detail view is returned
    """
    # Get query parameters
    old_index = request.GET.get("oldIndex", 0)
    new_index = request.GET.get("newIndex", 0)
    if (old_index is None) or (new_index is None):
        return redirect('exam detail view')
    if old_index != new_index:
        # Check if user has exam
        exam_qs = Exam.objects.filter(author=request.user)
        if exam_qs.exists():
            exam = exam_qs.latest('creationDate')
        else:
            return redirect('exam detail view')
        # Swap positions
        content_old_index_qs = Content.objects.filter(position=old_index, exam=exam)
        content_new_index_qs = Content.objects.filter(position=new_index, exam=exam)
        if content_old_index_qs.exists() & content_old_index_qs.exists():
            content_old_index = content_old_index_qs[0]
            content_new_index = content_new_index_qs[0]
            content_old_index.position = new_index
            content_old_index.save()
            content_new_index.position = old_index
            content_new_index.save()

    return redirect('exam detail view')


@login_required
@user_passes_test(has_permission, login_url='/permissionDenied')
def remove_exercise_by_topic(request, pk):
    """
    Removes an exercise of the given topic from the current exam. Only works if the exam has at most one exercise of the
    topic.
    The url can contain an optional query ?return_to=URL providing a URL to redirect to after the request is processed.
    Defaults to topic overview.
    :param pk: the primary key of the topic
    :return: redirect to the site the user came from if given or topic overview
    """
    user = request.user
    topic = Topic.objects.get(pk=pk)
    exam_qs = Exam.objects.filter(author=user)
    return_to = request.GET.get('return_to')
    if return_to is None:
        return_to = reverse('topic overview')
    if exam_qs.exists():
        exam = exam_qs.latest('creationDate')
    else:
        return redirect(return_to)

    exercise_qs = Exercise.objects.filter(content__exam=exam, topic=topic)
    if len(exercise_qs) > 1:
        return redirect(return_to)
    else:
        # Remove exercise from exam and reduce index of all following exercise by one
        exercise = exercise_qs[0]
        exercise_content = Content.objects.get(exam=exam, exercise=exercise)
        exam_content = Content.objects.filter(exam=exam)
        following_exercises = exam_content.filter(position__gt=exercise_content.position)
        exercise_content.delete()
        for exercise in following_exercises:
            exercise.position -= 1
            exercise.save()

    return redirect(return_to)
