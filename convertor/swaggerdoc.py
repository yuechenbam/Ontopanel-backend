from drf_yasg import openapi
from numpy import minimum

# convertor request data

convertor_request_format = openapi.Schema(description='OWL format: "application/rdf+xml" or "turtle"',
                                          type=openapi.TYPE_STRING, default='application/rdf+xml')

convertor_request_fileData_errors = openapi.Schema(type=openapi.TYPE_OBJECT, description="the errors schema",
                                                   properties={
                                                       "node_errors": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(
                                                           type=openapi.TYPE_OBJECT, properties={
                                                                                     "id": openapi.Schema(type=openapi.TYPE_STRING, description="node id"),
                                                                                     "message": openapi.Schema(type=openapi.TYPE_STRING, description="error message")
                                                                                     })),

                                                       "edge_errors": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(
                                                           type=openapi.TYPE_OBJECT, properties={
                                                                                     "id": openapi.Schema(type=openapi.TYPE_STRING, description="edge id"),
                                                                                     "message": openapi.Schema(type=openapi.TYPE_STRING, description="error message")
                                                                                     })),
                                                       "relation_errors": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(
                                                           type=openapi.TYPE_OBJECT, properties={
                                                               "id_list": openapi.Schema(type=openapi.TYPE_ARRAY, description="id list", items=openapi.Items(
                                                                                         type=openapi.TYPE_STRING
                                                                                         )),
                                                               "message": openapi.Schema(type=openapi.TYPE_STRING, description="error message")
                                                           })),
                                                       "other_errors": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(
                                                           type=openapi.TYPE_OBJECT, properties={
                                                               "id": openapi.Schema(type=openapi.TYPE_STRING, description="shape id"),
                                                               "message": openapi.Schema(type=openapi.TYPE_STRING, description="error message")
                                                           })),
                                                   })

convertor_request_fileData = openapi.Schema(description='Drawio plot in JSON format',
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                "nodes": openapi.Schema(type=openapi.TYPE_OBJECT,
                                                                        additional_properties=openapi.Schema(type=openapi.TYPE_OBJECT, description="dict--{node id: dict}", properties={
                                                                            "type": openapi.Schema(type=openapi.TYPE_STRING, description="shape type defined by Ontopanel library"),
                                                                            "style": openapi.Schema(type=openapi.TYPE_STRING, description="shape style defined by drawio"),
                                                                            "label": openapi.Schema(type=openapi.TYPE_STRING, description="shape label defined by drawio"),
                                                                            "geometry": openapi.Schema(type=openapi.TYPE_STRING, description="shape geometry defined by drawio"),
                                                                            "objectData": openapi.Schema(type=openapi.TYPE_OBJECT, description="shape data"),


                                                                        })),
                                                "edges": openapi.Schema(type=openapi.TYPE_OBJECT,
                                                                        additional_properties=openapi.Schema(type=openapi.TYPE_OBJECT, description="dict--{edge id: dict}", properties={

                                                                            "type": openapi.Schema(type=openapi.TYPE_STRING, description="shape type defined by Ontopanel library"),
                                                                            "style": openapi.Schema(type=openapi.TYPE_STRING, description="shape style defined by drawio"),
                                                                            "label": openapi.Schema(type=openapi.TYPE_STRING, description="shape label defined by drawio"),
                                                                            "source": openapi.Schema(type=openapi.TYPE_STRING, description="starting connection defined by drawio"),
                                                                            "target": openapi.Schema(type=openapi.TYPE_STRING, description="ending connection defined by drawio"),
                                                                            "objectData": openapi.Schema(type=openapi.TYPE_OBJECT, description="shape data"),
                                                                        })
                                                                        ),
                                                "errors": convertor_request_fileData_errors

                                            }
                                            )


convertor_request_mappingData = openapi.Schema(
    type=openapi.TYPE_OBJECT, description="data for mapping in JSON, from '/convertor/formtable/' ")

convertor_request_schema = openapi.Schema(type=openapi.TYPE_OBJECT,
                                          example={
                                              "format": "application/rdf+xml",
                                              "fileData": {
                                                  "nodes": {
                                                      "BbhZRngCjeGGAclDs0S0-24": {
                                                          "type": "Class",
                                                          "style": "rounded=0;whiteSpace=wrap;html=1;snapToPoint=1;points=[[0.1,0],[0.2,0]];fillColor=#FFFFFF;",
                                                          "label": "cco:Agent",
                                                          "geometry": {"x": 50, "y": 520, "width": 100, "height": 30},
                                                          "objectData": {
                                                                  "IRI": "http://www.ontologyrepository.com/CommonCoreOntologies/Agent"
                                                          }
                                                      }
                                                  },
                                                  "edges": {
                                                      "BbhZRngCjeGGAclDs0S0-23": {
                                                          "type": "SubClassOf",
                                                          "style": "endArrow=block;html=1;fontColor=#000099;exitX=0.5;exitY=0;exitDx=0;exitDy=0;endFill=0;entryX=0.5;entryY=1;entryDx=0;entryDy=0;endSize=8;arcSize=0;rounded=0;",
                                                          "label": "",
                                                          "source": "BbhZRngCjeGGAclDs0S0-25",
                                                          "target": "BbhZRngCjeGGAclDs0S0-24",
                                                          "objectData": "none"
                                                      },

                                                  },
                                                  "errors": {
                                                      "node_errors": [],
                                                      "edge_errors": [],
                                                      "relation_errors": [],
                                                      "other_errors": [
                                                          {
                                                              "id": "3BGgxLQI-Xo-QI-qNfJG-2",
                                                              "message": "this shape is not from ontopanel-libary, please use libary or transform."
                                                          }
                                                      ]
                                                  },
                                              },
                                              "mappingData": None

                                          },
                                          properties={
                                              "format": convertor_request_format,
                                              "fileData": convertor_request_fileData,
                                              "mappingData": convertor_request_mappingData
                                          })


# response


convertor_response = openapi.Response(
    "owl result and errors", schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
        "result": openapi.Schema(description="owl in turtle or rdf/xml format", type=openapi.TYPE_STRING),
        "errors": convertor_request_fileData_errors
    }))

# convertor-tabledata

tabledata_file = openapi.Parameter(
    "myfile", in_=openapi.IN_FORM, description="excel or csv data", required=True, type=openapi.TYPE_FILE)
tabledata_decimal = openapi.Parameter("decimal", in_=openapi.IN_FORM, description="decimal or punkte of numerical values",
                                      required=True, type=openapi.TYPE_STRING, enum=[",", "."])
tabledata_filetype = openapi.Parameter("filetype", in_=openapi.IN_FORM, description="excel or csv",
                                       required=True, type=openapi.TYPE_STRING, enum=["excel", "csv"])
tabledata_nrows = openapi.Parameter("startRow", in_=openapi.IN_FORM,
                                    description="get the first N rows", default=0, type=openapi.TYPE_INTEGER, minimum=0, required=True)

tabledata_seperator = openapi.Parameter("seperator", in_=openapi.IN_FORM,
                                        description="Seperator for CSV data", type=openapi.TYPE_STRING, enum=[";", ","], required=True)
tabledata_skiprows = openapi.Parameter("skipRow", in_=openapi.IN_FORM,
                                       description="skip the first N rows", type=openapi.TYPE_INTEGER, default=0, minimum=0, required=True)

tabledata_parameters = [tabledata_file,
                        tabledata_decimal, tabledata_filetype, tabledata_nrows, tabledata_seperator, tabledata_skiprows]


tabledata_response = openapi.Response("Table in JSON format (orient in 'columns')", schema=openapi.Schema(type=openapi.TYPE_OBJECT, additional_properties=openapi.Schema(type=openapi.TYPE_OBJECT, description="column header", properties={
    "in_x": openapi.Schema(type=openapi.TYPE_STRING, description="value of row x and column header"),
})),
    examples={
    "application/json": {"Test piece ID": {"in_0": "HP-160-10m", "in_1": "HP-160-1"}, "Aging temperature": {"in_0": "160", "in_1": "160"}},
})
