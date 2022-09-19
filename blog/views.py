from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.views import generic, View
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.text import slugify
from django.template import loader
from .models import Post
from .forms import CommentForm, PostForm


def frontpage(_):
    template = loader.get_template('drinks/frontpage.html')
    return HttpResponse(template.render())


class Homepage(View):
    def get(self, request):
        template_name = "drinks/index.html"
        return render(request, template_name)


class CocktailsList(generic.ListView):
    """ Displays a list of all cocktails """
    model = Post
    queryset = Post.objects.filter(status=1).order_by("-created_on")
    template_name = "drinks/cocktails.html"
    paginate_by = 6


class PostDetail(View):

    def get(self, request, slug, *args, **kwargs):
        queryset = Post.objects.filter(status=1)
        post = get_object_or_404(queryset, slug=slug)
        comments = post.comments.filter(approved=True).order_by("-created_on")
        liked = False
        if post.likes.filter(id=self.request.user.id).exists():
            liked = True

        context = {
                "post": post,
                "comments": comments,
                "commented": False,
                "liked": liked,
                "comment_form": CommentForm(),
                "is_author": post.author == request.user
                 }

        return render(
            request,
            "drinks/post_detail.html",
            context
        )

    def post(self, request, slug, *args, **kwargs):

        queryset = Post.objects.filter(status=1)
        post = get_object_or_404(queryset, slug=slug)
        comments = post.comments.filter(approved=True).order_by("-created_on")
        liked = False
        if post.likes.filter(id=self.request.user.id).exists():
            liked = True

        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            comment_form.instance.email = request.user.email
            comment_form.instance.name = request.user.username
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.save()
        else:
            comment_form = CommentForm()

        return render(
            request,
            "drinks/post_detail.html",
            {
                "post": post,
                "comments": comments,
                "commented": True,
                "comment_form": comment_form,
                "liked": liked
            },
        )


class DeletePost(View):
    """ Athor can delete post """
    def post(self, request, id):
        post = Post.objects.get(id=id)
        post.delete()

        return HttpResponseRedirect(reverse('home'))

class EditPost(View):
    """ Athor can edit post """
    def get(self, request, user_id):
        template_name = 'drinks/edit_post.html'
        context = {
            'form': PostForm(instance=Post.objects.get(id=user_id)),
            'message': ''
        }

        return render(request, template_name, context)

    def post(self, request, user_id):
        
        existing_post = get_object_or_404(Post, id = user_id)

        form = PostForm(request.POST or None, instance = existing_post)
        
        if form.is_valid():
            print('Post is valid... saving post.')
            form.save()
            return HttpResponseRedirect('/')
            
        else:
            print('Post is invalid.')
            print(form.errors)
            return HttpResponseRedirect('/')

    def post2(self, request, id):
        author = request.user

        # this is for creating an entirely new post
        # post = PostForm(request.POST, request.FILES)

        # this is for updating
        current_post = Post.objects.get(id=id)
        post = PostForm(instance=current_post, data=request.post)
        
        if post.is_valid():
            print('Post is valid... saving post.')
            # prepared_post = post.save(commit=False)
            post.author = author
            post.slug = slugify(request.POST['title'])
            post.save()

        # author = request.user
        # if author.has_perm('blog.add_post'):
        #     post = Post.objects.get(id=id)
        #     post.title = request.POST['title']
        #     post.excerpt = request.POST['excerpt']
        #     post.content = request.POST['content']
        #     post.status = request.POST['status']
        # post = Post.objects.get(id=id)
        # form = PostForm(instance=post, data=request.post)
        # if form.is_valid():
        #     form.save()
        #     return HttpResponseRedirect(reverse('post_detail', args=[post.slug]))

        return redirect('/')


class PostLike(View):
    def post(self, request, slug, *args, **kwargs):
        post = get_object_or_404(Post, slug=slug)
        if post.likes.filter(id=request.user.id).exists():
            post.likes.remove(request.user)
        else:
            post.likes.add(request.user)

        return HttpResponseRedirect(reverse('post_detail', args=[slug]))


class AddPostView(View):
    def post(self, request, *aggs, **kwargs):
        author = request.user
        if author.has_perm('blog.add_post'):
            new_post = PostForm(request.POST, request.FILES)
            # new_post = PostForm(initial={
            #     'title': request.POST['title'],
            #     'featured_image': request.POST['featured_image'],
            #     'excerpt': request.POST['excerpt'],
            #     'content': request.POST['content'],
            #     'status': request.POST['status'],
            # })
            post_save = new_post.save(commit=False)
            post_save.slug = slugify(request.POST['title'])
            post_save.author = author
            post_save.save()
            return redirect('/')

        template_name = 'drinks/add_post.html'
        context = {
            'message': 'You do not have permission to post',
            'form': PostForm
            }
        return render(request, template_name, context)

    def get(self, request):
        template_name = 'drinks/add_post.html'
        context = {
            'form': PostForm,
            'message': ''  
        }
        return render(request, template_name, context)