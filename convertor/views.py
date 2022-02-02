from django.http.response import HttpResponse, HttpResponseNotFound
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework import status
import json
from rest_framework.exceptions import APIException
from .utilies.conversion.graph_to_rdf import MakeOntology
from .utilies.datauploader import data_process


class GraphConvertor(APIView):
    permission_classes = [AllowAny]

    def process_data(self, request):
        data = json.loads(request.body)
        file_data = data['data']
        file_format = data['format'].strip()

        onto = MakeOntology(file_data)

        errors = onto.errors
        g = onto.g

        result = g.serialize(format=file_format)

        return result, errors

    def post(self, request):

        result, errors = self.process_data(request)
        data = {
            "result": result,
            "errors": errors
        }

        return Response(data=data, status=status.HTTP_200_OK)


class TableDataProcessor(APIView):
    permission_classes = [AllowAny]

    def process_data(self, request):
        file_object = request.FILES.get("formFile")
        keyword = request.POST.get("filetype")
        result = data_process(file_object, keyword)

        return result

    def post(self, request):

        result = self.process_data(request)

        return Response(data=result, status=status.HTTP_200_OK)
