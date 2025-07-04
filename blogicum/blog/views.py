from django.shortcuts import get_list_or_404, get_object_or_404, render
from django.utils import timezone

from blog.models import Post

MAX_RECORD_COUNT = 5


def index(request):
    template = 'blog/index.html'
    post_list = Post.objects.filter(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True
    )[:MAX_RECORD_COUNT]
    context = {'post_list': post_list}
    return render(request, template, context)


def post_detail(request, id):
    template = 'blog/detail.html'
    get_object_or_404(
        Post.objects.filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True
        ),
        pk=id
    )
    post = Post.objects.get(pk=id)
    context = {'post': post, }
    return render(request, template, context)


def category_posts(request, category_slug):
    template = 'blog/category.html'
    post_list = get_list_or_404(
        Post.objects.filter(
            category__slug=category_slug,
            pub_date__lte=timezone.now(),
            category__is_published=True,
            is_published=True,
        ),
        category__slug=category_slug
    )
    category = category_slug
    context = {'post_list': post_list, 'category': category}
    return render(request, template, context)
