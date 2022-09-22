from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post, User

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаём тестовую запись в БД
        # и сохраняем созданную запись в качестве переменной класса.
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тест группа',
            slug='Тест слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тест пост',
        )

    def test_models_have_correct_object_names(self):
        """Содержимое поля title преобразуется в slug."""
        group = PostModelTest.group
        group_title = group.title
        post = PostModelTest.post
        post_title = post.text[:15]
        expected_str = {
            group: group_title,
            post: post_title
        }

        for model, expected_value in expected_str.items():
            with self.subTest(model=model):
                self.assertEqual(expected_value, str(model))
