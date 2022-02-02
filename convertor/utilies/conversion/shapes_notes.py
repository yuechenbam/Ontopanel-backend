# all the master-shapes in lower case
# work as connections
edges_shapes = ['subclassof',
                'subpropertyof',
                'rdftype',
                'objectproperty',
                'datatypeproperty',
                'annotationproperty',
                'equivalentclass',
                'equivalentproperty',
                'inverseof',
                'disjointclass',
                'disjointproperty',
                'domain',
                'range',
                'complementof',
                'sameas',
                'differentfrom',
                'connector']
# work as nodes
nodes_shapes = ['class',
                'individual',
                'datatype',
                'metadata',
                'namespace',
                'objectproperty',
                'datatypeproperty',
                'annotationproperty',
                'datavalue',
                'unionof',
                'intersectionof',
                'equivalentclass',
                'disjointclass',
                'customdatatype']

template_shapes = nodes_shapes + edges_shapes

# validation of shape combinations


class_rules = {'class+objectproperty': ['class', 'unionof', 'intersectionof'],
               "class+objectproperty(hasvalue)": ['individual', 'datatype'],

               'class+subclassof': ['class', 'unionof', 'intersectionof'],
               'class+equivalentclass': ['class', 'unionof', 'intersectionof'],
               'class+disjointclass': ['class', 'unionof', 'intersectionof'],
               'class+complementof': ['class', 'unionof', 'intersectionof'],

               }

ind_rules = {'individual+rdftype': ['class', 'unionof', 'intersectionof'],
             'individual+objectproperty': ['individual'],
             'individual+datatypeproperty': ['datavalue'],
             'bnode+op': 'individual',
             'bnode+dp': 'datavalue',
             'individual+sameas': 'individual',
             'individual+differentfrom': 'individual'}

connectors_rules = {
    'disjointclass+connector': ['class', 'unionof', 'intersectionof'],
    'equivalentclass+connector': ['class', 'unionof', 'intersectionof'],
    'unionof+connector': ['class', 'unionof', 'intersectionof'],
    'intersectionof+connector': ['class', 'unionof', 'intersectionof'],
    'alldifferent+connector': 'individual',

}

op_rules = {'objectproperty+subpropertyof': 'objectproperty',
            'objectproperty+domain': ['class', 'unionof', 'intersectionof'],
            'objectproperty+range': ['class', 'unionof', 'intersectionof'],
            'objectproperty+equivalentproperty': 'objectproperty',
            'objectproperty+inverseof': 'objectproperty',
            'objectproperty+disjointproperty': 'objectproperty',
            }
dp_rules = {
    'datatypeproperty+subpropertyof': 'datatypeproperty',
    'datatypeproperty+domain': ['class', 'unionof', 'intersectionof'],
    'datatypeproperty+range': 'datatype',
    'datatypeproperty+equivalentproperty': 'datatypeproperty',
    'datatypeproperty+disjointproperty': 'datatypeproperty',
}

ap_rules = {
    'annotationproperty+subpropertyof': 'annotationproperty',
    'class+annotationproperty': 'datavalue',
    'objectproperty+annotationproperty': 'datavalue',
    'datatypeproperty+annotationproperty': 'datavalue',
    'annotationproperty+annotationproperty': 'datavalue',
    'individual+annotationproperty': 'datavalue',
    'datatype+annotationproperty': 'datavalue',


}

sum_rules = {**class_rules, **ind_rules, **
             op_rules, **dp_rules, **connectors_rules, **ap_rules}


# special mapping names used for imported ontology or data mapping
# the result names in shape data will be considered as mapping data
mapping_names = ['EntityIRI',
                 'EntityName',
                 'BelongsTo',
                 'RDFLabel',
                 'MappingID',
                 'MappingIRI']
