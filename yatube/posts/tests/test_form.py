from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Test_group',
            description='Описание')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()

    def create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый заголовок',
            'group': self.group.id}

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True)

        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создалась запись с заданным текстом и группой
        self.assertEqual(response.status_code, HTTPStatus.ОК)
        self.assertTrue(Post.objects.filter(*form_data).exists())
