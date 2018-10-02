from haystack import indexes

from courses.models import Course


class CourseIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    course_id = indexes.IntegerField(model_attr='id')
    is_active = indexes.BooleanField(model_attr='is_active')

    name_auto = indexes.NgramField(model_attr='name')

    def get_model(self):
        return Course

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def get_updated_field(self):
        return 'update_time'
