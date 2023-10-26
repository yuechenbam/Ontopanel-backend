import time
import copy
from owl_processor.utility.special_entities import datatype, annotation_properties
from owl_processor.utility.machester import Class
from rest_framework.exceptions import APIException
import json
from rdflib.util import find_roots, get_tree
from rdflib.term import URIRef
import os
import pandas as pd
import rdflib
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


class ImportOnto:
    def __init__(self, filepath, inputType):
        self.filepath = filepath
        self.inputType = inputType
        self.g = rdflib.Graph()
        self.base_onto = None
        # {namespace:prefix}
        self.namespace_list = {
            rdflib.URIRef("http://www.w3.org/2004/02/skos/core#"): "skos",
            rdflib.RDF: 'rdf',
            rdflib.RDFS: 'rdfs',
            rdflib.OWL: 'owl',
            rdflib.URIRef("http://www.w3.org/2000/10/swap/list#"): 'list',
            rdflib.URIRef("http://purl.org/dc/elements/1.1/"): 'dc'

        }
        self.imported_ontology = []
        self.deprecated = []
        self.entity_tree = {}
        self.anno_properties = copy.deepcopy(annotation_properties)
        self.df = pd.DataFrame(
            [],
            columns=(
                "EntityName",
                "BelongsTo",
                "RDFLabel",
                "SpecialInfo",
                "Color",
                "namespace",
                "EntityIRI"
            ),
        )

    def get_imports(self, address, keyword="URL"):
        parse_format_list = [
            "xml",
            "turtle",
            "html",
            "hturtle",
            "n3",
            "nquads",
            "trix",
            "rdfa",
        ]

        try:
            # address_name, address_data
            if keyword != "URL":
                address_name = address.name

            else:
                address_name = address

            parse_format = rdflib.util.guess_format(address_name)

            if parse_format:
                parse_format_list.insert(0, parse_format)

            for i in range(len(parse_format_list)):
                try:

                    self.g.parse(source=address,
                                 format=parse_format_list[i])

                    namespaces = list(self.g.namespaces())
                    for ns_prefix, namespace in namespaces:

                        if namespace not in self.namespace_list.keys():
                            if ns_prefix == "":
                                ns_prefix = "base"
                                self.g.bind("base", namespace)
                            self.namespace_list[namespace] = ns_prefix

                    break
                except Exception as e:
                    print(e)
                    pass
            if i == len(parse_format_list) - 1:
                raise APIException(
                    "Your ontology or its imported ontologies can not be accessed or parsed. Please check access or the format(rdf or turtle) or use merged file.")

            all_imports = list(self.g.objects(
                subject=None, predicate=rdflib.OWL.imports))

            if all_imports:
                for o in all_imports:
                    if o not in self.imported_ontology:
                        self.imported_ontology.append(o)
                        self.get_imports(o)

        except Exception as e:

            raise APIException(
                "Your ontology or its imported ontologies can not be accessed or parsed. Please check access or the format(rdf or turtle) or use merged file.")

    def compute_n3(self, entity, includeLabel=True):
        if type(entity) != rdflib.BNode:
            prefix, namespace, name = self.g.compute_qname(entity)
            if namespace not in self.namespace_list:
                self.namespace_list[namespace] = prefix
                # sub_n3 = self.g.namespace_manager.qname(sub)
            # n3 = self.namespace_list[namespace] + ":" + name

            # prefix_short = sub_n3.split(':')[0]
            n3 = prefix+':'+name

            rdfLabel = self.g.label(entity).strip()
            if includeLabel and rdfLabel and (rdfLabel != name):

                n3 = n3 + "(" + rdfLabel + ")"
        else:
            n3 = None

        return n3

    def assign_df(self, sub, belongsTo):

        if type(sub) != rdflib.BNode:

            prefix, namespace, name = self.g.compute_qname(sub)

            sub_n3 = self.compute_n3(sub, includeLabel=False)

            # get annotations
            annotations = {}

            color = 'none'

            for anno in self.anno_properties:
                anno_list = list(self.g.objects(subject=sub, predicate=anno))
                # see anno property used multi times
                if anno_list:
                    anno_list_n3 = []
                    if anno == rdflib.OWL.deprecated:

                        if anno_list[0].value == True:
                            self.deprecated.append(sub)

                    for j in anno_list:
                        try:
                            anno_list_n3.append(j.n3())
                        except Exception:
                            anno_list_n3.append(j)

                    anno_prop_n3 = self.compute_n3(anno)
                    annotations[anno_prop_n3] = anno_list_n3

            specialInfo = {}

            if belongsTo == "Class":
                all_info = Class(sub, graph=self.g).get_expression()
                for i in all_info.keys():
                    specialInfo[i] = [all_info[i]]

            elif belongsTo == "ObjectProperty":
                OP_attributes = {
                    "subPropertyOf": rdflib.RDFS.subPropertyOf,
                    "inverseOf": rdflib.RDFS.subPropertyOf,
                    "disjointWith": rdflib.OWL.disjointWith,
                    "domain": rdflib.RDFS.domain,
                    "range": rdflib.RDFS.range,
                    "equivalentTo": rdflib.OWL.equivalentProperty
                }

                for k, v in OP_attributes.items():
                    attr_list = [
                        self.compute_n3(x)
                        for x in self.g.objects(
                            subject=sub, predicate=v
                        ) if type(x) != rdflib.BNode
                    ]
                    if attr_list:
                        specialInfo[k] = attr_list

            elif belongsTo == "DatatypeProperty":
                DP_attributes = {
                    "subPropertyOf": rdflib.RDFS.subPropertyOf,
                    "disjointWith": rdflib.OWL.disjointWith,
                    "domain": rdflib.RDFS.domain,
                    "range": rdflib.RDFS.range,
                    "equivalentTo": rdflib.OWL.equivalentProperty
                }

                for k, v in DP_attributes.items():
                    attr_list = [
                        self.compute_n3(x)
                        for x in self.g.objects(
                            subject=sub, predicate=v
                        ) if type(x) != rdflib.BNode
                    ]
                    if attr_list:
                        specialInfo[k] = attr_list

            elif belongsTo == "AnnotationProperty":

                subPropertyOf = [
                    self.compute_n3(x)
                    for x in self.g.objects(
                        subject=sub, predicate=rdflib.RDFS.subPropertyOf
                    )if type(x) != rdflib.BNode
                ]
                if subPropertyOf:
                    specialInfo = {
                        "SubPropertyOf": subPropertyOf,
                    }

            elif belongsTo == "Individual":

                type_ind = [
                    self.compute_n3(x)
                    for x in self.g.objects(subject=sub, predicate=rdflib.RDF.type)if type(x) != rdflib.BNode
                ]
                if type_ind:
                    specialInfo = {"Type": type_ind}

            elif belongsTo == "Datatype":
                color = "#FF8C00"

            else:
                pass

            new_row = {
                "Color": color,
                "EntityName": sub_n3,
                "RDFLabel": self.g.label(sub),
                "Annotations": annotations,
                "SpecialInfo": specialInfo,
                "BelongsTo": belongsTo,
                "namespace": namespace,
                "EntityIRI": sub}

        else:
            new_row = None

        return new_row

    def extract_anno_properties(self):
        self.anno_properties.update(
            set(self.g.subjects(
                predicate=rdflib.RDF.type, object=rdflib.OWL.AnnotationProperty
            ))
        )

    def extract_infos(self):
        extract_entity = {
            rdflib.OWL.Class: "Class",
            rdflib.OWL.ObjectProperty: "ObjectProperty",
            rdflib.OWL.DatatypeProperty: "DatatypeProperty",
            rdflib.RDFS.Datatype: "Datatype",
        }

        for entity in extract_entity.keys():
            subjects = self.g.subjects(
                predicate=rdflib.RDF.type, object=entity
            )
            for s in subjects:
                new_row = self.assign_df(s, extract_entity[entity])
                if new_row:
                    self.df = self.df.append(new_row, ignore_index=True)
                if entity == rdflib.OWL.Class:
                    subjects_ind = self.g.subjects(
                        predicate=rdflib.RDF.type, object=s
                    )
                    for s_in in subjects_ind:
                        new_row = self.assign_df(s_in, "Individual")
                        if new_row:
                            self.df = self.df.append(
                                new_row, ignore_index=True)

        for anno in self.anno_properties:
            new_row = self.assign_df(anno, "AnnotationProperty")
            if new_row:
                self.df = self.df.append(new_row, ignore_index=True)

        # add datatype

        for dt in datatype:
            data_n3 = self.compute_n3(dt, includeLabel=False)
            new_row_datatype = {
                "Color": "#FF8C00",
                "EntityName": data_n3,
                "RDFLabel": '',
                "Annotations": {},
                "SpecialInfo": {},
                "BelongsTo": 'Datatype',
                "namespace": rdflib.OWL,
                "EntityIRI": dt}

            self.df = self.df.append(new_row_datatype, ignore_index=True)

    def map_function(self, x):
        n3 = self.compute_n3(x, includeLabel=False)
        if x in self.deprecated:
            return f'<del>{n3}</del>'
        else:
            return n3

    def find_roots(self, prop, obj):
        roots = []

        all_entities = set([i for i in self.g.subjects(
            predicate=rdflib.RDF.type, object=obj) if type(i) != rdflib.BNode])

        if obj == rdflib.OWL.AnnotationProperty:
            all_entities = self.anno_properties

        for i in all_entities:
            root_level = list(self.g.objects(subject=i, predicate=prop))

            if (not root_level) or (all([(x not in all_entities) for x in root_level])):

                tree = get_tree(
                    self.g,
                    i,
                    prop,
                    mapper=self.map_function,
                    sortkey=lambda s: (s[0].startswith('<del>'), s[0])
                )
                roots.append(tree)

        return sorted(roots, key=lambda s: (s[0].startswith('<del>'), s[0]))

    def get_roots(self):
        entity_type = {
            "Class": [rdflib.RDFS.subClassOf, rdflib.OWL.Class],
            "ObjectProperty": [rdflib.RDFS.subPropertyOf, rdflib.OWL.ObjectProperty],
            "DatatypeProperty": [rdflib.RDFS.subPropertyOf, rdflib.OWL.DatatypeProperty],
            "AnnotationProperty": [rdflib.RDFS.subPropertyOf, rdflib.OWL.AnnotationProperty],
        }

        for key, value in entity_type.items():
            self.entity_tree[key] = self.find_roots(value[0], value[1])

        # inidvidual and datatype, have no tree structure
        Inds = sorted(
            self.df[self.df["BelongsTo"] ==
                    "Individual"]["EntityName"].tolist()
        )
        self.entity_tree["Individual"] = [(x, []) for x in Inds]

        Datatype = sorted(
            self.df[self.df["BelongsTo"] ==
                    "Datatype"]["EntityName"].tolist()
        )
        self.entity_tree["Datatype"] = [(x, []) for x in Datatype]

    def run_all(self):

        if self.inputType == "URL":
            self.get_imports(self.filepath)
        else:
            self.get_imports(self.filepath, keyword="file")

        for namespace, prefix in self.namespace_list.items():
            rdflib.namespace.NamespaceManager(self.g).bind(
                prefix, namespace, override=True)

        self.extract_anno_properties()

        self.extract_infos()

        self.get_roots()

        used_namespaces = self.df["namespace"].unique()

        output_namespace = [
            f"{self.namespace_list[x]}:{x}" for x in used_namespaces
        ]

        self.df = (
            self.df.sort_values(by=["Color", "EntityName"])
            .drop(["namespace"], axis=1)
            .drop_duplicates(subset="EntityName")
            .set_index("EntityName")
        )

        return self.df, output_namespace, self.entity_tree


def onto_to_table(filepath, inputType="URL"):
    import_onto = ImportOnto(filepath, inputType=inputType)
    df, output_namespace, tree = import_onto.run_all()

    df = df.to_json(orient="index")

    return df, output_namespace, tree


if __name__ == "__main__":
    filepath = r"https://raw.githubusercontent.com/Mat-O-Lab/MSEO/main/MSEO_mid.owl"
    df, output_namespace, tree = onto_to_table(filepath)

    # with open(
    #     r"C:\Users\ychen2\Documents\Project\javascript\Vue\drawioPlugin\vanilla\peple.json",
    #     "w",
    # ) as f:
    #     json.dump({'title': "MESO", 'onto_source': filepath, 'onto_table': {"table": df, "tree": tree,
    #               "namespace": output_namespace}, 'author': 'no author'}, f)
