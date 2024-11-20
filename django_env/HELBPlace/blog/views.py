from django.forms import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Canvas

import logging

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
    
    def post(self, request, *args, **kwargs):
        pk = kwargs.get('pk')

        if request.method == 'POST':
            pixel_index = request.POST.get("pixel", "")
            new_color = request.POST.get("new_color", "")
            canvas = Canvas.objects.filter(id=pk).first()

            logging.getLogger("mylogger").info(pixel_index)
            logging.getLogger("mylogger").info(new_color)
            logging.getLogger("mylogger").info(canvas)
            
            canvas.content = Canvas.change_pixel(Canvas, canvas.content, int(pixel_index), new_color)
            canvas.save()

            return redirect("canvas-detail", pk=pk)

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