from django.http.response import HttpResponse, HttpResponseNotFound
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework import status
import json
from rest_framework.exceptions import APIException
from .utilies.conversion.graph_to_rdf import MakeOntology
from .utilies.datauploader.data_process import file_to_json
import sys
import traceback

"""
Convertor that communicates with Ontopanel-Convertor in the frontend.
More detailed API documentation is available in the README.
"""


class GraphConvertor(APIView):
    permission_classes = [AllowAny]

    """
    post: convert drawio graph in JSON format into OWL and return errors.
    """

    def process_data(self, request):
        data = json.loads(request.body)
        file_format = data['format'].strip()

        onto = MakeOntology(data)

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

    """
    post: work in the data-mapping window to convert EXCEL or CSV to JSON format.
    """

    def process_data(self, request):
        file_object = request.FILES.get("myfile")
        decimal = request.POST.get("decimal")
        keyword = request.POST.get("filetype")
        nrows = int(request.POST.get("startRow"))
        seperator = request.POST.get("seperator")
        skip_rows = int(request.POST.get("skipRow"))

        if nrows == 0:
            nrows = None
        try:
            result = file_to_json(file_object, keyword,
                                  decimal, nrows, skip_rows, sep=seperator)

        except Exception as e:
            exc_type, exc_value, exc_traceback_obj = sys.exc_info()
            traceback.print_tb(exc_traceback_obj)
            if type(e) == AssertionError:
                raise APIException(
                    str(e))

            raise APIException(
                "File type does not match or can not be processed.")

        return result

    def post(self, request):

        result = self.process_data(request)

        return Response(data=result, status=status.HTTP_200_OK)
