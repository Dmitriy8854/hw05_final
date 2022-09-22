from django import forms
from django.contrib.auth import get_user_model

from .models import Post, Comment

User = get_user_model()


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'text': 'Текст поста', 'group': 'Группа'}

    def clean_text(self):
        data = self.cleaned_data['text']
        if Post.text == '':
            raise forms.ValidationError(
                'Поле, текст обязателен для заполнения!')
        return data


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
        labels = {'text': 'Текст поста', }

    def clean_text(self):
        data = self.cleaned_data['text']
        if Post.text == '':
            raise forms.ValidationError(
                'Поле, текст обязателен для заполнения!')
        return data
