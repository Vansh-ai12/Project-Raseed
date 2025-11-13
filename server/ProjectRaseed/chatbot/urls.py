from django.contrib import admin
from django.urls import path,include
from . import views
urlpatterns = [
     path('prompt/', views.chatPrompt, name='chatBot_Prompt'),
     path('reply/', views.chatReply, name='chatBot_Reply'),
     path('status/',views.statusInfo,name='StatusInfo')
]
