from django.forms import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Canvas

class CanvasListView(ListView):
    model = Canvas
    template_name = 'blog/home.html'  # by default: <app>/<model>_<viewtype>.html
    context_object_name = 'canvases'
    ordering = ['-date_posted']  # replace with 'intensity' of the canvas

    def get_queryset(self):
        # Get the base queryset
        queryset = super().get_queryset()

        # Modify the 'content' attribute for each canvas
        for canvas in queryset:
            canvas.content = Canvas.get_pixel_list(canvas.content)
        return queryset
class CanvasDetailView(DetailView):
    model = Canvas

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        content = self.object.content

        context['pixel_list'] = Canvas.get_pixel_list(content)
        return context

class CanvasCreateView(LoginRequiredMixin, CreateView):
    model = Canvas
    fields= ['title', 'width', 'height', 'time_to_wait']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class CanvasUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Canvas
    fields= ['content']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        canvas = self.get_object()
        return self.request.user == canvas.author

class CanvasDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Canvas
    success_url = '/blog' # weird

    def test_func(self):
        canvas = self.get_object()
        return self.request.user == canvas.author

def about(request):
    context = {
        'title': 'About'
    }
    return render(request, 'blog/about.html', context)

