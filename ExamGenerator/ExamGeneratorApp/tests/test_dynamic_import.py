import os
import random
import time

from .Selen import My_selenium_tests
from ..models import Header, Exercise


class Dynamic_import(My_selenium_tests):
    """
    Fixtures are used to preload some date before every test. We use a very basic fixture with only 2 users. One of them
    has the username:'super' and the password:'1234' and the other one username:'test' and the password:'1234'. Besides
    of that we have no data in our fixture and insert all the data we need, during our tests.
    """
    fixtures = ['2Users_noData.json']

    @classmethod
    def setUpClass(cls):

        # set to True to see an opening browser for each test in this class
        debug = False
        super().setUpClass(debug)

    def test_upload_new_header_with_valid_user(self):
        """
        Checks if the upload of a new header with a valid user works
        :return: asserts if something doesn't work otherwise it returns nothing
        """
        selenium = self.selenium

        self.login("super", "1234")

        # Navigate to Import
        import_button = selenium.find_element_by_xpath("//*[text()='Import']")
        import_button.click()

        """
        IMPORT_Header_TEST
        """

        # push add header button:
        add_header = selenium.find_element_by_xpath("//button[contains(text(),'Add header')]")
        add_header.click()

        # get the latex data for the example header
        example_head = open(
            os.path.join('ExamGeneratorApp', 'tests', 'sample_data_for_tests', 'test_header.txt'))
        all_of_it = example_head.read()
        example_head.close()

        # find field for headername and headersourcecode input
        name_header = selenium.find_element_by_xpath("//input[@placeholder='Name']")
        latex_code_header = selenium.find_element_by_xpath("//textarea[@name='latex_code']")

        # insert data in the fields
        name_header.send_keys('Header 1')
        latex_code_header.send_keys(all_of_it)

        # find submit button and store new header in the db
        selenium.find_element_by_xpath('//input[@value="Submit header"]').click()

        # scroll to header selection
        header_selector = selenium.find_element_by_xpath("//select[@name='header_choices']")
        script_to_scroll = "window.scrollTo(" + str(header_selector.location['x']) + "," + (
            str(int(header_selector.location['y']) - 150)) + ")"
        selenium.execute_script(script_to_scroll)

        # check if the header got created
        header_selector_with_option = selenium.find_element_by_xpath(
            "//select[@name='header_choices']/option[text()='Header 1']")
        header_selector.click()
        header_selector_with_option.click()
        self.assertEquals(len(Header.objects.all()), 1)

        # navigate to navbar
        navbar = selenium.find_element_by_xpath("//button[@data-toggle='collapse']")
        navbar.click()

        # navigate to header section
        headers_section = selenium.find_element_by_xpath("//a[@href='/headers']")
        time.sleep(1)
        script_to_scroll = "window.scrollTo(" + str(headers_section.location['x']) + "," + (
            str(int(headers_section.location['y']) - 150)) + ")"
        selenium.execute_script(script_to_scroll)
        headers_section.click()

        # navigate to newly created header
        h2 = selenium.find_element_by_xpath("//a[@href='/header/1 ']")
        h2.click()

        # edit newly created header
        h2_edit = selenium.find_element_by_xpath("//a[@href='/header/1/edit']")
        h2_edit.click()

        # check if new header has name and code as specified
        h2_edit_screen_name = selenium.find_element_by_xpath("//input[@value='Header 1']")
        self.assertEquals(h2_edit_screen_name.get_attribute("value"), "Header 1")
        h2_edit_screen_snippet = selenium.find_element_by_id("id_latex_code")
        self.assertEquals(h2_edit_screen_snippet.get_attribute("value"), all_of_it)

        # send new values (added to old values)
        h2_edit_screen_name.send_keys("New name test")
        h2_edit_screen_snippet.send_keys("New latex Code")

        # save new values
        h2_edit_screen_save = selenium.find_element_by_xpath("//input[@type='submit']")
        h2_edit_screen_save.click()

        # go back to edit screen of header
        h2_edit = selenium.find_element_by_xpath("//a[@href='/header/1/edit']")
        h2_edit.click()

        # check if changes to header name and header snippet code got applied
        h2_edit_screen_name = selenium.find_element_by_xpath("//input[@id='id_name']")
        self.assertEquals("Header 1New name test", h2_edit_screen_name.get_attribute("value"))
        h2_edit_screen_snippet = selenium.find_element_by_id("id_latex_code")
        expected_snippet_code = all_of_it + "New latex Code"
        self.assertEquals(h2_edit_screen_snippet.get_attribute("value"), expected_snippet_code)

    def test_access_import_page_with_noRightsUser(self):
        """
        Test tries to access the import page with a user who has no rights to acces it.
        :return: asserts if the permission denied dialog was not shown
        """
        selenium = self.selenium

        self.login("test", "1234")

        """
        Access import page test
        """

        # Navigate to Import
        import_button = selenium.find_element_by_xpath("//*[text()='Import']")
        import_button.click()

        # check for permission denied message (throws an error if message is not visible)
        selenium.find_element_by_xpath("//*[contains(text(),'Permissions denied')]")

    def test_access_generate_page_with_noRightsUser(self):
        """
        Test tries to access the generate page with a user who has no rights to acces it.
        :return: asserts if the permission denied dialog was not shown
        """
        selenium = self.selenium

        self.login("test", "1234")

        """
        Access generate page test
        """
        # Navigate to Exercises
        import_button = selenium.find_element_by_xpath("//*[text()='Exercises']")
        import_button.click()

        # check for permission denied message (throws an error if message is not visible)
        selenium.find_element_by_xpath("//*[contains(text(),'Permissions denied')]")

    def test_access_generate_page_with_superuser(self):
        """
        Test tries to access the generate page with superuser
        :return: asserts if access was not successful
        """
        selenium = self.selenium

        self.login("test", "1234")

        """
        Access generate page test
        """

        # Navigate to Exercises
        import_button = selenium.find_element_by_xpath("//*[text()='Exercises']")
        import_button.click()

        self.find_href("/examScreen").click()

    def test_add_newTopic(self):
        """
        Test tries to create a new topic and checks if it got created properly
        :return: asserts if creation at some point was not successful
        """
        selenium = self.selenium

        self.login("super", "1234")

        """
        Add new topic test
        """

        # Navigate to Import
        import_button = selenium.find_element_by_xpath("//*[text()='Import']")
        import_button.click()

        # find field for topic name
        name_topic = selenium.find_element_by_xpath("//input[@placeholder='Topic name']")

        # insert data in the fields
        value_topic = "Topic one"
        name_topic.send_keys(value_topic)

        # find add button and store new topic in the db
        selenium.find_element_by_xpath('//input[@value="Add"]').click()

        # navigate to navigation bar
        navbar = selenium.find_element_by_xpath("//button[@data-toggle='collapse']")
        navbar.click()

        # check if new topic is a part of the navbar
        new_topic_in_navbar = selenium.find_element_by_xpath(f"//div[contains(text(),'{value_topic}')]")
        self.assertEqual(value_topic, new_topic_in_navbar.text)

        # navigate to exercise page of the newly generated topic
        self.find_href("/topic/1/exerciseList").click()

        # check that no exercises are currently present
        self.assertEqual(len(Exercise.objects.all()), 0)

    def test_add_newTopic_and_Exercise_to_that_Topic_and_create_Exam(self):
        """
        (Somehow summarises all above tests and a test for exercise importation and exam generation.)
        Test creates a header, 3 new topics and for every topic one exercise. Afterwards it moves adds one exercise 
        of each topic to the exam and then downloads the exam.
        :return: asserts if creation was at some point not successful. See error message for further details
        """
        selenium = self.selenium

        self.login("super", "1234")

        # Navigate to Import
        import_button = selenium.find_element_by_xpath("//*[text()='Import']")
        import_button.click()

        """
        Add 3 topics
        """

        i = 0
        # create 3 topics
        while i < 3:
            # find field for topicname and clear it
            name_topic = selenium.find_element_by_xpath("//input[@placeholder='Topic name']")
            name_topic.clear()

            # insert data in the fields
            value_topic = "Topic " + str(i)
            name_topic.send_keys(value_topic)

            # find add button and store new topic in the db
            selenium.find_element_by_xpath('//input[@value="Add"]').click()

            i += 1

        """
        Insert a header which can be used
        """

        # insert a header to use :

        # push add header button:
        add_header = selenium.find_element_by_xpath("//button[contains(text(),'Add header')]")
        add_header.click()

        # get the latex data for the example header
        example_head = open(
            os.path.join('ExamGeneratorApp', 'tests', 'sample_data_for_tests', 'test_header.txt'))
        all_of_it = example_head.read()
        example_head.close()

        # find field for header name and header sourcecode input
        name_header = selenium.find_element_by_xpath("//input[@placeholder='Name']")
        latex_code_header = selenium.find_element_by_xpath("//textarea[@name='latex_code']")

        # insert data in the fields
        name_header.send_keys('Header 1')
        latex_code_header.send_keys(all_of_it)

        # find dependencies upload
        dependencies_upload = selenium.find_element_by_xpath("//input[@id='id_header_files']")
        dependencies_upload.send_keys(os.getcwd() + "/ExamGeneratorApp/tests/sample_data_for_tests/CS-UdS-logo.jpg")

        # find submit button and store new header in the db
        selenium.find_element_by_xpath('//input[@value="Submit header"]').click()

        """
        Add 3 exercises (one to each topic)
        """

        # add exercises to each topic :
        points = []
        i = 0
        while i < 3:
            # scroll to header selection and choose Header
            header_selector = selenium.find_element_by_xpath("//select[@name='header_choices']")
            script_to_scroll = "window.scrollTo(" + str(header_selector.location['x']) + "," + (
                str(int(header_selector.location['y']) - 150)) + ")"
            selenium.execute_script(script_to_scroll)

            header_selector_with_option = selenium.find_element_by_xpath(
                "//select[@name='header_choices']/option[text()='Header 1']")
            header_selector.click()
            header_selector_with_option.click()

            # scroll to reachable points,clear it  and insert Value
            reachable_points_field = selenium.find_element_by_xpath("//input[@id='id_points']")
            reachable_points_field.clear()
            points.append(random.randint(1, 100))
            reachable_points_field.send_keys(points[i])

            # select topic
            value_topic = "Topic " + str(i)
            topic_selecter_with_option = selenium.find_element_by_xpath(
                f"//select[@name='topic_choices']/option[text()='{value_topic}']")
            topic_selecter_with_option.click()

            # scroll to exercise input
            exercise_latex_input = selenium.find_element_by_xpath("//*[@placeholder='Exercise Latex']")
            script_to_scroll = "window.scrollTo(" + str(exercise_latex_input.location['x']) + "," + (
                str(int(exercise_latex_input.location['y']) - 150)) + ")"
            selenium.execute_script(script_to_scroll)

            # send values to exercise latex and solution latex (clear it before)
            solution_latex_input = selenium.find_element_by_xpath("//*[@placeholder='Solution Latex']")
            exercise_value = "Exercise " + str(i)
            solution_value = "Solution " + str(i)
            solution_latex_input.clear()
            exercise_latex_input.clear()
            exercise_latex_input.send_keys(exercise_value)
            solution_latex_input.send_keys(solution_value)

            i += 1

            # find render button,scroll to it and click it
            render_exercise = selenium.find_element_by_xpath("//input[@name='render_exercise']")
            script_to_scroll = "window.scrollTo(" + str(render_exercise.location['x']) + "," + (
                str(int(render_exercise.location['y']) - 150)) + ")"
            selenium.execute_script(script_to_scroll)
            render_exercise.click()

            # find import button and click it
            import_exercise = selenium.find_element_by_xpath("//input[@value='Import exercise']")
            time.sleep(1)
            import_exercise.click()

            time.sleep(2)

        # check if exercises got imported and safed correctly
        i = 0
        exercise_list = Exercise.objects.all()
        while i < 3:
            expected_latex_code_value = "Exercise " + str(i)
            expected_solution_code_value = "Solution " + str(i)
            value_topic = "Topic " + str(i)
            exercise = exercise_list[i]
            self.assertEqual(expected_latex_code_value, exercise.exerciseText.latex_code)
            self.assertEqual(expected_solution_code_value, exercise.exerciseSolution.latex_code)
            self.assertTrue(exercise.modifiable)
            self.assertEqual(exercise.points, points[i])
            self.assertEqual(exercise.topic.name, value_topic)
            self.assertEqual(exercise.exerciseText.author.username, 'super')
            self.assertEqual(exercise.exerciseSolution.author.username, 'super')
            i += 1

        """
        Add one exercise for each topic to the exam
        """

        # navigate to navigation bar
        navbar = selenium.find_element_by_xpath("//button[@data-toggle='collapse']")
        navbar.click()

        topic1_exercise_list = selenium.find_element_by_xpath("//a[@href='/topic/1/exerciseList']")
        topic1_exercise_list.click()

        exercise_1_add = selenium.find_element_by_xpath("//a[contains(text(),'Add to exam')]")
        exercise_1_add.click()

        # navigate to navigation bar
        navbar = selenium.find_element_by_xpath("//button[@data-toggle='collapse']")
        navbar.click()

        topic2_exercise_list = selenium.find_element_by_xpath("//a[@href='/topic/2/exerciseList']")
        topic2_exercise_list.click()

        exercise_2_add = selenium.find_element_by_xpath("//a[contains(text(),'Add to exam')]")
        exercise_2_add.click()

        # navigate to navigation bar
        navbar = selenium.find_element_by_xpath("//button[@data-toggle='collapse']")
        navbar.click()

        topic3_exercise_list = selenium.find_element_by_xpath("//a[@href='/topic/3/exerciseList']")
        topic3_exercise_list.click()

        exercise_3_add = selenium.find_element_by_xpath("//a[contains(text(),'Add to exam')]")
        exercise_3_add.click()

        """
        save the header which should be used for the exam
        """
        # find header selecter
        header_selector = selenium.find_element_by_xpath("//select[@id='id_documentHead']")
        header_selector.click()

        # choose the option for the header which got uploaded in this test
        header_selector_with_option = selenium.find_element_by_xpath(
            "//select[@id='id_documentHead']/option[text()='Header 1']")
        header_selector_with_option.click()

        # save the chosen header
        save_header = selenium.find_element_by_xpath("//input[@value='Save selection']")
        save_header.click()

        """
        Download the created exam
        """

        # continue to download page
        continue_to_download = selenium.find_element_by_xpath("//*[contains(text(),'Continue to download')]")
        continue_to_download.click()

        # push download button
        download_without_solution = selenium.find_element_by_xpath(
            "//a[@href='/media/temp/super/ExamWithoutSolution.pdf']")
        download_without_solution.click()
