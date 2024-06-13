from rest_framework.exceptions import ValidationError


def create_queryset_obj(self):
    user = self.context['request'].user
    name_object = self.context['name_object']
    select_object = self.context['select_object']
    queryset = self.context['queryset']
    queryset_obj, created = queryset.get_or_create(
        user=user, **{name_object: select_object})
    if created:
        return select_object
    raise ValidationError(
        {'errors': 'Уже существует.'}, code='dublicate_errors')
