from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
# router.register(r'users', views.UserProfileViewSet)
router.register(r'users', views.UserViewSet)
router.register(r'perform', views.GbPerformViewSet)
router.register(r'method', views.GbMethodViewSet)
router.register(r'sample', views.SampleViewSet)
router.register(r'sheet', views.SheetViewSet)
router.register(r'sheet_item', views.SheetItemViewSet)
router.register(r'report', views.ReportViewSet)

app_name = 'api'
urlpatterns = [
    path(r'', include(router.urls)),
    # path(r'api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path(r'token-auth/', views.MyObtainAuthToken.as_view(), name='token'),
    path(r'download/sheet/view/<int:sample_id>/', views.SheetView.as_view(), name='sheet_view'),
    path(r'download/sheet/<int:sample_id>/', views.DownloadSheet.as_view()),
    path(r'download/sheet/header/', views.SheetHeader.as_view(), name='sheet_header'),
    path(r'download/report/view/<int:report_id>/', views.ReportView.as_view(), name='report_view'),
    path(r'download/report/<int:report_id>/', views.DownloadReport.as_view()),
    path(r'download/report/footer/', views.ReportFooter.as_view(), name='report_footer'),
]
