"""
URL configuration for Fueler project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from personal_dir.views import (home_page_view, btn_add_row,btn_show_raw_data, btn_add_row, btn_delete_row,  )
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', home_page_view, name='home'),
    # path('plots/', show_plots, name='plots'),
    path('fuel/view/', btn_show_raw_data,),
    path('add_row/', btn_add_row, name='add_row'),
    path('delete_row/', btn_delete_row, name='delete_row'),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
