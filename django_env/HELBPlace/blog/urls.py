from django.urls import path
from .views import CanvasListView, CanvasDetailView, CanvasCreateView, CanvasUpdateView, CanvasDeleteView
from . import views

urlpatterns = [
    path('', CanvasListView.as_view(), name='blog-home'),
    path('canvas/<int:pk>/', CanvasDetailView.as_view(), name='canvas-detail'),
    path('canvas/new/', CanvasCreateView.as_view(), name='canvas-create'),
    path('canvas/<int:pk>/update/', CanvasUpdateView.as_view(), name='canvas-update'),
    path('canvas/<int:pk>/delete/', CanvasDeleteView.as_view(), name='canvas-delete'),
    path('helbplace/', views.collaborative_canvas, name='blog-collaborative-canvas'),
    path('canvas/<int:pk>/timer/', views.get_timer, name='get_timer'),
]