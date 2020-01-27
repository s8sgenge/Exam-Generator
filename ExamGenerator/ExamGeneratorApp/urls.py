from ExamGeneratorApp.views import has_permission
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import path, include
from django.views.static import serve

from . import views
from .forms import LoginForm


@login_required
@user_passes_test(has_permission, login_url='/permissionDenied')
def protected_serve(request, path, document_root=None, show_indexes=False):
    return serve(request, path, document_root, show_indexes)


urlpatterns = [
                  path('', views.index_view, name='index'),
                  path('userPermissions', views.user_permissions_view, name='user permissions'),
                  path('topicOverview', views.topic_overview_view, name='topic overview'),
                  path('downloadPage', views.download_page_view, name='download page'),
                  path('examScreen', views.exam_detail_view, name='exam detail view'),
                  path('removeExercise/<int:position>', views.remove_from_exam, name='delete exercise'),
                  path('signUp', views.sign_up_view, name='sign up'),
                  path('permissionDenied', views.permission_denied_view, name='permission denied'),
                  path('uploadExercise', views.upload_exercise_view, name='upload exercise'),
                  path('topic/<int:pk>/exerciseList', views.TopicExerciseListView.as_view(),
                       name='topic exercise list'),
                  path('exercise/<int:pk>', views.exercise_detail_view, name='exercise detail'),
                  path('exercise/<int:pk>/prev', views.previous_version_view, name='prev version'),
                  path('exercise/<int:pk>/next', views.next_version_view, name='next version'),
                  path('accounts/login/', auth_views.LoginView.as_view(authentication_form=LoginForm)),
                  path('accounts/', include('django.contrib.auth.urls')),
                  path('newExam', views.new_exam_view, name='newExam'),
                  path('changeOrder/', views.change_order_view, name='change order'),
                  path('addToExam/<int:pk>', views.add_exercise_to_exam_view, name='add exercise to exam'),
                  path('remove_exercise_by_topic/<int:pk>', views.remove_exercise_by_topic,
                       name='remove exercise by topic'),
                  path('headers', views.HeaderListView.as_view(), name='header list'),
                  path('header/<int:pk>/edit', views.HeaderUpdateView.as_view(), name='edit header'),
                  path('header/<int:pk>', views.HeaderDetailView.as_view(), name='header detail view'),
                  path('renderLog', views.LogView.as_view(), name='render log')

              ] + static((settings.MEDIA_URL), protected_serve, document_root=settings.MEDIA_ROOT)
