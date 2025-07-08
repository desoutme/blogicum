from django.contrib.auth import get_user_model
from django.db.models import Count
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from blog.models import Category, Post, Comment

from .forms import PostForm, ProfileEditForm, CommentForm
PAGINATE_COUNT = 10

User = get_user_model()


class IndexListView(ListView):
    """Список всех опубликованных постов."""

    template_name = 'blog/index.html'
    paginate_by = PAGINATE_COUNT

    def get_queryset(self):
        return Post.objects.filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True
        ).order_by('-pub_date').annotate(comment_count=Count('comments'))


class PostDetailView(DetailView):
    """Детали поста."""

    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'
    paginate_by = PAGINATE_COUNT

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user

        is_post_published = (
            obj.is_published
            and obj.pub_date <= timezone.now()
            and obj.category is not None
            and obj.category.is_published
        )

        if not is_post_published and (
            not user.is_authenticated or user != obj.author
        ):
            raise Http404("Пост не найден")

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.all()
        return context


class CategoryPostListView(ListView):
    """Отображение постов в определенной категории."""

    template_name = 'blog/category.html'
    paginate_by = PAGINATE_COUNT

    def get_category(self):
        return get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )

    def get_queryset(self):
        category = self.get_category()
        return Post.objects.filter(
            category=category,
            pub_date__lte=timezone.now(),
            is_published=True,
        ).order_by('-pub_date').annotate(comment_count=Count('comments'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.get_category()
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    """Создание нового поста."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование поста."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def handle_no_permission(self):
        post_id = self.kwargs.get(self.pk_url_kwarg)
        return redirect('blog:post_detail', post_id=post_id)

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.user != self.object.author:
            return redirect('blog:post_detail', post_id=self.object.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.object.pk}
        )


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Редактирование профиля."""

    model = User
    form_class = ProfileEditForm
    template_name = 'blog/user.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class ProfileDetailView(ListView):
    """Профиль пользователя."""

    model = Post
    template_name = 'blog/profile.html'
    paginate_by = PAGINATE_COUNT

    def get_queryset(self):
        username = self.kwargs.get('username')
        self.profile = get_object_or_404(User, username=username)
        if not (
            self.request.user.is_authenticated
            and self.request.user == self.profile
        ):
            return Post.objects.filter(
                author=self.profile,
                is_published=True,
                category__is_published=True,
                pub_date__lte=timezone.now()
            ).order_by('-pub_date').annotate(comment_count=Count('comments'))
        else:
            return Post.objects.filter(
                author=self.profile
            ).order_by('-pub_date').annotate(comment_count=Count('comments'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.profile
        return context


class PostDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление поста."""

    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    success_url = reverse_lazy('blog:index')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            post_id = kwargs.get(self.pk_url_kwarg)
            return redirect('blog:post_detail', post_id=post_id)
        self.object = self.get_object()
        if request.user != self.object.author:
            return redirect('blog:post_detail', post_id=self.object.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.get_object())
        return context


class CommentCreateView(CreateView):
    """Создание комментария к посту."""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        self.post_obj = get_object_or_404(Post, pk=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.request.user.is_authenticated:
            context['form'] = None
        return context

    def form_valid(self, form):
        if not self.request.user.is_authenticated:
            return self.form_invalid(form)
        form.instance.author = self.request.user
        form.instance.post = self.post_obj
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.post_obj.pk}
        )


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование комментария."""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        self.post_obj = get_object_or_404(Post, pk=kwargs['post_id'])
        self.comment_obj = get_object_or_404(
            Comment,
            pk=kwargs['comment_id'],
            post=self.post_obj
        )
        if self.comment_obj.author != request.user:
            return redirect('blog:post_detail', post_id=self.post_obj.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return self.comment_obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment'] = self.comment_obj
        return context

    def form_valid(self, form):
        form.instance.post = self.post_obj
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.post_obj.pk}
        )


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление поста."""

    model = Comment
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        self.post_obj = get_object_or_404(Post, pk=kwargs['post_id'])
        self.comment_obj = get_object_or_404(
            Comment,
            pk=kwargs['comment_id'],
            post=self.post_obj
        )
        if self.comment_obj.author != request.user:
            return redirect('blog:post_detail', post_id=self.post_obj.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return self.comment_obj

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.post_obj.pk}
        )
