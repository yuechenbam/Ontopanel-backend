import re
import string
from .helpfunc import *
import rdflib


class Finder():

    def __init__(self, edges, vertexes):

        self.edges = edges
        self.vertexes = vertexes
        self.relations = {}
        self.namespaces = {}
        self.ontology_metadata = {}
        self.ellipses = {}
        self.individuals = {}
        self.attributes = {}
        self.concepts = {}
        self.attribute_blocks = {}
        self.rhombuses = {}
        self.hexagons = {}
        self.errors = {
            "Concepts": [],
            "Arrows": [],
            "Ellipses": [],
            "Attributes": [],
            "Namespaces": [],
            "Metadata": [],
            "Rhombuses": [],
            "Hexagons": [],
            "Individual": []
        }

    def find_vertexes(self):
        # find metadata and namespaces

        for vertex_id, vertex_value in self.vertexes:
            vertex_style = vertex_value['style']
            vertex_label = vertex_value['label']
            # Dictionary of Namespaces
            if "shape=note" in vertex_style:
                text = clean_html_tags(vertex_label)
                namespaces = text.split("|")
                namespaces = [
                    item for item in namespaces if item.strip() != ""]
                for ns in namespaces:
                    try:
                        ns = ns.strip()
                        prefix = ns.split(":")[0].strip()
                        ontology_uri = ns.split("http")[-1].strip()
                        ontology_uri = "http" + ontology_uri
                        self.namespaces[prefix] = rdflib.Namespace(
                            ontology_uri)
                    except:
                        error = {
                            "message": "Problems in the text of the Namespace",
                            "shape_id": vertex_id,
                            "label": vertex_label
                        }
                        self.errors["Namespaces"].append(error)
                        continue
            # Dictionary of ontology level metadata
            elif "shape=document" in vertex_style:
                text = clean_html_tags(vertex_label)
                annotations = text.split("|")
                for ann in annotations:
                    try:
                        ann_prefix = ann.split(":")[0].strip()
                        ann_type = ann.split(":")[1].strip()
                        if ann_type == "imports":
                            ann_value = ann.split(":")[2:]
                            ann_value = ":".join(ann_value).strip()
                        else:
                            ann_value = ann.split(":")[2].strip()
                        if ann_prefix + ":" + ann_type in self.ontology_metadata:
                            self.ontology_metadata[ann_prefix +
                                                   ":" + ann_type].append(ann_value)
                        else:
                            self.ontology_metadata[ann_prefix +
                                                   ":" + ann_type] = [ann_value]
                    except:
                        error = {
                            "message": "Problems in the text of the Metadata",
                            "shape_id": vertex_id,
                            "value": vertex_label
                        }
                        self.errors["Metadata"].append(error)
                        continue

            elif "ellipse" in vertex_style:
                ellipse_corrupted = False
                ellipse = {}
                if "⨅" in vertex_label or "owl:intersectionOf" in vertex_label:
                    ellipse["type"] = "owl:intersectionOf"
                elif "⨆" in vertex_label or "owl:unionOf" in vertex_label:
                    ellipse["type"] = "owl:unionOf"
                elif "≡" in vertex_label:
                    ellipse["type"] = "owl:equivalentClass"
                elif "⊥" in vertex_label:
                    ellipse["type"] = "owl:disjointWith"

                # Find the associated concepts to this union / intersection restriction
                ellipse["group"] = []

                for relation_id, relation in self.relations.items():

                    if "type" not in relation:
                        continue

                    if relation["type"] == "ellipse_connection":
                        source_id = relation["source"]
                        if vertex_id == source_id:
                            target_id = relation["target"]
                            if target_id is None:
                                ellipse_corrupted = True
                                break
                            ellipse["group"].append(target_id)

                if len(ellipse["group"]) < 2:
                    ellipse_corrupted = True

                if ellipse_corrupted:
                    continue

                self.ellipses[vertex_id] = ellipse

            # List of individuals
            elif "fontStyle=4" in vertex_style or "<u>" in vertex_label:
                individual = {}

                vertex_label = clean_html_tags(vertex_label)
                try:
                    check = vertex_label.split(":")[1]
                    assert(len(check) == 2)
                    individual["prefix"] = check[0].strip()
                    individual["uri"] = check[1].strip()

                    individual["type"] = None
                    individual["uri"] = re.sub(" ", "", individual["uri"])

                except:
                    error = {
                        "message": "Problems in the text of the Metadata",
                        "shape_id": vertex_id,
                        "label": vertex_label
                    }
                    self.errors["Individual"].append(error)
                    continue

                self.individuals[id] = individual
            elif "text" in vertex_style or "edgeLabel" in vertex_style or "shape" in vertex_style:
                pass
            elif "ellipse" in vertex_style or "rhombus" in vertex_style:
                pass
            elif "&quot;" in vertex_label or "^^" in vertex_label:
                pass
            else:
                concept = {}
                attribute_block = {}
                geo1 = vertex_value['geometry']

                # We need a second iteration because we need to know if there is a block
                # on top of the current block, that determines if we are dealing with a class or attributes
                for vertex2_id, vertex2_value in self.vertexes:
                    vertex2_style = vertex2_value['style']
                    # Filter all the elements except attributes and classes
                    if "text" in vertex2_style or "edgeLabel" in vertex2_style:
                        continue
                    if "ellipse" in vertex2_style or "rhombus" in vertex2_style or "shape" in vertex2_style:
                        continue

                    geo2 = vertex2_value['geometry']
                    stacked = compare_geo(geo1, geo2)

                    if stacked:
                        attributes = []
                        value = clean_html_tags(vertex_label)
                        attribute_list = value.split("|")
                        domain = False if "dashed=1" in vertex_style else vertex2_id
                        for attribute_value in attribute_list:
                            attribute = {}
                            _, attribute_value_cleaned = seperate_string_pattern(
                                attribute_value)
                            try:
                                attribute["prefix"] = attribute_value_cleaned.split(":")[
                                    0].strip()
                                # Check if error in text
                                attribute["prefix"][0]
                                attribute["uri"] = attribute_value_cleaned.split(":")[
                                    1].strip()

                                # Taking into account possible spaces in the uri of the concept
                                attribute["uri"] = re.sub(
                                    " ", "", attribute["uri"])

                                # Check if error in text
                                attribute["prefix"][1]
                            except:
                                error = {
                                    "message": "Problems in the text of the attribute",
                                    "shape_id": vertex_id,
                                    "value": attribute_value_cleaned
                                }
                                self.errors["Attributes"].append(error)
                                continue

                            try:
                                if len(attribute_value.split(":")) > 2:
                                    final_datatype = attribute_value.split(":")[
                                        2].strip()
                                    final_datatype = final_datatype[0].lower(
                                    ) + final_datatype[1:]
                                    attribute["datatype"] = final_datatype
                                else:
                                    attribute["datatype"] = None
                            except:
                                error = {
                                    "message": "Problems in the datatype of the attribute",
                                    "shape_id": id,
                                    "value": attribute_value_cleaned
                                }
                                self.errors["Attributes"].append(error)
                                continue

                            if attribute["datatype"] is None or attribute["datatype"] == "":
                                attribute["range"] = False
                            else:
                                attribute["range"] = True

                            attribute["domain"] = domain

                            # Existential Universal restriction evaluation
                            if "(all)" in attribute_value or "∀" in attribute_value:
                                attribute["allValuesFrom"] = True
                            else:
                                attribute["allValuesFrom"] = False

                            if "(some)" in attribute_value or "∃" in attribute_value:
                                attribute["someValuesFrom"] = True
                            else:
                                attribute["someValuesFrom"] = False

                            attribute["functional"] = True if "(F)" in attribute_value else False

                            # Cardinality restriction evaluation
                            try:
                                max_min_card = re.findall(
                                    "\(([0-9][^)]+)\)", attribute_value)
                                max_min_card = max_min_card[-1] if len(
                                    max_min_card) > 0 else None
                                if max_min_card is None:
                                    attribute["min_cardinality"] = None
                                    attribute["max_cardinality"] = None
                                else:
                                    max_min_card = max_min_card.split("..")
                                    attribute["min_cardinality"] = max_min_card[0]
                                    attribute["max_cardinality"] = max_min_card[1]
                            except:
                                error = {
                                    "message": "Problems in cardinality definition",
                                    "shape_id": id,
                                    "value": attribute_value_cleaned
                                }
                                self.errors["Attributes"].append(error)
                                continue

                            if attribute["min_cardinality"] == "0":
                                attribute["min_cardinality"] = None

                            if attribute["max_cardinality"] == "N":
                                attribute["max_cardinality"] = None

                            if attribute["min_cardinality"] == attribute["max_cardinality"]:
                                attribute["cardinality"] = attribute["min_cardinality"]
                                attribute["min_cardinality"] = None
                                attribute["max_cardinality"] = None
                            else:
                                attribute["cardinality"] = None

                            attributes.append(attribute)
                        attribute_block["attributes"] = attributes
                        attribute_block["concept_associated"] = child2.attrib["id"]
                        self.attribute_blocks[id] = attribute_block
                        attributes_found = True
                        break
                # If after a dense one to all evaluation the object selected cannot be associated
                # to any other object it means that it is a class
                #value = clean_html_tags(value).strip()
                if not attributes_found and value != "":

                    # First we have to verify they are actually concepts

                    # One way is to verify breaks in the text
                    value = clean_html_tags(value).strip()
                    if "|" in value:
                        error = {
                            "message": "Problems in text of the Concept",
                            "shape_id": id,
                            "value": value
                        }
                        self.errors["Concepts"].append(error)

                        continue

                    # Other option is to verify things like functionality, some, all, etc.
                    if "(F)" in value or "(some)" in value or "(all)" in value or "∀" in value or "∃" in value:
                        error = {
                            "message": "Attributes not attached to any concept",
                            "shape_id": id,
                            "value": value
                        }
                        self.errors["Attributes"].append(error)
                        continue

                    # If datatype is mentioned
                    if len(value.split(":")) > 2:
                        error = {
                            "message": "Attributes not attached to any concept",
                            "shape_id": id,
                            "value": value
                        }
                        self.errors["Attributes"].append(error)
                        continue

                    # If cardinality is indicated
                    if len(value.split("..")) > 1:
                        error = {
                            "message": "Attributes not attached to any concept",
                            "shape_id": id,
                            "value": value
                        }
                        self.errors["Attributes"].append(error)
                        continue

                    if "\"" in value:
                        continue

                    value = clean_html_tags(value)
                    try:
                        concept["prefix"] = value.split(":")[0].strip()
                        concept["uri"] = value.split(":")[1].strip()

                        concept["prefix"][0]  # Check if error
                        concept["uri"][1]  # Check if error

                        # Taking into account possible spaces in the uri of the concept
                        concept["uri"] = re.sub(" ", "", concept["uri"])
                    except:
                        error = {
                            "message": "Problems in text of the concept",
                            "shape_id": id,
                            "value": value
                        }
                        self.errors["Concepts"].append(error)
                        continue

                    self.concepts[id] = concept

            except:
                print("here")
                continue
                # the rest are attributes and classes:

    def find_relations(self):

        for edge_id, edge_value in self.edges.items():

            edge_style = edge_value['style']
            edge_label_raw = edge_value['label']
            edge_label = clean_html_tags(edge_label_raw)
            ellipse_connection_detected = False

            relation = {}
            source = edge_value['source']
            target = edge_value['target']

            relation["source"] = source
            relation["target"] = target

            if relation["source"] == 'none' or relation["target"] == 'none':
                error = {
                    "message": f"the relation {edge_label} are not connected to both sides, please check this.",
                    "shape_id": edge_id,
                    "label": edge_label
                }
                self.errors["Arrows"].append(error)

            if edge_label is None or len(edge_label) == 0:

                # This edge is part of a unionOf / intersectionOf construct
                # it is not useful beyond that construction
                if source in self.vertexes:
                    source_vertex = self.vertexes[source]
                    vertex_style = source_vertex['style']

                    if "ellipse" in vertex_style or "hexagon" in vertex_style:

                        relation["type"] = "ellipse_connection"
                        ellipse_connection_detected = True

                    # Sometimes edges have their label not embedded into the edge itself, at least not in the
                    # "label" parameter of the object. We can track their associated label by looking for free text
                    # and evaluating the "parent" parameter which will point to an edge.
                    # vertexes
                    # write in frontend

                    # elif ("text" in vertex_style or "edgeLabel" in vertex_style) and edge_id == vertex_value["parent"]:
                    #     edge_label = clean_html_tags(vertex_label)
                    #     break
                    # else:
                    #     pass

                if ellipse_connection_detected:
                    self.relations[edge_id] = relation
                    continue

                # if not ellipse connection
                # we can say for sure that it is a "subclass" or "type" relationship
                # Check for both sides of the edge, sometimes it can be tricky.

                if "endArrow=block" in edge_style or "startArrow=block" in edge_style:
                    relation["type"] = "rdfs:subClassOf"
                elif "endArrow=open" in edge_style or "startArrow=open" in edge_style:
                    relation["type"] = "rdf:type"
                else:
                    error = {
                        "message": f"Could not recognize type of arrow {edge_label}",
                        "shape_id": edge_id,
                        "label": edge_label
                    }
                    self.errors["Arrows"].append(error)
                self.relations[edge_id] = relation
                continue

            # Detection of special type of edges
            edge_types = ["rdfs:subClassOf", "rdf:type", "owl:equivalentClass", "owl:disjointWith", "owl:complementOf",
                          "rdfs:subPropertyOf", "owl:equivalentProperty", "owl:inverseOf", "rdfs:domain", "rdfs:range", "owl:sameAs", "owl:differentFrom"]

            edge_type_founded = False

            for edge_type in edge_types:
                if edge_type in edge_label:
                    relation["type"] = edge_type
                    self.relations[edge_id] = relation
                    edge_type_founded = True
                    break

            if edge_type_founded:
                continue

            # the rest cases are object property or datatype property
            # Prefix and uri
            # whether it is an object or not

            if edge_value['isObject'] == 'True':
                # use object data
                object_value = edge_value['objectValue']
                for i in object_value.keys():
                    if i == 'IRI':
                        relation['IRI'] = rdflib.URIRef(object_value[i])
                    elif i in ['RDFLabel', 'Type']:
                        relation[i] = object_value[i]
                    else:
                        # rest keywords are ignored
                        pass
            else:
                # if not, then check the name pattern, if pattern is not correct, skip this one.
                try:
                    uri = seperate_string_pattern(edge_label)

                    check = uri.split(":")[1]  # Check if error in text

                    assert(len(check) == 2,
                           f"URI {uri} of {edge_label} should be prefix:name.")

                    prefix = check[0].strip()
                    assert(prefix in self.namespaces,
                           f"Prefix {prefix} is not defined.")

                    name = check[-1].strip()

                    name = re.sub(" ", "", name)
                    relation['IRI'] = self.namespaces[prefix][name]

                except Exception as e:
                    error = {
                        "message": e,
                        "shape_id": edge_id,
                        "label": edge_label
                    }
                    self.errors["Arrows"].append(error)
                    continue

            # Domain Range evaluation
            if "dashed=1" in edge_style:
                if "startArrow=oval" not in edge_style or "startFill=0" in edge_style:
                    relation["domain"] = False
                    relation["range"] = False
                elif "startFill=1" in edge_style:
                    relation["domain"] = source
                    relation["range"] = False

            elif "dashed=1" not in edge_style:
                if "startArrow=oval" not in edge_style or "startFill=1" in edge_style:
                    relation["domain"] = source
                    relation["range"] = target
                elif "startFill=0" in edge_style:
                    relation["domain"] = False
                    relation["range"] = target

            # Existential Universal restriction evaluation
            if "allValuesFrom" in edge_label or "(all)" in edge_label or "∀" in edge_label:
                relation["allValuesFrom"] = True
            else:
                relation["allValuesFrom"] = False

            if "someValuesFrom" in edge_label or "(some)" in edge_label or "∃" in edge_label:
                relation["someValuesFrom"] = True
            else:
                relation["someValuesFrom"] = False

            # Property restriction evaluation
            relation["functional"] = True if "(F)" in edge_label else False
            relation["inverse_functional"] = True if "(IF)" in edge_label else False
            relation["transitive"] = True if "(T)" in edge_label else False
            relation["symmetric"] = True if "(S)" in edge_label else False

            # Cardinality restriction evaluation
            max_min_card = re.match('(.+)\\(([0-9][^)]+)\\)', edge_label)
            if max_min_card:
                try:
                    max_min_card = max_min_card.split("..")
                    assert(len(max_min_card) == 2)
                    relation["min_cardinality"] = max_min_card[0]
                    relation["max_cardinality"] = max_min_card[1]

                except:
                    error = {
                        "message": "Problems in cardinality definition",
                        "shape_id": edge_id,
                        "label": edge_label
                    }
                    self.errors["Arrows"].append(error)
                    continue

                if relation["min_cardinality"] == "0":
                    relation["min_cardinality"] = None

                if relation["max_cardinality"] == "N":
                    relation["max_cardinality"] = None

                if relation["min_cardinality"] == relation["max_cardinality"]:
                    relation["cardinality"] = relation["min_cardinality"]
                    relation["max_cardinality"] = None
                    relation["min_cardinality"] = None
                else:
                    relation["cardinality"] = None
            else:
                relation["min_cardinality"] = None
                relation["max_cardinality"] = None
                relation["cardinality"] = None

            relation["type"] = "owl:ObjectProperty"

            self.relations[edge_id] = relation

    def find_ellipses(self):

        for child in self.root:

            id = child.attrib["id"]
            style = child.attrib["style"] if "style" in child.attrib else ""
            value = child.attrib["value"] if "value" in child.attrib else None
            ellipse_corrupted = False
            try:
                if "ellipse" in style:
                    ellipse = {}
                    ellipse["xml_object"] = child
                    if "⨅" in value or "owl:intersectionOf" in value:
                        ellipse["type"] = "owl:intersectionOf"
                    elif "⨆" in value or "owl:unionOf" in value:
                        ellipse["type"] = "owl:unionOf"
                    elif "≡" in value:
                        ellipse["type"] = "owl:equivalentClass"
                    elif "⊥" in value:
                        ellipse["type"] = "owl:disjointWith"

                    # Find the associated concepts to this union / intersection restriction
                    ellipse["group"] = []

                    for relation_id, relation in self.relations.items():

                        if "type" not in relation:
                            continue

                        if relation["type"] == "ellipse_connection":
                            source_id = relation["source"]
                            if id == source_id:
                                target_id = relation["target"]
                                if target_id is None:
                                    ellipse_corrupted = True
                                    break
                                ellipse["group"].append(target_id)

                    if len(ellipse["group"]) < 2:
                        ellipse_corrupted = True

                    if ellipse_corrupted:
                        continue

                    ellipse["xml_object"] = child
                    self.ellipses[id] = ellipse
            except:
                continue

        return self.ellipses

    def find_attribute_values(self):

        for vertex_id, vertex_value in self.vertexes:
            vertex_label = vertex_value['label']

            if vertex_label == 'none':
                continue

            vertex_label = clean_html_tags(vertex_label)

            if "&quot;" in vertex_label or "\"" in vertex_label:
                attribute = {}
                attribute["type"] = None
                attribute["lang"] = None

                try:
                    # Finding the value
                    if "&quot;" in vertex_label:

                        attribute["label"] = vertex_label.split("&quot;")[1]
                    elif "\"" in vertex_label:
                        reg_exp = '"(.*?)"'
                        attribute["label"] = re.findall(
                            reg_exp, vertex_label)[0]

                    # Finding the type
                    if "^^" in vertex_label:
                        attribute["type"] = vertex_label.split("^^")[-1]

                    elif "@" in vertex_label:
                        attribute["lang"] = vertex_label.split("@")[-1]

                except:
                    error = {
                        "message": "Problems in the text of the literal",
                        "shape_id": vertex_id,
                        "label": vertex_label
                    }
                    self.errors["attribute"].append(error)
                    continue

                self.attributes[vertex_id] = attribute

        return self.attributes

    def find_rhombuses(self):

        for vertex_id, vertex_value in self.vertexes:
            vertex_style = vertex_value['style']
            vertex_label = vertex_value['label']
            value_html_clean = clean_html_tags(vertex_label)

            if "rhombus" in vertex_style:

                rhombus = {}

                try:
                    property_type, text = seperate_string_pattern(
                        value_html_clean)

                    rhombus["type"] = property_type

                    check = text.split(':')[1]
                    assert(len(check) == 2)

                    prefix = check[0].strip()
                    uri = check[1].strip()

                    uri = re.sub(" ", "", uri)

                    rhombus["prefix"] = prefix
                    rhombus["uri"] = uri

                    self.rhombuses[vertex_id] = rhombus

                except:
                    error = {
                        "shape_id": vertex_id,
                        "label": value_html_clean
                    }
                    self.errors["Rhombuses"].append(error)
                    continue

                if property_type == "owl:ObjectProperty":

                    relation_uris = []

                    for relation_id, relation in self.relations.items():
                        if "uri" in relation:
                            relation_uris.append(relation["uri"])

                    if uri not in relation_uris:

                        uri = re.sub(" ", "", uri)

                        relation = {}
                        relation["source"] = None
                        relation["target"] = None
                        relation["type"] = type
                        relation["prefix"] = prefix
                        relation["uri"] = uri
                        relation["domain"] = False
                        relation["range"] = False
                        relation["allValuesFrom"] = False
                        relation["someValuesFrom"] = False
                        relation["functional"] = False
                        relation["inverse_functional"] = False
                        relation["transitive"] = False
                        relation["symmetric"] = False

                    self.relations[vertex_id] = relation

                elif property_type == "owl:DatatypeProperty":

                    attribute_uris = []

                    for attribute_block_id, attribute_block in self.attribute_blocks.items():
                        attributes = attribute_block["attributes"]
                        for attribute in attributes:
                            attribute_uris.append(attribute["uri"])

                    if uri not in attribute_uris:
                        attribute = {}
                        attribute_block = {}
                        attribute["prefix"] = prefix
                        attribute["uri"] = uri
                        attribute["datatype"] = None
                        attribute["functional"] = False
                        attribute["domain"] = False
                        attribute["range"] = False
                        attribute["allValuesFrom"] = False
                        attribute["someValuesFrom"] = False
                        attribute["min_cardinality"] = None
                        attribute["max_cardinality"] = None
                        attribute_block["attributes"] = [attribute]

                    self.attribute_blocks[vertex_id] = attribute_block

        return self.rhombuses, self.errors

    def find_hexagons(self):

        for vertex_id, vertex_value in self.vertexes:
            vertex_style = vertex_value['style']
            vertex_label = vertex_value['label']

            ellipse_corrupted = False
            try:
                if "hexagon" in vertex_style:
                    hexagon = {}
                    if "owl:AllDifferent" in vertex_label:
                        hexagon["type"] = "owl:AllDifferent"
                    elif "owl:oneOf" in vertex_label:
                        hexagon["type"] = "owl:oneOf"

                    # Find the associated concepts to this union / intersection restriction
                    hexagon["group"] = []

                    for relation_id, relation in self.relations.items():

                        if "type" not in relation:
                            continue
                        if relation["type"] == "ellipse_connection":
                            source_id = relation["source"]
                            if id == source_id:
                                target_id = relation["target"]
                                if target_id is None:
                                    ellipse_corrupted = True
                                    break
                                hexagon["group"].append(target_id)

                    if len(hexagon["group"]) < 2:
                        ellipse_corrupted = True

                    if ellipse_corrupted:
                        continue

                    self.hexagons[vertex_id] = hexagon
            except:
                continue

        return self.hexagons

    def find_concepts_and_attributes(self):

        for vertex_id, vertex_value in self.vertexes:
            vertex_style = vertex_value['style']
            vertex_label = vertex_value['label']
            attributes_found = False

            try:
                # Check that neither of these components passes, this is because concepts
                # and attributes shape do not have a specific characteristic to differentiate them
                # and we have to use the characteristics of the rest of the shapes
                if "text" in vertex_style or "edgeLabel" in vertex_style:
                    continue
                if "ellipse" in vertex_style:
                    continue
                if "rhombus" in vertex_style:
                    continue
                if "shape" in vertex_style:
                    continue
                if "fontStyle=4" in vertex_style or "<u>" in vertex_label:
                    continue
                if "&quot;" in vertex_label or "^^" in vertex_label:
                    continue
                concept = {}
                attribute_block = {}
                geo1 = vertex_value['geometry']

                p1, p2, p3, p4 = get_corners_rect_child(child)

                # We need a second iteration because we need to know if there is a block
                # on top of the current block, that determines if we are dealing with a class or attributes
                for vertex2_id, vertex2_value in self.vertexes:
                    vertex2_style = vertex2_value['style']
                    # Filter all the elements except attributes and classes
                    if "text" in vertex2_style or "edgeLabel" in vertex2_style:
                        continue
                        continue
                    if "ellipse" in vertex2_style:
                        continue
                    if "rhombus" in vertex2_style:
                        continue
                    if "shape" in vertex2_style:
                        continue

                    geo2 = vertex2_value['geometry']
                    stacked = compare_geo(geo1, geo2)

                    if stacked:
                        attributes = []
                        value = clean_html_tags(vertex_label)
                        attribute_list = value.split("|")
                        domain = False if "dashed=1" in vertex_style else vertex2_id
                        for attribute_value in attribute_list:
                            attribute = {}
                            attribute_value_cleaned = clean_uri(
                                attribute_value)
                            try:
                                attribute["prefix"] = attribute_value_cleaned.split(":")[
                                    0].strip()
                                # Check if error in text
                                attribute["prefix"][0]
                                attribute["uri"] = attribute_value_cleaned.split(":")[
                                    1].strip()

                                # Taking into account possible spaces in the uri of the concept
                                attribute["uri"] = re.sub(
                                    " ", "", attribute["uri"])

                                # Check if error in text
                                attribute["prefix"][1]
                            except:
                                error = {
                                    "message": "Problems in the text of the attribute",
                                    "shape_id": id,
                                    "value": attribute_value_cleaned
                                }
                                self.errors["Attributes"].append(error)
                                continue

                            try:
                                if len(attribute_value.split(":")) > 2:
                                    final_datatype = attribute_value.split(":")[
                                        2].strip()
                                    final_datatype = final_datatype[0].lower(
                                    ) + final_datatype[1:]
                                    attribute["datatype"] = final_datatype
                                else:
                                    attribute["datatype"] = None
                            except:
                                error = {
                                    "message": "Problems in the datatype of the attribute",
                                    "shape_id": id,
                                    "value": attribute_value_cleaned
                                }
                                self.errors["Attributes"].append(error)
                                continue

                            if attribute["datatype"] is None or attribute["datatype"] == "":
                                attribute["range"] = False
                            else:
                                attribute["range"] = True

                            attribute["domain"] = domain

                            # Existential Universal restriction evaluation
                            if "(all)" in attribute_value or "∀" in attribute_value:
                                attribute["allValuesFrom"] = True
                            else:
                                attribute["allValuesFrom"] = False

                            if "(some)" in attribute_value or "∃" in attribute_value:
                                attribute["someValuesFrom"] = True
                            else:
                                attribute["someValuesFrom"] = False

                            attribute["functional"] = True if "(F)" in attribute_value else False

                            # Cardinality restriction evaluation
                            try:
                                max_min_card = re.findall(
                                    "\(([0-9][^)]+)\)", attribute_value)
                                max_min_card = max_min_card[-1] if len(
                                    max_min_card) > 0 else None
                                if max_min_card is None:
                                    attribute["min_cardinality"] = None
                                    attribute["max_cardinality"] = None
                                else:
                                    max_min_card = max_min_card.split("..")
                                    attribute["min_cardinality"] = max_min_card[0]
                                    attribute["max_cardinality"] = max_min_card[1]
                            except:
                                error = {
                                    "message": "Problems in cardinality definition",
                                    "shape_id": id,
                                    "value": attribute_value_cleaned
                                }
                                self.errors["Attributes"].append(error)
                                continue

                            if attribute["min_cardinality"] == "0":
                                attribute["min_cardinality"] = None

                            if attribute["max_cardinality"] == "N":
                                attribute["max_cardinality"] = None

                            if attribute["min_cardinality"] == attribute["max_cardinality"]:
                                attribute["cardinality"] = attribute["min_cardinality"]
                                attribute["min_cardinality"] = None
                                attribute["max_cardinality"] = None
                            else:
                                attribute["cardinality"] = None

                            attributes.append(attribute)
                        attribute_block["attributes"] = attributes
                        attribute_block["concept_associated"] = child2.attrib["id"]
                        self.attribute_blocks[id] = attribute_block
                        attributes_found = True
                        break
                # If after a dense one to all evaluation the object selected cannot be associated
                # to any other object it means that it is a class
                #value = clean_html_tags(value).strip()
                if not attributes_found and value != "":

                    # First we have to verify they are actually concepts

                    # One way is to verify breaks in the text
                    value = clean_html_tags(value).strip()
                    if "|" in value:
                        error = {
                            "message": "Problems in text of the Concept",
                            "shape_id": id,
                            "value": value
                        }
                        self.errors["Concepts"].append(error)

                        continue

                    # Other option is to verify things like functionality, some, all, etc.
                    if "(F)" in value or "(some)" in value or "(all)" in value or "∀" in value or "∃" in value:
                        error = {
                            "message": "Attributes not attached to any concept",
                            "shape_id": id,
                            "value": value
                        }
                        self.errors["Attributes"].append(error)
                        continue

                    # If datatype is mentioned
                    if len(value.split(":")) > 2:
                        error = {
                            "message": "Attributes not attached to any concept",
                            "shape_id": id,
                            "value": value
                        }
                        self.errors["Attributes"].append(error)
                        continue

                    # If cardinality is indicated
                    if len(value.split("..")) > 1:
                        error = {
                            "message": "Attributes not attached to any concept",
                            "shape_id": id,
                            "value": value
                        }
                        self.errors["Attributes"].append(error)
                        continue

                    if "\"" in value:
                        continue

                    value = clean_html_tags(value)
                    try:
                        concept["prefix"] = value.split(":")[0].strip()
                        concept["uri"] = value.split(":")[1].strip()

                        concept["prefix"][0]  # Check if error
                        concept["uri"][1]  # Check if error

                        # Taking into account possible spaces in the uri of the concept
                        concept["uri"] = re.sub(" ", "", concept["uri"])
                    except:
                        error = {
                            "message": "Problems in text of the concept",
                            "shape_id": id,
                            "value": value
                        }
                        self.errors["Concepts"].append(error)
                        continue

                    self.concepts[id] = concept

            except:
                print("here")
                continue

        return self.concepts, self.attribute_blocks

    def find_elements(self):

        namespaces = self.find_namespaces()
        metadata = self.find_metadata()
        relations = self.find_relations()
        ellipses = self.find_ellipses()
        hexagons = self.find_hexagons()
        individuals = self.find_individuals()
        concepts, attribute_blocks = self.find_concepts_and_attributes()
        rhombuses, errors = self.find_rhombuses()

        return concepts, attribute_blocks, relations, individuals, ellipses, hexagons, metadata, namespaces, rhombuses, errors
