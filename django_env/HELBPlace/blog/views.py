import sys
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Canvas, Contribution, CanvasStatistics
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.contrib.auth.models import User
import requests
from datetime import timedelta
from users.models import UserStatistics
from django.http import HttpResponseRedirect

def redirect(request):
    return HttpResponseRedirect("/gallery/")

def get_stats(request, pk):
    response_data = {}
    canvas = Canvas.objects.filter(id=pk).first()
    stats = CanvasStatistics.objects.filter(canvas=canvas).first()

    contrib_days = stats.contributions_day
    if not contrib_days:
        return JsonResponse({'error': 'no stats available'})
    min_day = timezone.datetime.strptime(min(contrib_days), "%Y-%m-%d")
    max_day = timezone.localtime().now()

    # Create a full range of days between min_day and max_day
    contrib_days_full_range = { 
        (min_day + timedelta(days=i)).strftime("%Y-%m-%d"): contrib_days.get((min_day + timedelta(days=i)).strftime("%Y-%m-%d"), 0)
        for i in range((max_day - min_day).days + 1)
    }

    response_data['canvas_graph'] = contrib_days_full_range

    contrib_user = stats.contributions_user
    canvas_scoreboard = {}
    for key in contrib_user:
        user = User.objects.filter(id=key).first()
        canvas_scoreboard[user.username + "\\" + str(user.id)] = contrib_user[key]

    canvas_scoreboard = dict(sorted(canvas_scoreboard.items(), key=lambda item: item[1], reverse=True))
    response_data['canvas_scoreboard'] = canvas_scoreboard

    return JsonResponse(response_data)

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
        canvases = super().get_queryset()

        # Modify the 'content' attribute for each canvas
        for canvas in canvases:
            canvas.content = Canvas.get_pixel_list(canvas.content)

        # canvas, contributions_day {date, int}, contributions_user {date, int}
        canvas_stats = CanvasStatistics.objects.all()
        
        canvas_pixel_placed_last_day = {}

        for stats in canvas_stats:
            contrib_days = stats.contributions_day

            if not contrib_days:
                canvas_pixel_placed_last_day[stats.canvas] = ['N/A', 0]
                continue

            last_day = sorted(contrib_days.keys(), key=lambda x: timezone.datetime.strptime(x, '%Y-%m-%d'))[-1]
            last_day_django_format = parse_date(last_day)
            last_day_value = contrib_days[last_day]

            canvas_pixel_placed_last_day[stats.canvas] = [last_day_django_format, last_day_value]

        sorted_canvas_pixel_placed_last_day = dict(sorted(
            (canvas for canvas in canvas_pixel_placed_last_day.items() if canvas[1][0] != 'N/A'),
            key=lambda x: (x[1][0], x[1][1]),
            reverse=True
        ))

        na_entries = {canvas: value for canvas, value in canvas_pixel_placed_last_day.items() if value[0] == 'N/A'}
        sorted_canvas_pixel_placed_last_day.update(na_entries)

        return sorted_canvas_pixel_placed_last_day
    
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

            # Update Canvas statistics
            canvas_stats, canvas_stats_was_created = CanvasStatistics.objects.get_or_create(canvas=canvas)
            today = timezone.localtime().now().date().isoformat()
            canvas_stats.contributions_day[today] = canvas_stats.contributions_day.get(today, 0) + 1
            canvas_stats.contributions_user[str(user.id)] = canvas_stats.contributions_user.get(str(user.id), 0) + 1
            canvas_stats.save()

            
            # Update User statistics
            user_stats, stats_was_created = UserStatistics.objects.get_or_create(user=user)
            user_stats.contributions_canvas[str(canvas.id)] = user_stats.contributions_canvas.get(str(canvas.id), 0) + 1
            user_stats.save()

            response_data['message'] = 'Color modified successfully.'
            return JsonResponse(response_data)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        content = self.object.content

        context['pixel_list'] = Canvas.get_pixel_list(content)
        
        canvas_statistics = CanvasStatistics.objects.filter(canvas=self.object).first()

        if canvas_statistics and not canvas_statistics.contributions_day:
            context['has_stats'] = False
        else:
            context['has_stats'] = True

        return context

class CanvasCreateView(LoginRequiredMixin, CreateView):
    model = Canvas
    fields= ['title', 'width', 'height', 'time_to_wait']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class CanvasUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Canvas
    fields= ['title', 'time_to_wait']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        canvas = self.get_object()
        return self.request.user == canvas.author

class CanvasDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Canvas
    success_url = '/gallery' # weird

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

