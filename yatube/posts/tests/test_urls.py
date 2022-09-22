from http import HTTPStatus
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, User, Comment


class PostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД
        cls.user = User.objects.create_user(username='Author')
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='slug',
            description='Описание',
            pub_date='31 июля 1854',
        )
        cls.post = Post.objects.create(
            pub_date='31 июля 1854',
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_guest_client(self):
        pages_list = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': 'Author'})
        ]
        for page in pages_list:
            response = self.guest_client.get(page)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_client(self):
        pages_list = (reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}),
            reverse('posts:post_create'))
        for page in pages_list:
            response = self.authorized_client.get(page)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexiting_url_exists_at_desired_location(self):
        """Страница /unexiting_page/ доступна любому пользователю."""
        response = self.guest_client.get('/unexiting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={
                'username': 'Author'}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                'post_id': self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.id}): 'posts/post_create.html',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(template)
                self.assertTemplateUsed(response, address)

    def test_page_404(self):
        response = self.guest_client.get('/jff61/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
  

class TestComment(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create_user(username='Leo')
        cls.post = Post.objects.create(
            pub_date='31 июля 1854',
            author=cls.user_1,
            text='Тестовый текст',
            
        )
    
    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()


    def test_comment_guest_client(self):
        response = self.guest_client.get(reverse(
            'posts:add_comment', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
