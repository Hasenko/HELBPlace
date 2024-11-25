from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Canvas, Contribution
from django.utils import timezone

from datetime import timedelta

def get_timer(request, pk):
    canvas = Canvas.objects.filter(id=pk).first()
    contribution = Contribution.objects.filter(canvas=canvas, user=request.user).first()

    wait_time = contribution.time_placed + timedelta(minutes=canvas.time_to_wait)
    remaining_time = (wait_time - timezone.now()).total_seconds()

    if remaining_time < 0:
        remaining_time = 0


    return JsonResponse({'remaining_time': remaining_time})

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
class CanvasDetailView(LoginRequiredMixin, DetailView):
    model = Canvas
    
    def post(self, request, *args, **kwargs):
        pk = kwargs.get('pk')

        if request.method == 'POST':
            canvas = Canvas.objects.filter(id=pk).first()
            # self.request.user -> USER that clicked the pixel

            # Check for an existing contribution
            contribution = Contribution.objects.filter(
                canvas=canvas,
                user=self.request.user
            ).first()

            if contribution:
                # Calculate the time threshold
                wait_time = contribution.time_placed + timedelta(minutes=canvas.time_to_wait)

                if wait_time <= timezone.now():
                    # Allow the user to update the contribution
                    contribution.time_placed = timezone.now()
                    contribution.save()

                    pixel_index = request.POST.get("pixel", "")
                    new_color = request.POST.get("new_color", "")
                    canvas.content = Canvas.change_pixel(Canvas, canvas.content, int(pixel_index), new_color)
                    canvas.save()
            else:
                Contribution.objects.create(
                    canvas=canvas,
                    user=self.request.user,
                    time_placed=timezone.now()
                )

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