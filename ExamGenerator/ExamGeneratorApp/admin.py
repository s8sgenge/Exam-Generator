from django.contrib import admin

from .models import Exercise, Exam, Header, ExerciseSolution, ExerciseText, Content, Topic, FileDependency

admin.site.register(Exercise)
admin.site.register(Exam)
admin.site.register(Header)
admin.site.register(ExerciseText)
admin.site.register(ExerciseSolution)
admin.site.register(Content)
admin.site.register(Topic)
admin.site.register(FileDependency)

#
# class ExerciseTextAdmin(admin.modelAdmin):
#
#     def save_model(self, request, obj, form, change):
#         obj.versionGroup = obj.pk
#         super().save_model(request, obj, form, change)
