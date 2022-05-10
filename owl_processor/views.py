from sys import api_version
from django.http.response import HttpResponse, HttpResponseNotFound
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Onto
from .serializers import OntoSerializer
from .utility.ontotable import onto_to_table
from rest_framework import status
import json
from rest_framework.exceptions import APIException
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from drf_yasg import openapi
from rest_framework.parsers import (
    FormParser,
    MultiPartParser
)
from .swaggerdoc import *


class OntoList(APIView):

    permission_classes = [IsAuthenticated]
    parser_classes = (FormParser, MultiPartParser)

    @ swagger_auto_schema(
        operation_summary='list ontology',
        operation_description='Authenticated user gets a list of ontologies saved in the databank. \
                                Ontologies are loaded in Ontopanel-EntityManager when user logs in.',
        responses={
            "200": openapi.Response("list of Ontologies",
                                    schema=openapi.Schema(
                                        type=openapi.TYPE_ARRAY, items=onto_response_schema),
                                    examples={
                                        "application/json": [{"id": "ontology id", "onto_source": "url or file name", "onto_table": "see example in POST(add ontology (auth))", "author": "user id", "date_created": "date"}]
                                    })

        }

    )
    def get(self, request):
        user = request.user
        ontos = Onto.objects.filter(author=user)
        serializer = OntoSerializer(ontos, many=True)
        return Response(serializer.data)

    @ swagger_auto_schema(
        operation_summary='add and save ontology',
        operation_description='Authenticated user uploads and saves ontology in the databank.\
                               Ontology is added into Ontopanel-EntityManager. ',
        manual_parameters=doc_form_data,
        responses={
            "201": doc_onto_auth,
            "400": "Bad Request",
            "503": openapi.Response("Unprocessable errors", schema=openapi.Schema(type=openapi.TYPE_STRING, description="different cases, return different messages, see examples."), examples={
                "application/json": {
                    "503/Input URL and file are both empty": "no file available",
                    "503/User has already 10 ontologies saved in databank": "You can store up to 10 ontologies.",
                    "503/Input cant be parse or accessed": "Your ontology or its imported ontologies can not be accessed or parsed. Please check access or the format(rdf or turtle) or use merged file."
                }
            })
        }

    )
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
    parser_classes = (FormParser, MultiPartParser)

    def get_object(self, user, id):
        try:
            return Onto.objects.filter(author=user).get(id=id)
        except Onto.DoesNotExist:
            raise APIException("This ontology does not exist.")

    @ swagger_auto_schema(
        operation_summary='update ontology',
        operation_description='Authenticated user updates the ontology with id in the databank.\
                                Ontology with id is updated in Ontopanel-EntityManager.',
        manual_parameters=doc_form_data,
        responses={
            "201": doc_onto_auth,
            "400": "Bad Request",
            "503": openapi.Response("Unprocessable errors", schema=openapi.Schema(type=openapi.TYPE_STRING, description="different cases, return different messages, see examples."), examples={
                "application/json": {
                    "503/Input URL and file are both empty": "no file available",
                    "503/Input cant be parse or accessed": "Your ontology or its imported ontologies can not be accessed or parsed. Please check access or the format(rdf or turtle) or use merged file."
                }
            })
        }
    )
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

    @ swagger_auto_schema(
        operation_summary='delete ontology',
        operation_description='Authenticated user removes the ontology with id from the database.\
                                Ontology with this id is removed in Ontopanel-EntityManager.',
        responses={
            "204": "Successful removed.",
            "404": "This ontology does not exist.",
        }

    )
    def delete(self, request, id):
        user = request.user
        onto = self.get_object(user, id)
        onto.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OwlTable(APIView):
    permission_classes = [AllowAny]
    parser_classes = (FormParser, MultiPartParser)

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

    @ swagger_auto_schema(
        operation_summary='add ontology',
        operation_description='User uploads ontology without authentication.\
                                Ontology is added into Ontopanel-EntityManager.',
        manual_parameters=doc_form_data,
        responses={
            "201": doc_onto,
            "400": "Bad Request",
            "503": openapi.Response("Unprocessable errors", schema=openapi.Schema(type=openapi.TYPE_STRING, description="different cases, return different messages, see examples."), examples={
                "application/json": {"503/Input URL and file are both empty": "no file available",
                                    "503/Input cant be parse or accessed": "Your ontology or its imported ontologies can not be accessed or parsed. Please check access or the format(rdf or turtle) or use merged file."}

            })
        })
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
