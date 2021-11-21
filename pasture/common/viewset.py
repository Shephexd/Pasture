from rest_framework import viewsets


class SerializerMapMixin(viewsets.GenericViewSet):
    serializer_class_map = {}

    def get_serializer_class(self):
        return self.serializer_class_map.get(self.action, self.serializer_class)


class QuerysetMapMixin(viewsets.GenericViewSet):
    queryset_map = {}

    def get_queryset(self):
        return self.queryset_map.get(self.action, self.queryset)
