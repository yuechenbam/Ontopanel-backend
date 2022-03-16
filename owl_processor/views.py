from django.http.response import HttpResponse, HttpResponseNotFound
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Onto
from .serializers import OntoSerializer
from rest_framework.views import APIView
from .utility.ontotable import onto_to_table
from rest_framework import status
import json
from rest_framework.exceptions import APIException


class OntoList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        ontos = Onto.objects.filter(author=user)
        serializer = OntoSerializer(ontos, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = request.user
        ontosCounts = Onto.objects.filter(author=user).count()
        if ontosCounts >= 10:
            raise APIException("You can store up to 10 ontologies.")

        onto_source, onto_file, tagName, table, namespaces, tree = OwlTable().process_data(request)

        data = {
            "title": tagName,
            "onto_source": onto_source,
            'onto_file': onto_file,
            "onto_table": {"table": table, "namespaces": namespaces, "tree": tree},
            "author": user.id,
        }

        serializer = OntoSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OntoChange(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, user, id):
        try:
            return Onto.objects.filter(author=user).get(id=id)
        except Onto.DoesNotExist:
            raise APIException("This ontology does not exist.")

    def put(self, request, id):
        user = request.user
        onto_source, onto_file, tagName, table, namespaces, tree = OwlTable().process_data(request)

        data = {
            "title": tagName,
            "onto_source": onto_source,
            'onto_file': onto_file,
            "onto_table": {"table": table, "namespaces": namespaces, "tree": tree},
            "author": user.id,
        }

        onto = self.get_object(user, id)

        serializer = OntoSerializer(onto, data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        user = request.user
        onto = self.get_object(user, id)
        onto.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OwlTable(APIView):
    permission_classes = [AllowAny]

    def process_data(self, request):
        file_object = request.FILES.get("formFile")
        file_url = request.POST.get("formURL").strip()
        tagName = request.POST.get("formName").strip()

        if file_url:
            table, namespaces, tree = onto_to_table(file_url)
            onto_source = file_url
            onto_file = file_url
        elif file_object:
            table, namespaces, tree = onto_to_table(
                file_object, inputType="File")
            onto_source = file_object.name
            file_object.file.seek(0)
            onto_file = file_object.read().decode()
        else:
            raise APIException("no file available")

        return onto_source, onto_file, tagName, table, namespaces, tree

    def post(self, request):
        onto_source, onto_file, tagName, table, namespaces, tree = self.process_data(
            request)
        data = {
            "title": tagName,
            "onto_source": onto_source,
            "onto_table": {"table": table, "namespaces": namespaces, "tree": tree},
            "author": "no user",
        }

        return Response(data=data, status=status.HTTP_200_OK)
