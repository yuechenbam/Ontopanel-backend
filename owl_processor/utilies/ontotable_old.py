import rdflib
import pandas as pd
import os

# no tree structure


class ImportOnto:
    def __init__(self, filepath, inputType):
        self.filepath = filepath
        self.inputType = inputType
        self.g = rdflib.Graph()
        self.base_onto = None
        # {namespace:prefix}
        self.namespace_list = {}
        self.imported_ontology = []
        self.error = None
        self.df = pd.DataFrame(
            [],
            columns=(
                "EntityName",
                "BelongsTo",
                "RDFLabel",
                "Defintion",
                "EntityIRI",
                "Color",
                "namespace",
            ),
        )

    def get_imports(self, address, keyword="URL"):
        try:
            if keyword != "URL":
                parse_format = rdflib.util.guess_format(address.name)
            else:
                parse_format = rdflib.util.guess_format(address)

            if parse_format:
                parse_format_list = [
                    parse_format,
                    "xml",
                    "turtle",
                    "html",
                    "hturtle",
                    "n3",
                    "nquads",
                    "trix",
                    "rdfa",
                ]
            else:
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

            t = rdflib.Graph()
            if keyword != "URL":
                address_data = address.read()

            for i in range(len(parse_format_list)):
                try:
                    if keyword != "URL":
                        t.parse(data=address_data, format=parse_format_list[i])
                        self.g.parse(data=address_data, format=parse_format_list[i])
                    else:
                        t.parse(address, format=parse_format_list[i])
                        self.g.parse(address, format=parse_format_list[i])

                    namespaces = list(self.g.namespaces())
                    for ns_prefix, namespace in namespaces:

                        if namespace not in self.namespace_list.keys():
                            if ns_prefix == "":
                                ns_prefix = "base"
                                self.g.bind("base", namespace)
                            self.namespace_list[namespace] = ns_prefix

                    break
                except Exception as e:
                    pass
            if i == len(parse_format_list) - 1:
                self.error = "Your ontology or it imported ontologies can not be parsed. Tried to merge ontologies first in xml or turtle."

            if list(t.triples((None, rdflib.OWL.imports, None))):
                for _, _, o in t.triples((None, rdflib.OWL.imports, None)):
                    if o not in self.imported_ontology:
                        self.get_imports(o)
                        self.imported_ontology.append(o)

        except Exception as e:
            self.error = "There is something wrong in parsing. Please use merged ontologies in xml or turtle."

    def assign_df(self, sub, belongsTo):
        deprecated = list(self.g.objects(subject=sub, predicate=rdflib.OWL.deprecated))
        if type(sub) != rdflib.BNode and (not deprecated):

            prefix, namespace, name = self.g.compute_qname(sub)
            if namespace not in self.namespace_list:
                self.namespace_list[namespace] = prefix
            # sub_n3 = self.g.namespace_manager.qname(sub)
            sub_n3 = self.namespace_list[namespace] + ":" + name
            # prefix_short = sub_n3.split(':')[0]

            new_row = {
                "Color": "none",
                "EntityIRI": sub,
                "EntityName": sub_n3,
                "RDFLabel": self.g.label(sub),
                "Defintion": self.g.comment(sub),
                "BelongsTo": belongsTo,
                "namespace": namespace,
            }
        else:
            new_row = None

        return new_row

    def extract_infos(self):
        extract_entity = {
            rdflib.OWL.Class: "Class",
            rdflib.OWL.ObjectProperty: "OP",
            rdflib.OWL.DatatypeProperty: "DP",
        }
        i = 0
        for entity in extract_entity.keys():
            for s, _, _ in self.g.triples((None, rdflib.RDF.type, entity)):
                new_row = self.assign_df(s, extract_entity[entity])
                if new_row:
                    self.df = self.df.append(new_row, ignore_index=True)
                if entity == rdflib.OWL.Class:
                    for s_in, _, _ in self.g.triples((None, rdflib.RDF.type, s)):
                        new_row = self.assign_df(s_in, "Individual")
                        if new_row:
                            self.df = self.df.append(new_row, ignore_index=True)

    def run_all(self):
        if self.inputType == "URL":
            self.get_imports(self.filepath)
        else:
            self.get_imports(self.filepath, keyword="file")

        if not self.error:
            self.extract_infos()

            used_namespaces = self.df["namespace"].unique()

            output_namespace = [
                f"{self.namespace_list[x]}:{x}" for x in used_namespaces
            ]

            self.df = self.df.sort_values(by=["Color", "EntityName"]).drop(
                ["namespace"], axis=1
            )

            return self.error, self.df, output_namespace
        else:
            return self.error, None, None


def onto_to_table(filepath, inputType="URL"):
    import_onto = ImportOnto(filepath, inputType=inputType)
    error, df, output_namespace = import_onto.run_all()
    if not error:
        df = df.to_json(orient="records")

    return error, df, output_namespace
