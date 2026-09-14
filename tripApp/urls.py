import sitemaps
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('rides.urls')),
    path('users/', include('users.urls')),
    path('reviews/', include('reviews.urls')),
    path('notifications/', include('notifications.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )


class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = 'daily'

    def items(self):
        return ['home', 'login', 'register']  # имена на основните ти URL адреси

    def location(self, item):
        return reverse(item)


sitemaps = {
    'static': StaticViewSitemap,
}
