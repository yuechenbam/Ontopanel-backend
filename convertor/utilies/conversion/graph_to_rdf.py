from convertor.utilies.conversion.helpfunc import *
from convertor.utilies.conversion.shapes_notes import *
import os
import re
import pandas as pd
import rdflib
from rdflib import Literal, XSD, DCTERMS, DC, URIRef, RDFS, RDF, OWL
from rdflib import Namespace, Graph, BNode
from rdflib.namespace import NamespaceManager
from rdflib.extras.infixowl import Class, Restriction, Ontology, BooleanClass
from rdflib.collection import Collection
import json
import itertools
import logging
from rest_framework.exceptions import APIException
import sys
import traceback
import warnings
import numpy as np
warnings.simplefilter(action='ignore', category=np.VisibleDeprecationWarning)


logger = logging.getLogger(__name__)

'''
Class MakeEntityDF: 
used to decode the graphs in diagrams.net and extract entities and their relationships and
put them in a dataframe.

Class MakeOntology: 
convert the dataframe to the OWL language

Attributes:
data: graph information in JSON format

'''


class MakeEntityDF():
    def __init__(self, data):
        file_data = data['fileData']
        self.nodes = file_data['nodes']
        self.edges = file_data['edges']

        self.mapping_df = pd.DataFrame.from_dict(
            data['mappingData'], orient="columns").fillna("")

        # resctritions: only for class, some, all, cardinality, hasValue
        # triples: only for individuals
        # characteristics: only for properties, F,IF....
        # specialRelations: for all: type, subClassOf, domain, range .....
        # annotations: for all
        # BelongsTo: see in shapes_templates

        self.combined_df = pd.DataFrame([], columns=('ID', 'BelongsTo',  'name', 'restrictions',
                                                     'specialRelations', 'triples', 'characteristics', 'annotations', 'hasMapping'))

        self.combined_df = self.combined_df.astype('object').set_index('ID')

        self.base_IRI = None

        self.namespaces = {}
        # self.errors = {"node_errors": [],
        #                "edge_errors": [], "relation_errors": [], "other_errors": []}
        self.errors = file_data['errors']
        self.meta_data = []

    def _extract_nodes(self):
        # in node_df
        # belongsTo: class, individual, datatype, datavalue,
        # belongsTo: 'intersectionof', 'unionof', 'equivalentclass', 'disjointclass', 'alldifferent', 'oneof'
        # belongsTo: others

        # must find namespace first

        for node_id, node_value in self.nodes.items():
            node_style = node_value['style']
            node_label = clean_html_tags(node_value['label'])
            _, node_type = seperate_string_pattern(node_value['type'].lower())

            # namespace, save in self.namespace
            if node_type == 'namespace':
                namespaces = node_label.split("|")
                for namespace in namespaces:
                    try:
                        prefix, name = namespace.split(':', 1)
                        # use validator to check whether the URI is ok
                        # accepted ones are http://yue.com/ or http://yue.com/a#

                        assert uri_validator(name.strip(
                        )), f'"{name.strip()}" does not seem to be a valid url, please follow the form in shape: Namespace.'

                        self.namespaces[prefix.strip().lower()] = Namespace(
                            name.strip())

                        # identify the base IRI

                        if not self.base_IRI:

                            self.base_IRI = URIRef(
                                name.strip())

                    except (ValueError, AssertionError) as e:
                        logging.warning(e)
                        if type(e) == ValueError:
                            e = f'Namespaces does not form correctly.'
                        error = {
                            'message': str(e),
                            'id': node_id
                        }
                        self.errors["node_errors"].append(error)
                        continue

        for node_id, node_value in self.nodes.items():
            node_style = node_value['style']
            node_label = clean_html_tags(node_value['label'])
            _, node_type = seperate_string_pattern(node_value['type'].lower())

            # metadata, save in self.meta_data
            if node_type == 'metadata':
                annotations = node_label.split("|")
                for ann in annotations:
                    try:
                        assert len(ann.split(
                            ":")) >= 3, f"The form of metaData {ann} should be preifx:name:string."
                        ann_prefix = ann.split(":")[0].strip()
                        assert ann_prefix in self.namespaces, f"Prefix {ann_prefix} of metaData {ann} is not defined."
                        ann_type = ann.split(":")[1].strip()
                        if ann_type == "imports":
                            ann_name = ann.split(":")[2:]
                            ann_name = ":".join(ann_name).strip()
                        else:
                            ann_name = ann.split(":")[2].strip()

                        validated = uri_validator(
                            self.namespaces[ann_prefix][ann_type])
                        assert validated, f'"{self.namespaces[ann_prefix][ann_type]}" in the shape is not a valid URI. It should not contains unwise characters, such as {{}}.'

                        self.meta_data.append(
                            [self.namespaces[ann_prefix][ann_type], Literal(ann_name)])
                    except Exception as e:
                        logging.warning(e)
                        error = {
                            'message': str(e),
                            'id': node_id
                        }
                        self.errors["node_errors"].append(error)
                        continue

                self.combined_df.loc[node_id, ['name', 'BelongsTo']] = [
                    'empty', 'metadata']

            # individual or class or annotationproperty, save in self.combined_df
            elif node_type == 'class':
                try:
                    node_URI = self.label_or_uri(node_value, node_label)
                    self.combined_df.loc[node_id, ['name', 'BelongsTo']] = [
                        node_URI, node_type]

                except Exception as e:
                    logging.warning(e)
                    error = {
                        "message": str(e),
                        "id": node_id
                    }
                    self.errors["node_errors"].append(error)
                    continue

            # individuals
            elif node_type == 'individual':
                try:
                    node_URI_ind = self.label_or_uri(
                        node_value, node_label)
                    self.combined_df.loc[node_id, ['name', 'BelongsTo']] = [
                        node_URI_ind, 'individual']

                    object_value = node_value['objectData']
                    if "MappingCol" in object_value:
                        mapping_col = object_value["MappingCol"].strip()
                        assert mapping_col in self.mapping_df.columns, f'The column "{mapping_col}" is not found in the mapping dataset. This mapping request is ignored.'

                        self.combined_df.loc[node_id,
                                             'hasMapping'] = mapping_col

                except Exception as e:
                    logging.warning(e)
                    error = {
                        "message": str(e),
                        "id": node_id
                    }

                    self.errors["node_errors"].append(error)
                    continue

            # objectproperty, save in self.combined_df
            elif node_type == 'objectproperty':
                # split (res) part in label
                # only rhombus shape
                res, op_uri = seperate_string_pattern(node_label)

                # whether it contains '(F,IF....)'
                restrictions = res.split('(')

                if len(restrictions) == 2:
                    res_com = restrictions[1].split(',')
                    op_func = ['F', 'IF', 'T', 'S', 'AS', 'R', 'IR']
                    res_list = [x.strip()
                                for x in res_com if x.strip() in op_func]
                else:
                    res_list = []

                # can have extrat URI
                try:
                    op_URI = self.label_or_uri(node_value, op_uri)
                    self.combined_df.loc[node_id, ['name', 'BelongsTo', 'characteristics']] = [
                        op_URI, 'objectproperty', res_list]

                except Exception as e:
                    logging.warning(e)
                    error = {
                        "message": str(e),
                        "id": node_id
                    }
                    self.errors["node_errors"].append(error)

            # datatypeproperty, save in self.combined_df
            elif node_type == 'datatypeproperty':
                if 'rhombus' in node_style:
                    # datatypeProperty as node
                    res, dp_uri = seperate_string_pattern(node_label)
                    res_com = ['F'] if 'F' in res else []
                    try:
                        dp_URI = self.label_or_uri(node_value, dp_uri)

                        self.combined_df.loc[node_id, ['name', 'BelongsTo', 'characteristics']] = [
                            dp_URI, 'datatypeproperty', res_com]

                    except Exception as e:
                        logging.warning(e)
                        error = {
                            "message": str(e),
                            "id": node_id
                        }
                        self.errors["node_errors"].append(error)
                else:
                    # datatypeproperty combined with class, as underblock
                    try:
                        res, cleaned_node_label = seperate_string_pattern(
                            node_label)

                        # two forms
                        # ns:datatypeproperty ~ ns:datatype
                        # ns:datatypeproperty

                        if '~' in cleaned_node_label:
                            # if datatype exists, make up an id for datatype, save in nodes_df, datatype_id = id +'_dt'
                            node_dp, node_dt = cleaned_node_label.split('~', 1)
                            node_URI_dp = self.label_or_uri(
                                node_value, node_dp, keyword="IRI_DP")
                            node_URI_dt = self.label_or_uri(
                                node_value, node_dt, keyword='IRI_DT')

                            node_dt_id = node_id + '_dt'

                            self.combined_df.loc[node_dt_id, ['name', 'BelongsTo']] = [
                                node_URI_dt, 'datatype']

                            self.combined_df.loc[node_id, ['name', 'BelongsTo']] = [
                                node_URI_dp, 'datatypeproperty']

                        else:
                            node_URI_dp = self.label_or_uri(
                                node_value, cleaned_node_label, keyword="IRI_DP")
                            self.combined_df.loc[node_id, ['name', 'BelongsTo']] = [
                                node_URI_dp, 'datatypeproperty']

                        if res:
                            if 'F' in res:
                                self.combined_df.loc[node_id, [
                                    'characteristics']] = ['F']

                    except Exception as e:
                        error = {
                            "message": str(e),
                            "id": node_id,
                        }
                        self.errors["node_errors"].append(error)

            # intersection of, union of..., save in self.combined_df
            elif node_type in ['intersectionof', 'unionof', 'equivalentclass', 'disjointclass', 'alldifferent', 'oneof']:
                self.combined_df.loc[node_id, ['name', 'BelongsTo']] = [
                    node_type, node_type]

            # customdatatype, save in self.combined_df
            elif node_type == 'customdatatype':
                datatypes = node_label.split("|")
                for i in range(len(datatypes)):
                    datatype = datatypes[i].strip()
                    try:
                        prefix, name = datatype.split(':', 1)
                        # use validator to check whether the URI is ok
                        # accepted ones are http://yue.com/ or http://yue.com/a#

                        assert prefix in self.namespaces, f"Prefix {prefix} is not defined."

                        name = re.sub(" ", "", name)
                        node_URI = self.namespaces[prefix][name]

                        validated = uri_validator(node_URI)
                        assert validated, f'"{node_URI}" in the shape is not a valid URI. It should not contains unwise characters, such as {{}}.'

                        node_dt_id = node_id + f'_{i}'
                        self.combined_df.loc[node_dt_id, ['name', 'BelongsTo']] = [
                            node_URI, 'datatype']

                    except Exception as e:
                        logging.warning(e)
                        error = {
                            'message': str(e),
                            'id': node_id
                        }
                        self.errors["node_errors"].append(error)
                        continue
                # used for relationship check

                self.combined_df.loc[node_id, ['name', 'BelongsTo']] = [
                    node_URI, 'customdatatype']

            # datatype, save in self.combined_df
            elif node_type == "datatype":
                try:
                    node_URI = self.label_or_uri(node_value, node_label)

                    self.combined_df.loc[node_id, ['name', 'BelongsTo']] = [
                        node_URI, 'datatype']

                except Exception as e:
                    logging.warning(e)
                    error = {
                        'message': str(e),
                        'id': node_id
                    }
                    self.errors["node_errors"].append(error)
                    continue

            elif node_type == "datavalue":
                # used for datatypeproperty and annotations
                # 'datavalue'^^datatype, belongsTo datavalue
                try:
                    if "^^" in node_label and "@" in node_label:
                        assert False, 'One datavalue can only contain one of ^^(datatype) or @(lang)'

                    if "^^" in node_label:
                        datavalue_text = node_label.split(
                            "^^")[0].strip(' "\xa0')
                        datatype_text = node_label.split("^^")[-1].strip()
                        datatype_URI = self.label_or_uri(
                            node_value, datatype_text, keyword="IRI_DT")
                        datavalue = Literal(
                            datavalue_text, datatype=datatype_URI)

                        # check whether it can creat datatype automatically
                        node_dt_id = node_id + '_dt'
                        self.combined_df.loc[node_dt_id, ['name', 'BelongsTo']] = [
                            datatype_URI, 'datatype']

                        self.combined_df.loc[node_id, ['name', 'BelongsTo']] = [
                            datavalue, 'datavalue']

                    elif "@" in node_label:
                        datavalue_text = node_label.split(
                            "@")[0].strip(' "\xa0')

                        lang_type = node_label.split("@")[-1].strip()
                        datavalue = Literal(
                            datavalue_text, lang=lang_type)

                        self.combined_df.loc[node_id, ['name', 'BelongsTo']] = [
                            datavalue, 'datavalue']

                    else:
                        datavalue_text = node_label.strip(' "\xa0')
                        datavalue = Literal(
                            datavalue_text)
                        self.combined_df.loc[node_id, ['name', 'BelongsTo']] = [
                            datavalue, 'datavalue']

                    object_value = node_value['objectData']
                    if "MappingCol" in object_value:
                        mapping_col = object_value["MappingCol"].strip()
                        assert mapping_col in self.mapping_df.columns, f'The column "{mapping_col}" is not found in the mapping dataset.This mapping request is ignored.'
                        self.combined_df.loc[node_id,
                                             'hasMapping'] = mapping_col

                except Exception as e:
                    logging.warning(e)
                    error = {
                        'message': str(e),
                        'id': node_id
                    }
                    self.errors["node_errors"].append(error)
                    continue
            elif node_type == "annotationproperty":
                res, ap_uri = seperate_string_pattern(node_label)
                try:
                    ap_URI = self.label_or_uri(node_value, ap_uri)

                    self.combined_df.loc[node_id, ['name', 'BelongsTo']] = [
                        ap_URI, 'annotationproperty']

                except Exception as e:
                    logging.warning(e)
                    error = {
                        "message": str(e),
                        "id": node_id
                    }
                    self.errors["node_errors"].append(error)

            else:
                # the rest are marked with others
                if node_type in nodes_shapes:
                    self.combined_df.loc[node_id, ['name', 'BelongsTo']] = [
                        node_label, node_type]
                else:
                    error = {
                        'message': f'Shape {node_type} is not from libary.',
                        'id': node_id
                    }
                    self.errors["node_errors"].append(error)

    def label_or_uri(self, value, label, keyword="IRI"):

        # search for keyword:  URI or URI_*(class or dt)

        object_value = value['objectData']
        node_IRI = ""
        if keyword in object_value:
            iri_value = object_value[keyword].strip()
            if iri_value != 'Null' and iri_value:
                validated = uri_validator(iri_value)
                assert validated, f'"{iri_value}" in shape data {keyword} is not a valid URI. Should be URI, Null, or empty.'
                node_IRI = URIRef(iri_value)

        if not node_IRI:

            check = label.split(":", 1)  # Check if error in text

            assert len(
                check) == 2, f'IRI form of "{label}" label should be prefix:name.'

            prefix = check[0].strip()
            assert prefix in self.namespaces, f"Prefix {prefix} is not defined."

            name = check[-1].strip()

            name = re.sub(" ", "", name)
            node_IRI = self.namespaces[prefix][name]
            validated = uri_validator(node_IRI)
            assert validated, f'"{node_IRI}" in the shape is not a valid URI. It should not contains unwise characters, such as {{}}.'

        return node_IRI

    def _extract_edges(self):
        # in edges_df
        # belongsTo: objectproperty, datatypeproperty, others

        for edge_id, edge_value in self.edges.items():
            edge_style = edge_value['style']
            edge_label = clean_html_tags(edge_value['label'])
            _, edge_type = seperate_string_pattern(edge_value['type'].lower())
            try:
                if edge_type == 'objectproperty':
                    edge_res, edge_label = seperate_string_pattern(edge_label)
                    edge_uri = self.label_or_uri(edge_value, edge_label)
                    res_list = []
                    if edge_res:
                        op_func = ['F', 'IF', 'T', 'S', 'AS', 'R', 'IR']
                        res_list = [x.strip()
                                    for x in edge_res.split(',') if x.strip() in op_func]

                    self.combined_df.loc[edge_id, ['name', 'BelongsTo', 'characteristics']] = [
                        edge_uri, 'objectproperty', res_list]

                elif edge_type == 'datatypeproperty':
                    _, edge_label = seperate_string_pattern(edge_label)
                    edge_uri = self.label_or_uri(edge_value, edge_label)
                    self.combined_df.loc[edge_id, ['name', 'BelongsTo']] = [
                        edge_uri, 'datatypeproperty']

                elif edge_type == 'annotationproperty':
                    _, edge_label = seperate_string_pattern(edge_label)
                    edge_uri = self.label_or_uri(edge_value, edge_label)
                    self.combined_df.loc[edge_id, ['name', 'BelongsTo']] = [
                        edge_uri, 'annotationproperty']

                else:
                    # the rest are marked with others

                    assert edge_type in edges_shapes, f'Shape {edge_type} is not from libary.'

                    self.combined_df.loc[edge_id, ['name', 'BelongsTo']] = [
                        edge_label, 'others']

            except Exception as e:
                logging.warning(e)
                error = {
                    'message': str(e),
                    'id': edge_id
                }
                self.errors["edge_errors"].append(error)
                continue

    def _extract_relations(self):

        # node relations. stacked
        # only loop through the nodes_df
        # two forms
        # below: individual, upper: class
        # below: datatypeproperty, upper:class

        sub_node_class = self.combined_df[self.combined_df['BelongsTo'] == 'class']

        for node_id, node_value in self.nodes.items():

            node_label = clean_html_tags(node_value['label'])
            _, node_type = seperate_string_pattern(node_value['type'].lower())
            node_style = node_value['style']

            if node_id in self.combined_df.index:
                for node2_id, node2_value in self.nodes.items():
                    if node2_id in self.combined_df.index:

                        geo1 = node_value['geometry']
                        geo2 = node2_value['geometry']
                        stacked = compare_geo(geo1, geo2)
                        # node2 is above node1
                        if stacked:
                            _, node2_type = seperate_string_pattern(
                                node2_value['type'].lower())
                            if node_type == 'individual' and node2_type == "class":
                                self.combined_df.at[node_id, 'specialRelations'] = [[
                                    'rdftype', node2_id]]

                            elif node_type == 'datatypeproperty' and node2_type == "class":
                                # datatypeproperty
                                # check whether this datatypeproperty node has datatype nor not
                                dt_id = node_id+'_dt'
                                dt_exist = dt_id in self.combined_df.index

                                try:
                                    dt_res, _ = seperate_string_pattern(
                                        node_label)

                                    if "all" in dt_res or "∀" in dt_res:
                                        # should have datatype, and it is made in _extract_nodes. id = original_id +'_dt'

                                        assert dt_exist, 'Class datatypeproperty restriction must have a datatype.'

                                        self.combined_df.at[node2_id, 'restrictions'] += [['all',
                                                                                           node_id, dt_id]]

                                    elif "someValuesFrom" in dt_res or "some" in dt_res or "∃" in dt_res:
                                        # should have datatype, and it is made in _extract_nodes. id = original_id +'_dt'
                                        dt_id = node_id+'_dt'

                                        assert dt_exist, 'Class datatypeproperty restriction must have a datatype.'

                                        self.combined_df.at[node2_id, 'restrictions'] += [['some',
                                                                                           node_id, dt_id]]

                                    elif re.match('(.+)\\((.+)\\)', node_label):
                                        # cardinality

                                        dt_id = node_id+'_dt'

                                        assert dt_exist, 'Class datatypeproperty restriction must have a datatype.'

                                        max_min_card = re.match(
                                            '(.+)\\((.+)\\)', node_label).group(2)

                                        max_min_card = max_min_card.split("..")

                                        assert len(
                                            max_min_card) == 2, 'Please use (N1..N2) to express cardinality.'
                                        min_card = max_min_card[0].strip()
                                        max_card = max_min_card[1].strip()
                                        assert min_card.isdigit(), "MinQualifiedCardinality N1 in (N1..N2) can only be positive number or 0, 0 means no minQualifiedCardinality."
                                        assert max_card.isdigit() or max_card == "N" or max_card == "N2", "MaxQualifiedCardinality N2 in (N1..N2) can only be positive number or N or N2, N or N2 means no maxQualifiedCardinality."
                                        max_min_card_label = min_card+'..'+max_card
                                        self.combined_df.at[node2_id, 'restrictions'] += [[max_min_card_label,
                                                                                           node_id, dt_id]]

                                    else:
                                        # domain and range
                                        if "dashed=1" in node_style:
                                            # no domain
                                            if dt_exist:
                                                self.combined_df.at[node_id,
                                                                    'specialRelations'] += [['range', dt_id]]
                                        else:
                                            # domain
                                            self.combined_df.at[node_id,
                                                                'specialRelations'] += [['domain', node2_id]]

                                            if dt_exist:
                                                self.combined_df.at[node_id,
                                                                    'specialRelations'] += [['range', dt_id]]

                                except Exception as e:
                                    error = {
                                        'message': str(e),
                                        'id': node_id
                                    }
                                    self.errors['edge_errors'].append(error)
                            else:
                                error = {
                                    "message": f"This stacked relationship is not allowed, please follow the libary.",
                                    "id_list": [node_id, node2_id]

                                }
                                self.errors["relation_errors"].append(error)

        # edge relations. connected
        # loop the edges that in edges_df and are really edges(arrows, not nodes)
        for edge_id, edge_value in self.edges.items():
            if edge_id in self.combined_df.index:
                edge_style = edge_value['style']
                edge_label = clean_html_tags(edge_value['label'])
                _, edge_type = seperate_string_pattern(
                    edge_value['type'].lower())

                source = edge_value['source']
                target = edge_value['target']

                total_ids = self.combined_df.index.values.tolist(
                )

                if source == 'none' or target == 'none':
                    error = {
                        'message': f'{edge_id} is not both sides connected, please check.',
                        'id': edge_id
                    }
                    self.errors['edge_errors'].append(error)

                # ony process: source and target exist and they are correctly formed(in df)
                elif source in total_ids and target in total_ids:
                    try:
                        # validate the combination

                        res, predica = seperate_string_pattern(edge_type)
                        sub = self.combined_df.at[source,
                                                  'BelongsTo']
                        obj = self.combined_df.at[target,
                                                  'BelongsTo']

                        if "(hasValue)" in edge_label:
                            # special cases for (hasValue)objectproperty
                            predica = predica+"(hasvalue)"

                        validated = onRule_checker(sub, predica, obj)
                        assert validated, f'The combination {sub}+{predica}+{obj} is not allowed, please check the owl rule(AllowedCombinations) in Ontopanel-Library, or read this link: https://www.w3.org/TR/owl-features/.'

                        # if validated, then go on

                        if edge_type in ["subclassof", "equivalentclass", "disjointclass", 'complementof', "rdftype", 'sameas', 'differentfrom']:

                            self.combined_df.at[source,
                                                'specialRelations'] += [[edge_type, target]]
                            # these are mutual
                            if edge_style in ["equivalentclass", "disjointclass", 'sameas', 'differentfrom']:
                                self.combined_df.at[target,
                                                    'specialRelations'] += [[edge_type, source]]

                        elif edge_type == 'connector':
                            # used to connect ellipse

                            self.combined_df.at[source,
                                                'specialRelations'] += [['connector', target]]

                        elif edge_type in ['subpropertyof', 'equivalentproperty', 'inverseof', 'disjointproperty']:
                            self.combined_df.at[source,
                                                'specialRelations'] += [[edge_type, target]]

                            # these three are both-way
                            if edge_type in ['equivalentproperty', 'inverseof', 'disjointproperty']:
                                self.combined_df.at[target,
                                                    'specialRelations'] += [[edge_type, source]]

                        elif edge_type in ['domain', 'range']:
                            self.combined_df.at[source,
                                                'specialRelations'] += [[edge_type, target]]

                        elif edge_type == 'objectproperty':
                            # two forms
                            # starts with class: restriction, domain or range
                            # starts with individual: normal triple

                            if sub == 'class':
                                class_res, _ = seperate_string_pattern(
                                    edge_label)

                                if "hasValue" in class_res:
                                    self.combined_df.at[source, 'restrictions'] += [['hasvalue',
                                                                                    edge_id, target]]
                                elif "allValuesFrom" in class_res or "all" in class_res or "∀" in class_res:

                                    self.combined_df.at[source, 'restrictions'] += [['all',
                                                                                    edge_id, target]]
                                elif "someValuesFrom" in class_res or "some" in class_res or "∃" in class_res:
                                    self.combined_df.at[source, 'restrictions'] += [['some',
                                                                                    edge_id, target]]

                                elif re.match('(.+)\\((.+)\\)', edge_label):
                                    # cardinality
                                    max_min_card = re.match(
                                        '(.+)\\((.+)\\)', edge_label).group(2)

                                    try:
                                        max_min_card = max_min_card.split(
                                            "..")
                                        assert len(
                                            max_min_card) == 2, 'Please use (N1..N2) to express cardinality.'
                                        min_card = max_min_card[0].strip()
                                        max_card = max_min_card[1].strip()
                                        assert min_card.isdigit(), "MinQualifiedCardinality N1 in (N1..N2) can only be positive number or 0, 0 means no minQualifiedCardinality."
                                        assert max_card.isdigit() or max_card == "N" or max_card == "N2", "MaxQualifiedCardinality N2 in (N1..N2) can only be positive number or N or N2, N or N2 means no maxQualifiedCardinality."
                                        max_min_card_label = min_card+'..'+max_card
                                        self.combined_df.at[source, 'restrictions'] += [[max_min_card_label,
                                                                                        edge_id, target]]

                                    except Exception as e:
                                        error = {
                                            'message': str(e),
                                            'id': edge_id
                                        }
                                        self.errors['edge_errors'].append(
                                            error)

                                else:
                                    # domain and range, save in self.combined_df
                                    if "dashed=1" in edge_style:
                                        if "startFill=1" in edge_style:
                                            self.combined_df.at[edge_id,
                                                                'specialRelations'] += [['domain', source]]

                                    else:
                                        if "startArrow=oval" not in edge_style or "startFill=1" in edge_style:
                                            self.combined_df.at[edge_id,
                                                                'specialRelations'] += [['domain', source]]
                                            self.combined_df.at[edge_id,
                                                                'specialRelations'] += [['range', target]]

                                        elif "startFill=0" in edge_style:
                                            self.combined_df.at[edge_id,
                                                                'specialRelations'] += [['range', target]]

                            else:
                                # individuals
                                # combination has been checked in the first place
                                self.combined_df.at[source,
                                                    'triples'] += [[edge_id, target]]

                        elif edge_type == 'datatypeproperty':
                            self.combined_df.at[source,
                                                'triples'] += [[edge_id, target]]

                        elif edge_type == 'annotationproperty':
                            self.combined_df.at[source,
                                                'annotations'] += [[edge_id, target]]
                        else:
                            pass

                    except Exception as e:
                        logger.warning(e)
                        error = {
                            "message": str(e),
                            "id_list": [target, edge_id, source]

                        }
                        self.errors["relation_errors"].append(error)

                # source or target is not collected in _extract_nodes, due to wrong format or shape not from libary.
                else:
                    error = {
                        'message': f'source or target of {edge_id} is formed wrong or cant be reconginzed, so this relation is ignored.',
                        'id': edge_id
                    }
                    self.errors['edge_errors'].append(error)

    def _run_module(self):
        if self.mapping_df.empty:
            error = {
                "id": "null",
                "message": 'There is not data uploaded for mapping.'}
            self.errors["other_errors"].append(error)

        self._extract_nodes()
        self._extract_edges()
        self.combined_df = self.combined_df.fillna('empty').applymap(
            lambda x: [] if x == 'empty' else x)
        self.combined_df = self.combined_df.fillna('empty').applymap(
            lambda x: [] if x == 'empty' else x)
        self._extract_relations()


class MakeOntology(MakeEntityDF):
    def __init__(self, data):
        super().__init__(data)

        self.g = Graph()

        self._exe_all()

    def _create_namespace(self):
        for key, value in self.namespaces.items():
            self.g.bind(key, value)

    def _create_metadata(self):
        x = Ontology(identifier=self.base_IRI, graph=self.g)

        for meta in self.meta_data:

            self.g.add((self.base_IRI, meta[0], meta[1]))

    def _create_connector(self):
        # special connectors
        # first make connectors: intersectionof and unionof, equivalentclass, disjointclass, alldifferent

        connector_G1 = {'equivalentclass': OWL.equivalentClass,
                        'disjointclass': OWL.disjointWith}
        connector_G2 = {'intersectionof': OWL.intersectionOf,
                        'unionof': OWL.unionOf}

        connector_G3 = {'alldifferent': OWL.AllDifferent}

        connector_G2_df = self.combined_df[self.combined_df['BelongsTo'].isin(
            connector_G2.keys())]

        if not connector_G2_df.empty:
            for connector_id, value in connector_G2_df.iterrows():
                connector_type = value['BelongsTo']
                connector_URI = connector_G2[connector_type]
                target_groups = value['specialRelations']

                if len(target_groups) >= 2:
                    # get name
                    target_list = [self.combined_df['name'][x[1]]
                                   for x in target_groups]
                    blank_node = BNode()
                    BooleanClass(blank_node, operator=connector_URI,
                                 members=target_list, graph=self.g)
                    self.combined_df['name'][connector_id] = blank_node
                else:
                    error = {
                        "message": f'Elipse nodes must have at least 2 connections.',
                        "id": connector_id,

                    }
                    self.errors["node_errors"].append(error)

        connector_G3_df = self.combined_df[self.combined_df['BelongsTo'].isin(
            connector_G3.keys())]

        if not connector_G3_df.empty:
            for connector_id, value in connector_G3_df.iterrows():
                connector_type = value['BelongsTo']
                connector_URI = connector_G3[connector_type]
                target_groups = value['specialRelations']
                if len(target_groups) >= 2:
                    # make collections
                    collection_node = BNode()
                    ind_list = Collection(self.g, collection_node)
                    for target_group in target_groups:
                        ind_id = target_group[1]
                        ind_URI = self.combined_df['name'][ind_id]
                        ind_list.append(ind_URI)
                    # make alldifferent node
                    alldifferent_node = BNode()
                    self.g.add((alldifferent_node, RDF.type, OWL.AllDifferent))
                    self.g.add(
                        (alldifferent_node, OWL.distinctMembers, ind_list.uri))

        connector_G1_df = self.combined_df[self.combined_df['BelongsTo'].isin(
            connector_G1.keys())]

        if not connector_G1_df.empty:
            for connector_id, connector_value in connector_G1_df.iterrows():
                connector_type = connector_value['BelongsTo']
                connector_URI = connector_G1[connector_type]
                target_groups = connector_value['specialRelations']
                if len(target_groups) >= 2:
                    # at least have two
                    for target_group in itertools.combinations(target_groups, 2):
                        # (['connector', 'a'], ['connector', 'b'])
                        # all combinations
                        sub_id = target_group[0][1]  # 'a'
                        sub_URI = self.combined_df['name'][sub_id]
                        obj_id = target_group[1][1]  # 'b'
                        obj_URI = self.combined_df['name'][obj_id]

                        self.g.add((sub_URI, connector_URI, obj_URI))
                        self.g.add((obj_URI, connector_URI, sub_URI))
                else:

                    error = {
                        "message": f'Elipse nodes must have at least 2 connections.',
                        "id": connector_id,

                    }
                    self.errors["node_errors"].append(error)

    def _create_property(self):

        property_type_OWL = {
            'objectproperty': OWL.ObjectProperty, 'datatypeproperty': OWL.DatatypeProperty, 'annotationproperty': OWL.AnnotationProperty}

        special_relations_OWL = {'range': RDFS.range, 'domain': RDFS.domain, 'type': RDF.type, 'equivalentproperty': OWL.equivalentProperty,
                                 'disjointproperty': OWL.propertyDisjointWith, 'inverseof': OWL.inverseOf, 'subpropertyof': RDFS.subPropertyOf}
        property_characteristics_OWL = {'F': OWL.FunctionalProperty, 'IF': OWL.InverseFunctionalProperty, 'T': OWL.TransitiveProperty,
                                        'S': OWL.SymmetricProperty, 'AS': OWL.AsymmetricProperty, 'R': OWL.ReflexiveProperty, 'IR': OWL.IrreflexiveProperty}

        property_df = self.combined_df[self.combined_df['BelongsTo'].isin(
            property_type_OWL.keys())]
        if not property_df.empty:
            for _, value in property_df.iterrows():
                property_URI = value['name']
                property_type = value['BelongsTo']

                self.g.add(
                    (property_URI, RDF.type, property_type_OWL[property_type]))

                if len(value['specialRelations']):
                    for predica_name, obj_id in value['specialRelations']:

                        predica_URI = special_relations_OWL[predica_name]

                        obj_URI = self.combined_df['name'][obj_id]
                        self.g.add((property_URI, predica_URI, obj_URI))

                if len(value['characteristics']):
                    for characteristic in value['characteristics']:
                        self.g.add(
                            (property_URI, RDF.type, property_characteristics_OWL[characteristic]))

                if len(value['annotations']):
                    for predica_id, obj_id in value['annotations']:

                        predica_URI = self.combined_df['name'][predica_id]

                        obj_URI = self.combined_df['name'][obj_id]
                        self.g.add((property_URI, predica_URI, obj_URI))

    def _create_class(self):
        special_relations_OWL = {'equivalentclass': OWL.equivalentClass,
                                 'disjointclass': OWL.disjointWith, 'type': RDF.type, 'subclassof': RDFS.subClassOf, 'complementof': OWL.complementOf,
                                 }
        # special_relations_OWL = {'equivalentclass': "equivalentClass",
        #                          'disjointclass': "disjointWith", 'subclassof': "subClassOf", 'complementof': "complementOf",
        #                          }

        class_df = self.combined_df[self.combined_df['BelongsTo'] == 'class']
        if not class_df.empty:
            for _, value in class_df.iterrows():

                class_URI = value['name']

                a = Class(class_URI, graph=self.g)

                if len(value['restrictions']):
                    for res, predica_id, obj_id in value['restrictions']:

                        obj_URI = self.combined_df['name'][obj_id]
                        predica_URI = self.combined_df['name'][predica_id]
                        obj_type = self.combined_df['BelongsTo'][obj_id]

                        if res == 'some':

                            u = Restriction(
                                predica_URI, graph=self.g, someValuesFrom=obj_URI)

                            a.subClassOf = [u]

                        elif res == 'all':
                            u = Restriction(
                                predica_URI, graph=self.g, allValuesFrom=obj_URI)

                            a.subClassOf = [u]

                        elif res == 'hasvalue':
                            u = Restriction(
                                predica_URI, graph=self.g, value=obj_URI)

                            a.subClassOf = [u]

                        else:
                            # cardinality
                            # onClass for objectproperty, onDataRange for datatypeproperty
                            on_what = {'class': OWL.onClass,
                                       'datatype': OWL.onDataRange}

                            card_min, card_max = res.split('..')
                            if card_min != card_max:

                                if card_min != '0':
                                    card_min = int(card_min)
                                    emptyNode = BNode()
                                    self.g.add(
                                        (emptyNode, RDF.type, OWL.Restriction))
                                    self.g.add(
                                        (emptyNode, OWL.onProperty, predica_URI))

                                    self.g.add(
                                        (emptyNode, on_what[obj_type], obj_URI))

                                    self.g.add((emptyNode, OWL.minCardinality, Literal(
                                        card_min, datatype=XSD.int)))

                                    a.subClassOf = [emptyNode]

                                if card_max != 'N' and card_max != "N2":
                                    card_max = int(card_max)
                                    emptyNode = BNode()
                                    self.g.add(
                                        (emptyNode, RDF.type, OWL.Restriction))
                                    self.g.add(
                                        (emptyNode, OWL.onProperty, predica_URI))
                                    self.g.add(
                                        (emptyNode, on_what[obj_type], obj_URI))

                                    self.g.add((emptyNode, OWL.maxCardinality, Literal(
                                        card_max, datatype=XSD.int)))

                                    a.subClassOf = [emptyNode]
                            else:
                                card_max = int(card_max)
                                emptyNode = BNode()
                                self.g.add(
                                    (emptyNode, RDF.type, OWL.Restriction))
                                self.g.add(
                                    (emptyNode, OWL.onProperty, predica_URI))
                                self.g.add(
                                    (emptyNode, on_what[obj_type], obj_URI))

                                self.g.add((emptyNode, OWL.cardinality, Literal(
                                    card_min, datatype=XSD.int)))

                                a.subClassOf = [emptyNode]

                if len(value['specialRelations']):
                    for predica_name, obj_id in value['specialRelations']:

                        predica_URI = special_relations_OWL[predica_name]

                        obj_URI = self.combined_df['name'][obj_id]

                        self.g.add((class_URI, predica_URI, obj_URI))

                if len(value['annotations']):
                    for predica_id, obj_id in value['annotations']:

                        predica_URI = self.combined_df['name'][predica_id]

                        obj_URI = self.combined_df['name'][obj_id]
                        self.g.add((class_URI, predica_URI, obj_URI))

    def _create_individual(self):

        # individual can have two cases, triple op, and triple dp
        ind_df = self.combined_df[self.combined_df['BelongsTo']
                                  == 'individual']

        ind_df_mapping = ind_df[ind_df['hasMapping'].str.len() > 0]
        ind_df_no_mapping = ind_df[ind_df['hasMapping'].str.len() == 0]

        special_relations_OWL = {
            'sameas': OWL.sameAs, 'differentfrom': OWL.differentFrom, 'rdftype': RDF.type}

        if not ind_df_mapping.empty:
            for key, value in ind_df_mapping.iterrows():
                ind_id = key
                ind_URI = value['name']
                has_mapping = value['hasMapping']

                suffix_list = self.mapping_df[has_mapping].to_list()
                for i in range(len(suffix_list)):

                    new_ind_URI = ind_URI + suffix_list[i]

                    if not uri_validator(new_ind_URI):
                        error = {
                            "message": f'"{new_ind_URI}" composed from mapping data is not a valid URI.',
                            "id": ind_id
                        }

                        self.errors["node_errors"].append(error)

                    else:

                        self.g.add(
                            (new_ind_URI, RDF.type, OWL.NamedIndividual))

                        if len(value['specialRelations']):
                            for predica_name, obj_id in value['specialRelations']:

                                predica_URI = special_relations_OWL[predica_name]

                                obj_URI = self.combined_df['name'][obj_id]
                                obj_mapping = self.combined_df['hasMapping'][obj_id]

                                if obj_mapping:
                                    obj_suffix_list = self.mapping_df[obj_mapping].to_list(
                                    )
                                    obj_URI = obj_URI + obj_suffix_list[i]

                                    if not uri_validator(obj_URI):
                                        error = {
                                            "message": f'"{obj_URI}" composed from mapping data is not a valid URI.',
                                            "id": obj_id
                                        }

                                        self.errors["node_errors"].append(
                                            error)
                                        continue

                                self.g.add(
                                    (new_ind_URI, predica_URI, obj_URI))

                        # 'a.type = [self.names_space[obj_pre][obj_name]]'

                        if len(value['triples']):
                            for predica_id, obj_id in value['triples']:
                                obj_URI = self.combined_df['name'][obj_id]
                                predica_URI = self.combined_df['name'][predica_id]
                                obj_mapping = self.combined_df['hasMapping'][obj_id]

                                if obj_mapping:
                                    obj_suffix_list = self.mapping_df[obj_mapping].to_list(
                                    )
                                    if self.combined_df['BelongsTo'][obj_id] == "individual":
                                        obj_URI = obj_URI + obj_suffix_list[i]
                                        if not uri_validator(obj_URI):
                                            error = {
                                                "message": f'"{obj_URI}" composed from mapping data is not a valid URI.',
                                                "id": obj_id
                                            }

                                            self.errors["node_errors"].append(
                                                error)
                                            continue
                                    else:
                                        obj_dt = obj_URI.datatype
                                        obj_lang = obj_URI.language
                                        obj_URI = Literal(
                                            obj_suffix_list[i], datatype=obj_dt, lang=obj_lang)

                                self.g.add((new_ind_URI, predica_URI,
                                            obj_URI))

                        if len(value['annotations']):
                            for predica_id, obj_id in value['annotations']:

                                predica_URI = self.combined_df['name'][predica_id]

                                obj_URI = self.combined_df['name'][obj_id]
                                obj_mapping = self.combined_df['hasMapping'][obj_id]

                                if obj_mapping:
                                    obj_suffix_list = self.mapping_df[obj_mapping].to_list(
                                    )
                                    if self.combined_df['BelongsTo'][obj_id] == "individual":
                                        obj_URI = obj_URI + obj_suffix_list[i]

                                        if not uri_validator(obj_URI):
                                            error = {
                                                "message": f'"{obj_URI}" composed from mapping data is not a valid URI.',
                                                "id": obj_id
                                            }

                                            self.errors["node_errors"].append(
                                                error)
                                            continue
                                    else:
                                        obj_dt = obj_URI.datatype
                                        obj_lang = obj_URI.language
                                        obj_URI = Literal(
                                            obj_suffix_list[i], datatype=obj_dt, lang=obj_lang)

                                self.g.add((new_ind_URI, predica_URI,
                                            obj_URI))

        if not ind_df_no_mapping.empty:
            for _, value in ind_df_no_mapping.iterrows():
                ind_URI = value['name']

                self.g.add((ind_URI, RDF.type, OWL.NamedIndividual))

                if len(value['specialRelations']):
                    for predica_name, obj_id in value['specialRelations']:

                        predica_URI = special_relations_OWL[predica_name]

                        obj_URI = self.combined_df['name'][obj_id]

                        obj_mapping = self.combined_df['hasMapping'][obj_id]

                        if obj_mapping:
                            obj_suffix_list = self.mapping_df[obj_mapping].to_list(
                            )
                            for elem in obj_suffix_list:
                                new_obj_URI = obj_URI + elem
                                if not uri_validator(new_obj_URI):
                                    error = {
                                        "message": f'"{new_obj_URI}" composed from mapping data is not a valid URI.',
                                        "id": obj_id
                                    }

                                    self.errors["node_errors"].append(error)
                                    continue
                                self.g.add(
                                    (ind_URI, predica_URI, new_obj_URI))

                        else:
                            self.g.add((ind_URI, predica_URI, obj_URI))

                    # 'a.type = [self.names_space[obj_pre][obj_name]]'
                if len(value['triples']):
                    for predica_id, obj_id in value['triples']:
                        obj_URI = self.combined_df['name'][obj_id]
                        predica_URI = self.combined_df['name'][predica_id]

                        obj_mapping = self.combined_df['hasMapping'][obj_id]

                        if obj_mapping:
                            obj_suffix_list = self.mapping_df[obj_mapping].to_list(
                            )
                            for elem in obj_suffix_list:
                                if self.combined_df['BelongsTo'][obj_id] == "individual":
                                    new_obj_URI = obj_URI + elem
                                    if not uri_validator(new_obj_URI):
                                        error = {
                                            "message": f'"{new_obj_URI}" composed from mapping data is not a valid URI.',
                                            "id": obj_id
                                        }

                                        self.errors["node_errors"].append(
                                            error)
                                        continue
                                else:
                                    obj_dt = obj_URI.datatype
                                    obj_lang = obj_URI.language
                                    new_obj_URI = Literal(
                                        elem, datatype=obj_dt, lang=obj_lang)

                                self.g.add((ind_URI, predica_URI,
                                            new_obj_URI))
                        else:
                            self.g.add((ind_URI, predica_URI, obj_URI))

                if len(value['annotations']):
                    for predica_id, obj_id in value['annotations']:

                        predica_URI = self.combined_df['name'][predica_id]

                        obj_URI = self.combined_df['name'][obj_id]
                        self.g.add((ind_URI, predica_URI, obj_URI))

                        obj_mapping = self.combined_df['hasMapping'][obj_id]

                        if obj_mapping:
                            obj_suffix_list = self.mapping_df[obj_mapping].to_list(
                            )
                            for elem in obj_suffix_list:
                                if self.combined_df['BelongsTo'][obj_id] == "individual":
                                    new_obj_URI = obj_URI + elem
                                    if not uri_validator(new_obj_URI):
                                        error = {
                                            "message": f'"{new_obj_URI}" composed from mapping data is not a valid URI.',
                                            "id": obj_id
                                        }

                                        self.errors["node_errors"].append(
                                            error)
                                        continue
                                else:
                                    obj_dt = obj_URI.datatype
                                    obj_lang = obj_URI.language
                                    new_obj_URI = Literal(
                                        elem, datatype=obj_dt, lang=obj_lang)

                                self.g.add((ind_URI, predica_URI,
                                            new_obj_URI))

                        else:
                            self.g.add((ind_URI, predica_URI, obj_URI))

    def _create_datatype(self):
        dt_df = self.combined_df[self.combined_df['BelongsTo']
                                 == 'datatype']
        if not dt_df.empty:
            for _, value in dt_df.iterrows():
                dt_URI = value['name']

                self.g.add((dt_URI, RDF.type, RDFS.Datatype))

                if len(value['annotations']):
                    for predica_id, obj_id in value['annotations']:

                        predica_URI = self.combined_df['name'][predica_id]

                        obj_URI = self.combined_df['name'][obj_id]
                        self.g.add((dt_URI, predica_URI, obj_URI))

    def _exe_all(self):
        try:
            self._run_module()

            if self.combined_df.empty:
                error = {
                    "id": "null",
                    "message": 'No ontologies exist in the file. Please use the templates to make ontologies.'}
                self.errors["other_errors"].append(error)
            else:
                self._create_namespace()
                self._create_metadata()
                self._create_connector()
                self._create_property()
                self._create_class()
                self._create_individual()
                self._create_datatype()

        except Exception as e:
            exc_type, exc_value, exc_traceback_obj = sys.exc_info()
            traceback.print_tb(exc_traceback_obj)
            raise APIException(
                'Something goes wrong, please contact yue.chen@bam.de for fix this. thanks.')
