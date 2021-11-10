from django.db.models import fields
from rest_framework import serializers
from .models import Onto


class OntoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Onto
        fields = ["id", "title",  "onto_source", "onto_file",
                  "onto_table", "author", "date_created"]

    def to_representation(self, instance):
        data = super(OntoSerializer, self).to_representation(instance)
        data.pop('onto_file')
        return data
