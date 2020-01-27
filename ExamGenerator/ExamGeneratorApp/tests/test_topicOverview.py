from django.test import TestCase

from ..models import Topic


class Test_Topic_name(TestCase):
    @classmethod
    def setUpTestData(cls):
        Topic.objects.create(name='ER')

    def test_topic_name(self):
        topic = Topic.objects.get(name='ER')
        field_label = topic.name
        self.assertEquals(field_label, 'ER')
