import sys
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from django.views.generic import DetailView
from .models import Profile, UserStatistics
from django.contrib.auth.models import User
from blog.models import Canvas


"""
messages.debug
messages.info
messages.success
messages.warning
messages.error
"""

# Create your views here.
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}. You can now login !')
            return redirect('login')

    else:
        form = UserRegisterForm()

    context = {
        'form': form
    }
    return render(request, 'users/register.html', context)

@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, 
                                   request.FILES, 
                                   instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been updated succesfuly !')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }

    return render(request, 'users/profile.html', context)

class UsersProfileDetailView(DetailView):
    model = User
    template_name = 'users/user_detail.html'  # by default: <app>/<model>_<viewtype>.html
    context_object_name = 'user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object

        contributions_canvas = UserStatistics.objects.filter(user=user).first().contributions_canvas
        user_statistics = {}
        canvas_pixel_list = {}

        for key in contributions_canvas:
            canvas = Canvas.objects.filter(id=key).first()
            if not canvas:
                continue
            user_statistics[canvas] = contributions_canvas[key]
            canvas_pixel_list[canvas] = Canvas.get_pixel_list(canvas.content)

        user_statistics = dict(sorted(user_statistics.items(), key=lambda item: item[1], reverse=True))
        context['user_statistics'] = user_statistics
        context['canvas_pixel_list'] = canvas_pixel_list

        return context