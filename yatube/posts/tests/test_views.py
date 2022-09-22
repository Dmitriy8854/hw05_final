import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, User, Follow, Comment


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Leo3')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def check_post_info(self, post):
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group.id, self.post.group.id)
            self.assertEqual(post.image, self.post.image)


class PostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД
        cls.user = User.objects.create_user(username='Leo')
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
        # Создаем авторизованный и неавторизованный клиенты
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={
                'username': 'Leo'}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                'post_id': self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.id}): 'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html',

        }
        # Проверяем, что при обращении к name вызывается HTML-шаблон
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def asserting_test_post(self, post):
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group.id, self.post.group.id)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        self.asserting_test_post(response.context['page_obj'][0])

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        self.assertEqual(response.context['group'], self.group)
        self.asserting_test_post(response.context['page_obj'][0])

    def test_group_list_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': 'Leo'}))
        self.assertEqual(response.context['author'], self.user)
        self.asserting_test_post(response.context['page_obj'][0])


class TestPaginator(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Leo')
        cls.group = Group.objects.create(
            title='title', description='description', slug='newslug'
        )
        CONST = 13
        Post.objects.bulk_create(
            Post(
                text=f'Текст поста #{i}', author=cls.user, group=cls.group
            ) for i in range(CONST)
        )
        cls.pages_list = (reverse('posts:index'),
                          reverse('posts:group_list', kwargs={
                              'slug': cls.group.slug}),
                          reverse('posts:profile', kwargs={'username': 'Leo'})
                          )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):

        for page in self.pages_list:
            response = self.authorized_client.get(page)
            self.assertEqual(
                len(response.context['page_obj']), settings.POSTS_NUM
            )

    def test_second_page_contains_three_records(self):

        for page in self.pages_list:
            response = self.authorized_client.get(page + '?page=2')
            self.assertEqual(len(response.context['page_obj']), 3)


class TestCache(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Leo')
        cls.post = Post.objects.create(
            pub_date='31 июля 1854',
            author=cls.user,
            text='Тестовый текст',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index(self):
        """Тест кэширования index"""
        one_step = self.authorized_client.get(reverse('posts:index'))
        post_new = Post.objects.get(pk=1)
        post_new.text = 'Текст после изменений'
        post_new.save()
        two_step = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(one_step.content, two_step.content)
        cache.clear()
        tri_step = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(one_step.content, tri_step.content)


class TestFollow(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.follower_client = Client()
        self.following_client = Client()
        self.user_follower = User.objects.create_user(username='Подписчик')
        self.user_following = User.objects.create_user(username='Автор')
        self.follower_client.force_login(self.user_follower)
        self.following_client.force_login(self.user_following)

    def test_follow(self):
        follow_cont = Follow.objects.count()
        self.follower_client.post(reverse(
            'posts:profile_follow', kwargs={'username': self.user_following}))
        follow_cont1 = Follow.objects.count()
        self.assertTrue(Follow.objects.filter(
            author=self.user_following, user=self.user_follower).exists())
        self.assertEqual(follow_cont + 1, follow_cont1)

    def test_unfollow(self):
        self.follower_client.post(reverse(
            'posts:profile_follow', kwargs={'username': self.user_following}))
        follow_cont = Follow.objects.count()
        self.follower_client.post(reverse(
            'posts:profile_unfollow', kwargs={'username': self.user_following})
        )
        follow_cont1 = Follow.objects.count()
        self.assertFalse(Follow.objects.filter(
            author=self.user_following, user=self.user_follower).exists())
        self.assertEqual(follow_cont - 1, follow_cont1)

    def test_visual_follow_in_page(self):
        post = Post.objects.create(
            pub_date='31 июля 1854',
            author=self.user_following,
            text='Тестовый текст',
        )
        Follow.objects.create(
            author=self.user_following, user=self.user_follower)
        response = self.follower_client.get(reverse('posts:follow_index'))
        post_list = response.context['page_obj'].object_list
        self.assertIn(post, post_list)

    def test_not_visual_follow_in_page(self):
        post = Post.objects.create(
            pub_date='31 июля 1854',
            author=self.user_following,
            text='Тестовый текст',
        )
        response = self.follower_client.get(reverse('posts:follow_index'))
        post_list = response.context['page_obj'].object_list
        self.assertNotIn(post, post_list)


class TestComment(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='slug',
            description='Описание',
            pub_date='31 июля 1854',
        )
        cls.test_user = User.objects.create_user(username='Leo')
        cls.post = Post.objects.create(
            pub_date='31 июля 1854',
            author=cls.test_user,
            text='Тестовый текст',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client.force_login(self.test_user)
        self.author = User.objects.create_user(username='Leo1')
        self.authorized_client_author.force_login(self.author)

    def test_comment_2(self):
        post = Post.objects.create(
            author=self.test_user,
            text='Тестовый текст',
        )
        comments_count = Comment.objects.count()
        text = 'Тестовый комментарий'
        form_data = {
            'text': text,
        }
        response = self.authorized_client_author.post(
            reverse('posts:add_comment', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, (
            reverse('posts:post_detail', kwargs={'post_id': post.id})))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(Comment.objects.filter(
            text='Тестовый комментарий',
            author=self.author).exists())
