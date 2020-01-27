from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse


def get_sentinel_user():
    return get_user_model().objects.get_or_create(username='deleted')[0]


class Topic(models.Model):
    name = models.CharField(max_length=300, verbose_name='Topic', unique=True)

    def __str__(self):
        return self.name


class FileDependency(models.Model):
    file = models.FileField(upload_to='dependencies/')


class LatexSnippet(models.Model):
    """
    Explanation of versionGroup: This is used to create versions of latex snippets. All snippets that are somehow based
    off of each other, point to a single latex snippet through the versionGroup attribute. The next and previous snippet
    can than be found by grouping by the versionGroup and looking at the date attribute. When creating a new version
    one can simply pass the snippet it is based on as parameter and the save method takes care of it.
    """
    class Meta:
        # this is abstract so you cannot create an instance of LatexSnippet, only the classes inheriting from it
        abstract = True

    date = models.DateTimeField(auto_now_add=True)
    versionGroup = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, unique_for_date='date')
    latex_code = models.TextField()
    languageChoices = (
        ('DE', 'German'),
        ('EN', 'English')
    )
    language = models.TextField(choices=languageChoices, default='German')
    author = models.ForeignKey(get_user_model(), on_delete=models.SET(get_sentinel_user))
    files = models.ManyToManyField(FileDependency, blank=True)

    def save(self, *args, **kwargs):
        if self.versionGroup is None:
            # no versionGroup given, so it stays None
            super().save(*args, **kwargs)
        elif self.versionGroup.versionGroup is None:
            # the snippet used as base is not a version of anything, so we point to it
            super().save(*args, **kwargs)
        else:
            # the snippet used as base is a version of another snippet, so we use that pointer as our common
            # base element
            self.versionGroup = self.versionGroup.versionGroup
            super().save(*args, **kwargs)

    def getVersionGroup(self):
        if self.versionGroup is None:
            return self
        else:
            return self.versionGroup

    def __str__(self):
        return self.latex_code


class Header(LatexSnippet):
    name = models.TextField(max_length=150, verbose_name='name', default='', unique=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('header detail view', kwargs={'pk': self.pk})


class ExerciseSolution(LatexSnippet):
    pass


class ExerciseText(LatexSnippet):
    pass


class Exercise(models.Model):
    """
    The versionGroup attribute here works the exact same as it does for latex snippet.
    """
    date = models.DateTimeField(auto_now_add=True)
    versionGroup = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, unique_for_date='date')
    documentHead = models.ForeignKey(Header, on_delete=models.PROTECT)
    modifiable = models.BooleanField()
    points = models.IntegerField()
    exerciseSolution = models.ForeignKey(ExerciseSolution,
                                         on_delete=models.SET_NULL,
                                         null=True,
                                         blank=True)
    exerciseText = models.ForeignKey(ExerciseText,
                                     on_delete=models.SET_NULL,
                                     null=True)
    topic = models.ForeignKey(Topic,
                              on_delete=models.SET_NULL,
                              null=True)

    def get_absolute_url(self):
        return reverse('exercise detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.exerciseText.__str__() + "\n Solution :" + self.exerciseSolution.__str__()

    def getVersionGroup(self):
        if self.versionGroup is None:
            return self
        else:
            return self.versionGroup

    def save(self, *args, **kwargs):
        if self.versionGroup is None:
            super().save(*args, **kwargs)
        elif self.versionGroup.versionGroup is None:
            super().save(*args, **kwargs)
        else:
            self.versionGroup = self.versionGroup.versionGroup
            super().save(*args, **kwargs)


class Exam(models.Model):
    exercises = models.ManyToManyField(Exercise, through='Content')
    creationDate = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(get_user_model(), on_delete=models.SET(get_sentinel_user))
    documentHead = models.ForeignKey(Header, on_delete=models.PROTECT, null=True)


class Content(models.Model):
    """
    This the table specifying which exercises are at which position in an exam.
    """
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    position = models.IntegerField()
