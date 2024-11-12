from django.forms import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Canvas

class CanvasListView(ListView):
    model = Canvas
    template_name = 'blog/home.html' # by default : <app>/<model>_<viewtype>.html
    context_object_name = 'canvases'
    ordering = ['-date_posted'] # replace by 'intensity' of the canvas

class CanvasDetailView(DetailView):
    model = Canvas

class CanvasCreateView(LoginRequiredMixin, CreateView):
    model = Canvas
    fields= ['title', 'width', 'height', 'time_limite']

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

