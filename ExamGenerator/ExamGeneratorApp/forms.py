import sys

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms import ModelForm

from .models import Topic, Header, Exam


class SignUpForm(forms.Form):
    username = forms.CharField(label='Username', max_length=300,
                               widget=forms.TextInput(attrs={'class': 'form-control'}))
    name = forms.CharField(label='Name', max_length=300, widget=forms.TextInput(attrs={'class': 'form-control'}))
    mail = forms.CharField(label='Mail', max_length=300, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Password', max_length=300,
                               widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(label='Confirm Password', max_length="300",
                                       widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    firstname = forms.CharField(label='Firstname', max_length=300,
                                widget=forms.TextInput(attrs={'class': 'form-control'}))


class UploadForm(forms.Form):
    languageChoices = (
        ('DE', 'German'),
        ('EN', 'English')
    )
    modifiable = (('Yes', 'Modifiable'),
                  ('No', 'Not Modifiable')
                  )
    placeholder = 'This has to include all parts of the latex document that you would put the exercise in up ' \
                  'until the exercise starts (i.e. all libraries, commands, page header,\'\\begin{document}\''
    solutionTex = forms.CharField(label='Solution Latex', max_length=sys.maxsize, required=False, widget=forms.Textarea(
        attrs={'class': 'form-control', 'placeholder': 'Solution Latex', 'rows': '8'}))
    exerciseTex = forms.CharField(label='Exercise Latex', max_length=sys.maxsize, widget=forms.Textarea(
        attrs={'class': 'form-control', 'placeholder': 'Exercise Latex', 'rows': '8'}))
    topic_choices = forms.ModelChoiceField(Topic.objects.all(), empty_label='Select a Topic',
                                           widget=forms.Select(attrs={'class': 'form-control'}))
    header_choices = forms.ModelChoiceField(Header.objects.all(),
                                            empty_label='Select a Documenthead',
                                            widget=forms.Select(attrs={'class': 'form-control'}))
    points = forms.CharField(label='Points FORM', max_length=30, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Enter number of reachable points'}))
    fileDependencies = forms.FileField(required=False, widget=forms.ClearableFileInput(
        attrs={'multiple': True}))
    languages = forms.ChoiceField(choices=languageChoices, widget=forms.Select(attrs={'class': 'form-control'}))
    modifyable = forms.ChoiceField(choices=modifiable,
                                   widget=forms.Select(attrs={'class': 'form-control'}))


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'autofocus': True, 'class': 'form-control', 'placeholder': 'Topic name'})}


class HeaderForm(forms.ModelForm):
    class Meta:
        model = Header
        fields = ['name', 'latex_code']

    header_files = forms.FileField(required=False, widget=forms.ClearableFileInput(
        attrs={'multiple': True}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholder = 'This has to include all parts of the latex document that you would put the exercise in up ' \
                      'until the exercise starts (i.e. all libraries, the page header if needed,' \
                      ' \'\\begin{document}\', disclaimer)'
        self.fields['latex_code'].widget = forms.Textarea(
            attrs={'class': 'form-control', 'placeholder': placeholder, 'rows': '8'})
        self.fields['name'].widget = forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Name'})


class ExerciseDetailForm(forms.Form):
    exerciseTex = forms.CharField(label='Exercise Latex', max_length=sys.maxsize,
                                  widget=forms.Textarea(attrs={'class': 'form-control'}))
    solutionTex = forms.CharField(label='Solution Latex', max_length=sys.maxsize,
                                  widget=forms.Textarea(attrs={'class': 'form-control'}), required=False)
    header_choices = forms.ModelChoiceField(Header.objects.all(),
                                            empty_label='Select a Documenthead',
                                            widget=forms.Select(attrs={'class': 'form-control'}))


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget = forms.TextInput(
            attrs={'autofocus': True, 'class': 'form-control', 'placeholder': 'Username'})
        self.fields['password'].widget = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})


class ExamForm(ModelForm):
    class Meta:
        model = Exam
        fields = ['documentHead']
