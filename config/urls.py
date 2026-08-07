from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", include("apps.users.urls")),
    path("api/projects/", include("apps.projects.urls")),
    path("api/bidding/", include("apps.bidding.urls")),
    # Short-form aliases: /api/bids/* → /api/bidding/bids/*, /api/contracts/* → /api/bidding/contracts/*
    path("api/bids/", include("apps.bidding.urls.bids_only")),
    path("api/contracts/", include("apps.bidding.urls.contracts_only")),
    path("api/payments/", include("apps.payments.urls")),
    path("api/worklogs/", include("apps.worklogs.urls")),
    path("api/messaging/", include("apps.messaging.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/search/", include("apps.search.urls")),
]

if settings.DEBUG:
    from django.views.generic import RedirectView

    urlpatterns += [
        path("", RedirectView.as_view(url="/admin/")),
    ]
    # Serve uploaded media files locally
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
 
