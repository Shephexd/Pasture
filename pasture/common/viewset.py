from rest_framework import viewsets


class SerializerMapMixin(viewsets.ViewSet):
    serializer_class = None
    serializer_class_map = {
    }

    def get_serializer_class(self):
        return self.serializer_class_map.get(self.action, self.serializer_class)
