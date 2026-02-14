from django.urls import path
from .views import (
    LoadScenarioView,
    ListScenariosView,
    AnalyzeScenarioView,
    SeedDemoView,
    WowMomentView,
    DemoScriptListView,
    DemoScriptDetailView,
    DemoRunScriptView,
    DemoTriggerEventView,
    DemoHealthView,
    DemoRunScriptV2View,
)

urlpatterns = [
    path("load-scenario/", LoadScenarioView.as_view(), name="load-scenario"),
    path("scenarios/", ListScenariosView.as_view(), name="list-scenarios"),
    path("analyze/", AnalyzeScenarioView.as_view(), name="analyze-scenario"),
    path("seed/", SeedDemoView.as_view(), name="seed-demo"),
    path("wow-moment/", WowMomentView.as_view(), name="wow-moment"),
    # Demo scripts for hackathon pitch
    path("scripts/", DemoScriptListView.as_view(), name="demo-scripts"),
    path("scripts/<str:name>/", DemoScriptDetailView.as_view(), name="demo-script-detail"),
    path("run-script/", DemoRunScriptView.as_view(), name="demo-run-script"),
    # V2 — audit fix additions
    path("trigger-event/", DemoTriggerEventView.as_view(), name="demo-trigger-event"),
    path("health/", DemoHealthView.as_view(), name="demo-health"),
    path("run-script-v2/", DemoRunScriptV2View.as_view(), name="demo-run-script-v2"),
]
