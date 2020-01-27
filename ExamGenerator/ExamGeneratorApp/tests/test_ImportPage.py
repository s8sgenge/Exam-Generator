import os

from django.test import TestCase

from ..forms import UploadForm, HeaderForm, TopicForm


class Test_ImportPage(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_solutionTex_initial(self):
        """
        Checks the initial values/attributes of the textarea for the solution of an exercise
        :return: asserts if something went wrong. See assertion message for further infos.
        """
        import_form = UploadForm()
        self.assertTrue(import_form.fields['solutionTex'].label == 'Solution Latex')
        self.assertFalse(import_form.fields['solutionTex'].required)
        self.assertTrue(import_form.fields['solutionTex'].widget.attrs['placeholder'] == 'Solution Latex')
        self.assertTrue(import_form.fields['solutionTex'].widget.attrs['rows'] == '8')

    def test_exerciseTex_initial(self):
        """
        Checks the initial values/attributes of the textarea for the exercise-text of an exercise
        :return: asserts if something went wrong. See assertion message for further infos.
        """
        import_form = UploadForm()
        self.assertTrue(import_form.fields['exerciseTex'].label == 'Exercise Latex')
        self.assertTrue(import_form.fields['exerciseTex'].required)
        self.assertTrue(import_form.fields['exerciseTex'].widget.attrs['placeholder'] == 'Exercise Latex')
        self.assertTrue(import_form.fields['exerciseTex'].widget.attrs['rows'] == '8')

    def test_topic_choices_initial(self):
        """
        Checks the initial values/attributes of the topic selector
        :return: asserts if something went wrong. See assertion message for further infos.
        """
        import_form = UploadForm()
        self.assertTrue(import_form.fields['topic_choices'].empty_label == 'Select a Topic')
        self.assertTrue(import_form.fields['topic_choices'].required)

    def test_header_choices_initial(self):
        """
        Checks the initial values/attributes of the header selector
        :return: asserts if something went wrong. See assertion message for further infos.
        """
        import_form = UploadForm()
        self.assertTrue(import_form.fields['header_choices'].empty_label == 'Select a Documenthead')
        self.assertTrue(import_form.fields['header_choices'].required)

    def test_points_initial(self):
        """
        Checks the initial values/attributes of the points input field
        :return: asserts if something went wrong. See assertion message for further infos.
        """
        import_form = UploadForm()
        self.assertTrue(import_form.fields['points'].widget.attrs['placeholder'] == 'Enter number of reachable points')

    def test_fileDependencies_initial(self):
        """
        Checks the initial values/attributes of the file dependencies
        :return: asserts if something went wrong. See assertion message for further infos.
        """
        import_form = UploadForm()
        self.assertFalse(import_form.fields['fileDependencies'].required)

    def test_languages_initial(self):
        """
        Checks the initial values/attributes of the selector for the language
        :return: asserts if something went wrong. See assertion message for further infos.
        """
        import_form = UploadForm()
        all_available_languages = set(map(lambda x: x[1], import_form.fields['languages'].choices))
        self.assertTrue(all_available_languages.__contains__('German'))
        self.assertTrue(all_available_languages.__contains__('English'))
        self.assertTrue(import_form.fields['languages'].required)

    def test_modifyable_inital(self):
        """
        Checks the initial values/attributes of the selector for modifyability
        :return: asserts if something went wrong. See assertion message for further infos.
        """
        import_form = UploadForm()
        all_available_options = set(map(lambda x: x[1], import_form.fields['modifyable'].choices))
        self.assertTrue(all_available_options.__contains__('Modifiable'))
        self.assertTrue(all_available_options.__contains__('Not Modifiable'))
        self.assertEqual(len(all_available_options), 2)
        self.assertTrue(import_form.fields['modifyable'].required)
        pass

    def test_header_initial(self):
        """
        Checks the initial values/attributes of the header upload area
        :return: asserts if something went wrong. See assertion message for further infos.
        """
        import_form = HeaderForm()
        self.assertTrue(import_form.fields['name'].widget.attrs['placeholder'] == 'Name')
        self.assertTrue(import_form.fields['latex_code'].widget.attrs[
                            'placeholder'] == 'This has to include all parts of the latex document that you would put the exercise in up ' \
                                              'until the exercise starts (i.e. all libraries, the page header if needed,' \
                                              ' \'\\begin{document}\', disclaimer)')
        self.assertTrue(import_form.fields['latex_code'].required)
        self.assertTrue(import_form.fields['name'].required)

    def test_topic_form_initial(self):
        """
        Checks the initial values/attributes of the topic name input
        :return:
        """
        import_form = TopicForm()
        self.assertTrue(import_form.fields['name'].widget.attrs['placeholder'] == 'Topic name')

    def test_upload_new_header_invalid_because_of_missing_name(self):
        """
        Checks if the upload of a header without name is possible
        :return: asserts if the upload is possible
        """
        example_head = open(os.path.join('ExamGeneratorApp', 'tests', 'sample_data_for_tests', 'test_header.txt'))
        all_of_it = example_head.read()
        import_form = HeaderForm(
            data={'latex_code': all_of_it}
        )
        self.assertFalse(import_form.is_valid())

    def test_upload_new_header_invalid_because_of_missing_snippet(self):
        """
        Checks if the upload of a header without latex code is possible
        :return: asserts if the upload is possible
        """
        import_form = HeaderForm(
            data={'name': "Header1"}
        )
        self.assertFalse(import_form.is_valid())
