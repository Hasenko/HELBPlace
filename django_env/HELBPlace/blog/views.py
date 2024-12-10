import sys
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Canvas, Contribution, CanvasStatistics
from django.utils import timezone
import requests

from datetime import timedelta

from django.http import HttpResponseRedirect

def redirect(request):
    return HttpResponseRedirect("/blog/")

def get_timer(request, pk):
    canvas = Canvas.objects.filter(id=pk).first()
    contribution = Contribution.objects.filter(canvas=canvas, user=request.user).first()

    if not contribution:
        return JsonResponse({'remaining_time': 0})
    wait_time = contribution.time_placed + timedelta(seconds=canvas.time_to_wait)
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

        print(f"pk : {pk}", file=sys.stderr)
        if request.method == 'POST':
            response_data = {}
            canvas = Canvas.objects.get(id=pk)
            user = self.request.user

            try:
                pixel_index = int(request.POST.get("pixel", ""))
                new_color = request.POST.get("new_color", "")
            except:
                response_data['error'] = 'Invalid pixel or color data.'
                return JsonResponse(response_data, status=400)

            contribution, contribution_was_created = Contribution.objects.get_or_create(
                canvas=canvas,
                user=user,
                defaults={'time_placed': timezone.now()}
            )

            # Check wait time if not a new contribution
            if not contribution_was_created:
                wait_time = contribution.time_placed + timedelta(seconds=canvas.time_to_wait)
                if wait_time > timezone.now():
                    response_data['error'] = 'You need to wait before changing color pixel.'
                    return JsonResponse(response_data, status=403)

            # Update contribution time
            contribution.time_placed = timezone.now()
            contribution.save()

            # Update canvas content
            canvas.content = Canvas.change_pixel(Canvas, canvas.content, pixel_index, new_color)
            canvas.save()

            # Update statistics
            stats, stats_was_created = CanvasStatistics.objects.get_or_create(canvas=canvas)
            today = timezone.now().date().isoformat()
            stats.contributions_day[today] = stats.contributions_day.get(today, 0) + 1
            stats.contributions_user[str(user.id)] = stats.contributions_user.get(str(user.id), 0) + 1
            stats.save()

            response_data['message'] = 'Color modified successfully.'
            return JsonResponse(response_data)

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

def collaborative_canvas(request):
    if request.method == "POST":
            response_data = {}
            pixel_index = request.POST.get("pixel", "")
            new_color = request.POST.get("new_color", "")
            # 128 / 72
            # exemple for pixel_index = 345
            row = int(int(pixel_index) / 128)
            col = int(int(pixel_index) % 128)
            data = {
                'username': 'eimadd',
                'password': '03mpEuHXVXMq',
                'row': row,
                'col': col,
                'hexvalue': new_color,
                }
            

            r = requests.get('https://helbplace2425.alwaysdata.net/writer.php', params=data)
            response_data['message'] = r.content.decode()
            response_data['data'] = data

            if (response_data['message'].startswith("Erreur")):
                status = 400
            else:
                status = 200
            return JsonResponse(response_data, status=status)

    url = "https://helbplace2425.alwaysdata.net/colors.txt"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for HTTP errors
        data = response.text  # Get the content of colors.txt
        pixel_list = []
        i = 0
        pixel = ""
        for letter in data.replace(";", "").replace("\n", ""):
            if i%6 == 0 and i != 0:
                pixel_list.append("#" + pixel)
                pixel = ""

            pixel += letter
            i += 1

        pixel_list.append(pixel)

        context = {
            'collab_table': pixel_list,
        }

        return render(request, 'blog/collaborative_canvas.html', context)
    except requests.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)

