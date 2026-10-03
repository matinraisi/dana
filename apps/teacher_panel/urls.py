from django.urls import path
from . import views

app_name = 'teacher'

urlpatterns = [
    path('', views.TeacherDashboardView.as_view(), name='dashboard'),
    path('courses/', views.TeacherCourseListView.as_view(), name='course_list'),
    path('courses/<int:course_id>/students/', views.TeacherStudentListView.as_view(), name='student_list'),
    path('sessions/<int:session_id>/attendance/', views.TeacherAttendanceView.as_view(), name='attendance'),
    path('earnings/', views.TeacherEarningsView.as_view(), name='earnings'),
    path('profile/', views.TeacherProfileView.as_view(), name='profile'),

    # جلسات
    path('courses/<int:course_id>/sessions/', views.TeacherSessionListView.as_view(), name='session_list'),
    path('courses/<int:course_id>/sessions/create/', views.TeacherSessionCreateView.as_view(), name='session_create'),

    # محتوای جلسات
    path('sessions/<int:session_id>/materials/', views.TeacherMaterialListView.as_view(), name='material_list'),
    path('courses/<int:course_id>/materials/', views.TeacherCourseMaterialListView.as_view(), name='course_materials'),

    # آزمون‌ها
    path('exams/', views.TeacherExamListView.as_view(), name='exam_list'),
    path('exams/create/', views.TeacherExamCreateView.as_view(), name='exam_create'),
    path('exams/<int:exam_id>/edit/', views.TeacherExamEditView.as_view(), name='exam_edit'),
    path('exams/<int:exam_id>/delete/', views.TeacherExamDeleteView.as_view(), name='exam_delete'),
    path('exams/<int:exam_id>/questions/', views.TeacherExamQuestionsView.as_view(), name='exam_questions'),
    path('exams/<int:exam_id>/results/', views.TeacherExamResultsView.as_view(), name='exam_results'),
    path('attempts/<int:attempt_id>/', views.TeacherAttemptDetailView.as_view(), name='attempt_detail'),
    path('questions/<int:question_id>/choices/', views.TeacherQuestionChoicesView.as_view(), name='question_choices'),
]
