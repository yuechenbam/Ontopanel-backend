from drf_yasg import openapi

# request : form data

upload_url = openapi.Parameter('formURL', in_=openapi.IN_FORM, description="optional",
                               type=openapi.TYPE_STRING, default='')
upload_file = openapi.Parameter('formFile', in_=openapi.IN_FORM, description="optional",
                                type=openapi.TYPE_FILE)
upload_name = openapi.Parameter('formName', in_=openapi.IN_FORM, description='Tag Name',
                                type=openapi.TYPE_STRING, required=True)
doc_form_data = [upload_url, upload_file, upload_name]


# response


ontotable_schema = openapi.Schema(type=openapi.TYPE_OBJECT,
                                  description="Ontology details.",
                                  properties={
                                      "table": openapi.Schema(
                                          type=openapi.TYPE_OBJECT,
                                          description="Entities information."
                                      ),
                                      "namespaces": openapi.Schema(
                                          type=openapi.TYPE_ARRAY,
                                          items=openapi.Items(
                                              type=openapi.TYPE_STRING),
                                          description="namespaces list. "
                                      ),
                                      "tree": openapi.Schema(
                                          type=openapi.TYPE_OBJECT,
                                          description="Ontology hierarchy in nested arrays."
                                      ),

                                  }
                                  )

onto_response_schema = openapi.Schema(type=openapi.TYPE_OBJECT,
                                      properties={
                                          "id": openapi.Schema(
                                              type=openapi.TYPE_INTEGER,
                                              description="Ontology id in the databank"
                                          ),
                                          "title": openapi.Schema(
                                              type=openapi.TYPE_STRING,
                                              description="Tag name from input"
                                          ),
                                          "onto_source": openapi.Schema(
                                              type=openapi.TYPE_STRING,
                                              description="Input file name or URL"
                                          ),
                                          "onto_table": ontotable_schema,
                                          "author": openapi.Schema(type=openapi.TYPE_INTEGER, description="user id"),
                                          "date_created": openapi.Schema(type=openapi.TYPE_INTEGER, format=openapi.FORMAT_DATE),
                                      })


doc_onto_auth = openapi.Response('JSON to be displayed in Ontopanel-EntityManager', schema=onto_response_schema,
                                 examples={
                                     "application/json": {"title": "tag name",
                                                          "onto_source": "url or file name",
                                                          "onto_table": {"table": {"ns:test2": {"BelongsTo": "Class",
                                                                                                "RDFLabel": "Example",
                                                                                                "SpecialInfo": {"subClassOf": ["ns:test1"]},
                                                                                                "Color": "None",
                                                                                                "EntityIRI": "http:www.example.com/test",
                                                                                                "Annotations": {"cco:definition": ["It is an example.@en"]}}
                                                                                   },
                                                                         "namespaces": ["ns:http:www.example.com/"],
                                                                         "tree": {"Class": ["ns:test2", ["ns:test1", []]]}
                                                                         },
                                                          "author": "1",
                                                          "date_created": "2022-01-31"}

                                 })

doc_onto = openapi.Response('JSON to be displayed in Ontopanel-EntityManager',
                            schema=openapi.Schema(type=openapi.TYPE_OBJECT,
                                                  properties={
                                                      "title": openapi.Schema(
                                                          type=openapi.TYPE_STRING,
                                                          description="Tag name from input"
                                                      ),
                                                      "onto_source": openapi.Schema(
                                                          type=openapi.TYPE_STRING,
                                                          description="Input file name or URL"
                                                      ),
                                                      "onto_table": ontotable_schema,
                                                      "author": openapi.Schema(type=openapi.TYPE_STRING, default="no user"),
                                                  }),
                            examples={
                                "application/json": {"title": "tag name",
                                                     "onto_source": "url or file name",
                                                     "onto_table": {"table": {"ns:test2": {"BelongsTo": "Class",
                                                                                           "RDFLabel": "Example",
                                                                                           "SpecialInfo": {"subClassOf": ["ns:test1"]},
                                                                                           "Color": "None",
                                                                                           "EntityIRI": "http:www.example.com/test",
                                                                                           "Annotations": {"cco:definition": ["It is an example.@en"]}}
                                                                              },
                                                                    "namespaces": ["ns:http:www.example.com/"],
                                                                    "tree": {"Class": ["ns:test2", ["ns:test1", []]]}
                                                                    },
                                                     "author": "no user", }

                            })
