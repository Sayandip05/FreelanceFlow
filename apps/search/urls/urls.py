from django.urls import path
from apps.search.views import SearchView, ProjectSearchView, FreelancerSearchView, AutocompleteView
urlpatterns = [
    path("", SearchView.as_view(), name="search"),
    path("projects/", ProjectSearchView.as_view(), name="search-projects"),
    path("freelancers/", FreelancerSearchView.as_view(), name="search-freelancers"),
    path("autocomplete/", AutocompleteView.as_view(), name="search-autocomplete"),
]
