from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path


# Функция за статичен sitemap.xml
def sitemap_xml(request):
    content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://takethetripapp.com/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://takethetripapp.com/users/login/</loc>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
  <url>
    <loc>https://takethetripapp.com/users/register/</loc>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
</urlset>"""
    return HttpResponse(content, content_type="application/xml")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('rides.urls')),
    path('users/', include('users.urls')),
    path('reviews/', include('reviews.urls')),
    path('notifications/', include('notifications.urls')),
    path('sitemap.xml', sitemap_xml, name='sitemap'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)