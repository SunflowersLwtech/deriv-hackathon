from django.urls import path
from .views import LoadScenarioView, ListScenariosView, AnalyzeScenarioView, SeedDemoView, WowMomentView

urlpatterns = [
    path("load-scenario/", LoadScenarioView.as_view(), name="load-scenario"),
    path("scenarios/", ListScenariosView.as_view(), name="list-scenarios"),
    path("analyze/", AnalyzeScenarioView.as_view(), name="analyze-scenario"),
    path("seed/", SeedDemoView.as_view(), name="seed-demo"),
    path("wow-moment/", WowMomentView.as_view(), name="wow-moment"),
]
