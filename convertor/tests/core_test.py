import json
from rest_framework.test import APITestCase
import os
from rdflib import Literal, XSD, DCTERMS, DC, URIRef, RDFS, RDF, OWL
from rdflib import Namespace, Graph, BNode
from rdflib.extras.infixowl import Class, Restriction, Ontology, BooleanClass
from convertor.utilies.conversion.graph_to_rdf import MakeOntology
import owlready2
dir_path = os.path.dirname(os.path.realpath(__file__))


class TestGraphToRDF(APITestCase):
    def get_owl(self, filename):
        filepath = os.path.join(dir_path, 'files_test', filename)
        with open(filepath, encoding='utf-8') as f:
            data = json.load(f)

            onto = MakeOntology(data)
            g = onto.g
            result = g.serialize()
            return result

    def test_class_normal(self):
        # class
        filename = 'class_normal.json'
        owl_result = self.get_owl(filename)
        save_path = os.path.join(dir_path, 'files_test', filename + '.owl')

        with open(save_path,  "w") as f:
            f.write(owl_result.decode('utf-8'))

        onto = owlready2.get_ontology(
            save_path)
        onto.load()
        ns = owlready2.get_namespace(
            "http://test.namespace.com/")

        assert onto.unknownShape == None

        # complement of not tested here

        assert set(ns.OrangeApple.equivalent_to) == set(
            [ns.Apple1 & ns.Orange1, ns.Apple2 & ns.Orange2])
        assert set(ns.sweetFruit.equivalent_to) == set(
            [ns.Apple1 | ns.Orange1, ns.Apple2 | ns.Orange2])
        assert ns.Orange1.equivalent_to == [ns.Orange2]
        assert ns.Apple1.equivalent_to == [ns.Apple2]
        assert ns.Apple1.equivalent_to == [ns.Apple2]
        assert ([ns.Apple1, ns.NonApple1] in [
            x.entities for x in ns.Apple1.disjoints()]) == True
        assert ([ns.Apple2, ns.NonApple2] in [
            x.entities for x in ns.Apple2.disjoints()]) == True
        assert owlready2.issubclass(ns.Apple1, ns.Fruit) == True
        assert owlready2.issubclass(ns.Orange1, ns.Fruit) == True

        # restriction
        assert ns.hasBrand.value(ns.pinkLady) in ns.Apple1.is_a
        assert ns.hasShape.only(ns.Round) in ns.Apple1.is_a
        assert ns.hasShape.only(ns.Round) in ns.Apple2.is_a
        assert ns.hasShape.only(ns.Round) in ns.Apple3.is_a
        assert ns.hasColor.some(ns.Red) in ns.Apple1.is_a
        assert ns.objectProperty.some(ns.Red) in ns.Apple2.is_a
        assert ns.objectProperty.some(ns.Red) in ns.Apple3.is_a
        assert ns.hasType.min(1, ns.Type) in ns.Apple1.is_a
        assert ns.hasType.max(20, ns.Type) in ns.Apple1.is_a
        assert ns.hasType.max(20, ns.Type) in ns.Apple2.is_a

        assert ns.hasType.min(1, ns.Type) in ns.Apple3.is_a

    def test_class_IRI(self):
        # class
        filename = 'class_IRI.json'
        owl_result = self.get_owl(filename)
        save_path = os.path.join(dir_path, 'files_test', filename + '.owl')

        with open(save_path,  "w") as f:
            f.write(owl_result.decode('utf-8'))

        onto = owlready2.get_ontology(
            save_path)
        onto.load()
        cco = owlready2.get_namespace(
            "http://www.ontologyrepository.com/CommonCoreOntologies/")
        obo = owlready2.get_namespace("http://purl.obolibrary.org/obo/")

        assert onto.unknownShape == None

        # complement of not tested here

        assert owlready2.issubclass(cco.Park, cco.Agent) == True

        # restriction
        assert cco.caused_by.value(cco.CFAFranc) in cco.Iris.is_a
        assert cco.has_subsidiary.only(cco.SetOfEyes) in cco.Tattoo.is_a
        assert cco.delimits.only(cco.ReactionMass) in cco.Payload.is_a
        assert cco.disconnected_with.only(obo.BFO_0000024) in cco.Target.is_a
        assert cco.disconnected_with.some(cco.Engine) in cco.Decoy.is_a
        assert cco.has_maternal_aunt.some(
            cco.ElectricMotor) in cco.Artifact.is_a
        assert cco.has_uncle.some(cco.GasTurbine) in cco.StirlingEngine.is_a
        assert cco.is_child_of.min(
            1, cco.RamjetEngine) in cco.ReactionEngine.is_a
        assert cco.is_child_of.max(
            20, cco.RamjetEngine) in cco.ReactionEngine.is_a
        assert cco.has_maternal_aunt.max(
            20, cco.Facility) in cco.CoolingSystem.is_a
        assert cco.has_affiliate.min(
            1, cco.EducationalFacility) in cco.Farm.is_a

    def test_property_normal(self):
        # test datatypeproperty and objectproperty
        filename = 'property_normal.json'
        owl_result = self.get_owl(filename)
        save_path = os.path.join(dir_path, 'files_test', filename + '.owl')

        with open(save_path,  "w") as f:
            f.write(owl_result.decode('utf-8'))

        onto = owlready2.get_ontology(
            save_path)
        onto.load()
        ns = owlready2.get_namespace(
            "http://test.namespace.com/")

        assert onto.unknownShape == None
        # objectproperty

        assert ns.hasWeather in ns.isWarm.is_a  # subproperty
        assert ns.hasUnit1.domain == []
        assert ns.hasUnit1.range == []
        assert ns.hasUnit2.domain == []
        assert ns.hasUnit2.range == []
        assert ns.hasUnit3.domain == [ns.Data]
        assert ns.hasUnit3.range == [ns.Unit]
        assert ns.hasUnit4.domain == [ns.Data]
        assert ns.hasUnit4.range == [ns.Unit]
        assert ns.hasUnit5.domain == []
        assert ns.hasUnit5.range == [ns.Unit]
        assert ns.hasUnit6.domain == [ns.Data]
        assert ns.hasUnit6.range == []

        assert owlready2.owl.ObjectProperty in ns.isWarm.is_a
        assert owlready2.owl.SymmetricProperty in ns.isWarm.is_a
        assert owlready2.owl.InverseFunctionalProperty in ns.isWarm.is_a
        assert owlready2.owl.TransitiveProperty in ns.isWarm.is_a
        assert owlready2.owl.IrreflexiveProperty in ns.isWarm.is_a
        assert owlready2.owl.AsymmetricProperty in ns.isWarm.is_a
        assert owlready2.owl.FunctionalProperty in ns.isWarm.is_a
        assert owlready2.owl.ReflexiveProperty in ns.isWarm.is_a

        # inverse not test here

        # print(ns.isWarm)
        # print(owlready2.Inverse(ns.isWarm))
        # print(ns.isWarm.inverse)
        # assert ns.isWarm.inverse == [ns.isCold]
        assert ns.isWarm.equivalent_to == [ns.notCold]
        assert ([ns.isWarm, ns.isNotWarm] in [
            x.entities for x in ns.isWarm.disjoints()]) == True

        assert ns.hasData.domain == [ns.Measurement]
        assert ns.hasData.range == [ns.Data]

        # datataypeproperty

        # owl.really is float in owlready2
        assert ns.hasValue1.only(float) in ns.Result1.is_a
        assert ns.hasValue2.only(float) in ns.Result2.is_a
        assert ns.hasValue3.some(float) in ns.Result3.is_a
        assert ns.hasValue4.some(float) in ns.Result4.is_a
        assert ns.hasValue5.min(1, float) in ns.Result5.is_a
        assert ns.hasValue5.max(5, float) in ns.Result5.is_a
        assert ns.hasValue5_1.max(5, float) in ns.Result5_1.is_a
        assert ns.hasValue5_2.min(1, float) in ns.Result5_2.is_a

        assert ns.hasValue6.domain == [ns.Result6]
        assert ns.hasValue6.range == [float]
        assert ns.hasValue7.domain == [ns.Result7]
        assert ns.hasValue7.range == []
        assert ns.hasValue8.domain == []
        assert ns.hasValue8.range == [float]
        assert ns.hasValue9.domain == []
        assert ns.hasValue9.range == []
        assert ns.hasNumber.domain == [ns.Result]
        assert ns.hasNumber.range == [float]

        assert owlready2.owl.DatatypeProperty in ns.hasNumber.is_a
        assert owlready2.owl.FunctionalProperty in ns.hasNumber.is_a
        assert ns.hasValue in ns.hasNumber.is_a  # subproperty
        assert ns.hasNumber.equivalent_to == [ns.hasInt]
        assert ([ns.hasNumber, ns.hasString] in [
            x.entities for x in ns.hasNumber.disjoints()]) == True

    def test_ind_IRI(self):
        # test rest: indivdual, annotationproperty, datatype, and the others that are not tested in owlready2
        # use rdflib here
        filename = 'ind_IRI.json'
        owl_result = self.get_owl(filename)
        save_path = os.path.join(dir_path, 'files_test', filename + '.owl')

        with open(save_path,  "w") as f:
            f.write(owl_result.decode('utf-8'))

        g = Graph()
        g.parse(data=owl_result)

        cco = Namespace(
            "http://www.ontologyrepository.com/CommonCoreOntologies/")

        # individual and datatype

        assert set(list(g.objects(subject=cco.AlbaniaLek,
                                  predicate=RDF.type))) == {cco.Resource, OWL.NamedIndividual}
        assert set(list(g.objects(subject=cco.ArmenianDram,
                                  predicate=RDF.type))) == {cco.Agent, OWL.NamedIndividual}
        assert set(list(g.objects(subject=cco.AzerbaijanManat,
                                  predicate=RDF.type))) == {cco.Target, OWL.NamedIndividual}

        assert list(g.objects(subject=cco.BelarussianRuble,
                    predicate=cco.delimits)) == [cco.BoliviaBoliviano]
        assert list(g.objects(subject=cco.BruneiDollar, predicate=cco.has_date_value)) == [Literal(
            'IRI', datatype=XSD.long)]

        assert list(g.objects(subject=cco.BruneiDollar, predicate=cco.SI_unit_label)) == [Literal(
            'annotation1', lang="en")]

        assert cco.has_affiliate in list(
            g.objects(subject=cco.has_subsidiary, predicate=RDFS.subPropertyOf))

    def test_property_IRI(self):
        # test datatypeproperty and objectproperty
        filename = 'property_IRI.json'
        owl_result = self.get_owl(filename)
        save_path = os.path.join(dir_path, 'files_test', filename + '.owl')

        with open(save_path,  "w") as f:
            f.write(owl_result.decode('utf-8'))

        onto = owlready2.get_ontology(
            save_path)
        onto.load()
        cco = owlready2.get_namespace(
            "http://www.ontologyrepository.com/CommonCoreOntologies/")
        obo = owlready2.get_namespace("http://purl.obolibrary.org/obo/")
        pt = owlready2.get_namespace(
            "http://www.daml.org/2003/01/periodictable/PeriodicTable#")
        mid = owlready2.get_namespace("https://purl.matolab.org/mseo/mid/")

        assert onto.unknownShape == None
        # objectproperty

        assert cco.caused_by.domain == []
        assert cco.caused_by.range == []
        assert cco.condition_described_by.domain == []
        assert cco.condition_described_by.range == []
        assert cco.has_input.domain == [cco.CarrierAirWing]
        assert cco.has_input.range == [cco.ParamilitaryForce]
        assert cco.has_object.domain == [cco.Government]
        assert cco.has_object.range == [cco.GovernmentAgency]
        assert cco.has_recipient.domain == []
        assert cco.has_recipient.range == [cco.Artifact]
        assert obo.RO_0001015.domain == [cco.CombustionChamber]
        assert obo.RO_0001015.range == []

        assert owlready2.owl.ObjectProperty in obo.RO_0010001.is_a
        assert owlready2.owl.SymmetricProperty in obo.RO_0010001.is_a
        assert owlready2.owl.InverseFunctionalProperty in obo.RO_0010001.is_a
        assert owlready2.owl.TransitiveProperty in obo.RO_0010001.is_a
        assert owlready2.owl.IrreflexiveProperty in obo.RO_0010001.is_a
        assert owlready2.owl.AsymmetricProperty in obo.RO_0010001.is_a
        assert owlready2.owl.FunctionalProperty in obo.RO_0010001.is_a
        assert owlready2.owl.ReflexiveProperty in obo.RO_0010001.is_a

        assert obo.RO_0010001.domain == [cco.RadioReceiver]
        assert obo.RO_0010001.range == [cco.WireReceiver]

        assert owlready2.owl.ObjectProperty in cco.has_maternal_uncle.is_a
        assert owlready2.owl.SymmetricProperty in cco.has_maternal_uncle.is_a
        assert owlready2.owl.InverseFunctionalProperty in cco.has_maternal_uncle.is_a
        assert owlready2.owl.TransitiveProperty in cco.has_maternal_uncle.is_a
        assert owlready2.owl.IrreflexiveProperty in cco.has_maternal_uncle.is_a
        assert owlready2.owl.AsymmetricProperty in cco.has_maternal_uncle.is_a
        assert owlready2.owl.FunctionalProperty in cco.has_maternal_uncle.is_a
        assert owlready2.owl.ReflexiveProperty in cco.has_maternal_uncle.is_a

        # inverse not test here

        # assert cco.has_affiliate in cco.has_subsidiary.is_a

        assert cco.is_grandmother_of.equivalent_to == [
            cco.is_paternal_grandmother_of]
        assert ([cco.has_son_in_law, cco.has_sister_in_law] in [
            x.entities for x in cco.has_son_in_law.disjoints()]) == True

        assert cco.is_nephew_of.domain == [cco.Farm]
        assert cco.is_nephew_of.range == [cco.Stage]

        # datataypeproperty

        # owl.really is float in owlready2
        assert cco.has_date_value.only(float) in obo.BFO_0000001.is_a
        assert cco.has_longitude_value.only(float) in obo.BFO_0000001.is_a
        assert cco.has_latitude_value.some(float) in obo.BFO_0000001.is_a
        assert cco.has_integer_value.some(float) in obo.BFO_0000001.is_a
        assert pt.casRegistryID.min(1, float) in obo.BFO_0000001.is_a
        assert pt.casRegistryID.max(5, float) in obo.BFO_0000001.is_a
        assert cco.has_boolean_value.max(5, float) in obo.BFO_0000001.is_a
        assert pt.symbol.min(1, float) in obo.BFO_0000001.is_a

        assert cco.has_double_value.domain == [obo.BFO_0000001]
        assert cco.has_double_value.range == [float]
        assert cco.has_text_value.domain == [obo.BFO_0000001]
        assert cco.has_text_value.range == []
        assert pt.symbol.domain == []
        assert pt.symbol.range == [float]

        assert pt.color.domain == []
        assert pt.color.range == []
        assert cco.has_URI_value.domain == [obo.BFO_0000040]
        assert cco.has_URI_value.range == [float]

        assert owlready2.owl.DatatypeProperty in mid.has_column_index.is_a
        assert owlready2.owl.FunctionalProperty in mid.has_column_index.is_a
        assert cco.has_latitude_value in pt.atomicNumber.is_a  # subproperty
        assert pt.atomicWeight.equivalent_to == [cco.has_latitude_value]
        assert ([pt.symbol, pt.number] in [
            x.entities for x in pt.symbol.disjoints()]) == True

        assert owlready2.owl.AnnotationProperty in cco.content_license.is_a
        assert cco.definition_source in cco.designator_annotation.is_a

    def test_ind_normal(self):
        # test rest: indivdual, and the others that are not tested in owlready2
        # use rdflib here
        filename = 'ind_normal.json'
        owl_result = self.get_owl(filename)
        save_path = os.path.join(dir_path, 'files_test', filename + '.owl')

        with open(save_path,  "w") as f:
            f.write(owl_result.decode('utf-8'))

        g = Graph()
        g.parse(data=owl_result)
        ns = Namespace("http://test.namespace.com/")

        # individual and datatype

        assert set(list(g.objects(subject=ns.pinkLady1,
                                  predicate=RDF.type))) == {ns.Apple1, OWL.NamedIndividual}
        assert set(list(g.objects(subject=ns.pinkLady2,
                                  predicate=RDF.type))) == {ns.Apple2, OWL.NamedIndividual}
        assert set(list(g.objects(subject=ns.pinkLady3,
                                  predicate=RDF.type))) == {ns.Apple3, OWL.NamedIndividual}

        assert list(g.objects(subject=ns.pinkLady,
                    predicate=OWL.differentFrom)) == [ns.Fuji]
        assert list(g.objects(subject=ns.Fuji, predicate=OWL.sameAs)) == [
            ns.japanApple]
        assert list(g.objects(subject=ns.pinkLady1,
                    predicate=ns.hasTaste)) == [ns.sweet]
        assert list(g.objects(subject=ns.sweet, predicate=ns.hasGrade)) == [Literal(
            'grade1', datatype=ns.grade)]

        assert list(g.objects(subject=ns.sweet, predicate=ns.label)) == [Literal(
            'annotation1', lang="en")]

        assert list(g.objects(subject=ns.hasGrade, predicate=RDF.type)) == [
            OWL.DatatypeProperty]
        assert list(g.objects(subject=ns.hasTaste, predicate=RDF.type)) == [
            OWL.ObjectProperty]
        assert list(g.objects(subject=ns.label, predicate=RDF.type)) == [
            OWL.AnnotationProperty]

        assert list(g.objects(subject=ns.grade, predicate=RDF.type)) == [
            RDFS.Datatype]
        assert list(g.objects(subject=ns.datatype1, predicate=RDF.type)) == [
            RDFS.Datatype]
        assert list(g.objects(subject=ns.datatype2, predicate=RDF.type)) == [
            RDFS.Datatype]
        assert list(g.objects(subject=ns.datatype3, predicate=RDF.type)) == [
            RDFS.Datatype]

        # annotationproperty
        assert list(g.objects(subject=ns.comment, predicate=RDF.type)) == [
            OWL.AnnotationProperty]
        assert list(g.objects(subject=ns.comment, predicate=ns.hasAnno)) == [
            Literal('annotation2')]

        assert list(g.objects(subject=ns.subcomment, predicate=RDFS.subPropertyOf)) == [
            ns.comment]

        # rest
        assert list(g.objects(subject=ns.NonApple1, predicate=OWL.complementOf)) == [
            ns.Fruit]
        assert list(g.objects(subject=ns.NonApple1, predicate=ns.hasMark)) == [
            Literal('grade1', datatype=ns.literal)]
        assert list(g.objects(subject=ns.literal, predicate=RDF.type)) == [
            RDFS.Datatype]
        assert list(g.objects(subject=ns.hasMark, predicate=RDF.type)) == [
            OWL.AnnotationProperty]

        assert list(g.objects(subject=ns.isWarm, predicate=RDF.type)) == [
            OWL.ObjectProperty]

        assert list(g.objects(subject=ns.isWarm, predicate=OWL.inverseOf)) == [
            ns.isCold]
        assert list(g.objects(subject=ns.isWarm, predicate=ns.hasMark)) == [
            Literal('grade1', lang="de")]
        assert OWL.DatatypeProperty in list(
            g.objects(subject=ns.hasNumber, predicate=RDF.type))

        assert list(g.objects(subject=ns.hasNumber, predicate=ns.hasMark)) == [
            Literal('number1')]

        # metadata
        assert set([o for _, _, o in g.triples((None, DC.creator, None))]) == set(
            [Literal('yue')])
        assert set([o for _, _, o in g.triples((None, OWL.versionInfo, None))]) == set(
            [Literal('0.0.1')])
        assert set([o for _, _, o in g.triples((None, DC.title, None))]) == set(
            [Literal('test')])

    def test_mapping_1(self):
        filename = 'mapping_1.json'
        owl_result = self.get_owl(filename)
        save_path = os.path.join(dir_path, 'files_test', filename + '.owl')

        with open(save_path,  "w") as f:
            f.write(owl_result.decode('utf-8'))

        g = Graph()
        g.parse(data=owl_result)
        ns = Namespace("http://FirstIsBaseIRI.com/")

        assert set(g.objects(subject=ns.single, predicate=OWL.sameAs)) == {
            ns["mapping3_HP-160-10m"], ns["mapping3_HP-160-1"]}

        assert list(g.objects(subject=ns["mapping3_HP-160-10m"], predicate=ns.datatypeProperty)) == [
            Literal("value", datatype=ns.Literal)]

        for i in range(1, 6):
            assert list(g.objects(subject=ns[f"mapping_t-{i}"], predicate=ns.datatypeProperty)) == [
                Literal("160", datatype=ns.Literal)]
            assert list(g.objects(subject=ns[f"mapping_t-{i}"], predicate=ns.objectProperty)) == [
                ns['mapping2_HP-160-10m']]

            assert list(g.objects(subject=ns[f"mapping_t-{i}"], predicate=ns.annotationProperty)) == [
                Literal("annotation", lang="de")]

        for i in range(6, 11):
            assert list(g.objects(subject=ns[f"mapping_t-{i}"], predicate=ns.datatypeProperty)) == [
                Literal("160", datatype=ns.Literal)]
            assert list(g.objects(subject=ns[f"mapping_t-{i}"], predicate=ns.objectProperty)) == [
                ns['mapping2_HP-160-1']]
            assert list(g.objects(subject=ns[f"mapping_t-{i}"], predicate=ns.annotationProperty)) == [
                Literal("annotation", lang="de")]

        for i in range(1, 11):
            assert ns.Class1 in list(
                g.objects(subject=ns[f"mapping4_t-{i}"], predicate=RDF.type))
            assert list(g.objects(subject=ns[f"mapping4_t-{i}"], predicate=ns.annotationProperty)) == [
                Literal("160", datatype=ns.Literal)]
