from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from .forms import CommentForm, PostForm
from .models import Category, Comment, Post, User


def paging_posts(posts, page_number, limit):
    paginator = Paginator(posts, limit)
    return paginator.get_page(page_number)


class OnlyAuthorMixin(UserPassesTestMixin):
    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != self.request.user:
            return redirect('blog:post_detail',
                            post_id=self.kwargs[self.pk_url_kwarg])
        return super().dispatch(request, *args, **kwargs)


class UnPublishedMixin:
    def get_object(self, queryset=None):
        pk = self.kwargs.get('post_id')
        object = Post.post_manager.filter(pk=pk)
        if object.exists():
            return super().get_object(queryset=object)
        return get_object_or_404(
            Post.objects.filter(pk=pk), author=self.request.user)


class CommentMixin:
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'


class UserDetailView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    context_object_name = 'profile'

    def get_object(self):
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        if user == self.request.user:
            posts = Post.objects.filter(
                author=self.request.user).annotate(
                    comment_count=Count('comments')).order_by('-pub_date')
        else:
            posts = Post.post_manager.filter(
                author=user).annotate(
                    comment_count=Count('comments')).order_by('-pub_date')
        page_number = self.request.GET.get('page')
        page_obj = paging_posts(posts, page_number, settings.MAX_POSTS)
        context['page_obj'] = page_obj
        return context


class ProfileUpdateView(UserPassesTestMixin, UpdateView):
    model = User
    fields = ('username', 'email', 'first_name', 'last_name')
    template_name = 'blog/user.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )

    def test_func(self):
        object = self.get_object()
        return object == self.request.user


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    queryset = Post.post_manager.all().annotate(
        comment_count=Count('comments')
    )
    ordering = '-pub_date'
    paginate_by = settings.MAX_POSTS


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostDetailView(LoginRequiredMixin, UnPublishedMixin, DetailView):
    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/detail.html'

    def get_context_data(self, **kwargs):
        return dict(
            **super().get_context_data(**kwargs),
            form=CommentForm(),
            comments=Comment.objects.filter(post_id=self.kwargs['post_id']),
        )

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs[self.pk_url_kwarg]}
        )


class CategoryPostsDetailView(LoginRequiredMixin, DetailView):
    model = Category
    template_name = 'blog/category.html'
    slug_url_kwarg = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = get_object_or_404(
            Category, slug=self.kwargs['category'], is_published=True
        )
        posts = Post.post_manager.all().filter(
            category=category).annotate(
                comment_count=Count('comments')).order_by('-pub_date')
        page_number = self.request.GET.get('page')
        page_obj = paging_posts(posts, page_number, settings.MAX_POSTS)
        context['page_obj'] = page_obj
        return context


class PostUpdateView(OnlyAuthorMixin, UnPublishedMixin, UpdateView):
    model = Post
    form_class = PostForm
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'


class PostDeleteView(OnlyAuthorMixin, DeleteView):
    model = Post
    form_class = PostForm
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instance = get_object_or_404(Post, pk=self.kwargs[self.pk_url_kwarg])
        context['form'] = PostForm(instance=instance)
        return context

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class CommentCreateView(LoginRequiredMixin, CreateView):
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'post_id'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post, id=self.kwargs[self.pk_url_kwarg]
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs[self.pk_url_kwarg]}
        )


class CommentUpdateView(
    LoginRequiredMixin, UserPassesTestMixin,
    CommentMixin, UpdateView
):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        comment = self.get_object()
        post_id = comment.post.id
        if comment.author != self.request.user:
            return redirect('blog:post_detail',
                            post_id=post_id)
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


class CommentDeleteView(
    LoginRequiredMixin, UserPassesTestMixin,
    CommentMixin, DeleteView
):
    success_url = reverse_lazy('blog:index')

    def dispatch(self, request, *args, **kwargs):
        comment = self.get_object()
        post_id = comment.post.id
        if comment.author != self.request.user:
            return redirect('blog:post_detail',
                            post_id=post_id)
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user
