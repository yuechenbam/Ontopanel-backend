from rdflib.extras.infixowl import AnnotatableTerms, TermDeletionHelper, CastClass, BooleanClass, OWLRDFListProxy
from rdflib import RDF, RDFS, OWL, URIRef, Variable, BNode
from rdflib.collection import Collection
from rdflib.util import first
import itertools

# rewrite the function machesterSyntax and Class in rdflib


nsBinds = {
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "rdf": RDF,
    "rdfs": RDFS,
    "owl": OWL,
    "list": URIRef("http://www.w3.org/2000/10/swap/list#"),
    "dc": "http://purl.org/dc/elements/1.1/",

}


def classOrIdentifier(thing):
    if isinstance(thing, (Property, Class)):
        return thing.identifier
    else:
        assert isinstance(thing, (URIRef, BNode)), (
            "Expecting a Class, Property, URIRef, or BNode.. not a %s" % thing
        )
        return thing


def manchesterSyntax(thing, store, boolean=None, transientList=False):
    """
    Core serialization
    """
    assert thing is not None
    if boolean:
        if transientList:
            liveChildren = iter(thing)
            children = [manchesterSyntax(child, store) for child in thing]
        else:
            liveChildren = iter(Collection(store, thing))
            children = [
                manchesterSyntax(child, store) for child in Collection(store, thing)
            ]
        if boolean == OWL.intersectionOf:
            childList = []
            named = []
            for child in liveChildren:
                if isinstance(child, URIRef):
                    named.append(child)
                else:
                    childList.append(child)
            if named:

                def castToQName(x):
                    prefix, uri, localName = store.compute_qname(x)
                    return ":".join([prefix, localName])

                if len(named) > 1:
                    prefix = "( " + " AND ".join(map(castToQName, named)) + " )"
                else:
                    prefix = manchesterSyntax(named[0], store)
                if childList:
                    return (
                        str(prefix)
                        + " THAT "
                        + " AND ".join(
                            [str(manchesterSyntax(x, store))
                             for x in childList]
                        )
                    )
                else:
                    return prefix
            else:
                return "( " + " AND ".join([str(c) for c in children]) + " )"
        elif boolean == OWL.unionOf:
            return "( " + " OR ".join([str(c) for c in children]) + " )"
        elif boolean == OWL.oneOf:
            return "{ " + " ".join([str(c) for c in children]) + " }"
        else:
            assert boolean == OWL.complementOf

    elif OWL.Restriction in store.objects(subject=thing, predicate=RDF.type):
        prop = list(store.objects(subject=thing, predicate=OWL.onProperty))[0]
        prefix, uri, localName = store.compute_qname(prop)
        propString = ":".join([prefix, localName])
        label = store.label(prop).strip()
        if label and (label != localName):
            propString = propString + "(" + label + ")"

        for onlyClass in store.objects(subject=thing, predicate=OWL.allValuesFrom):
            return "( %s ONLY %s )" % (propString, manchesterSyntax(onlyClass, store))
        for val in store.objects(subject=thing, predicate=OWL.hasValue):
            return "( %s VALUE %s )" % (propString, manchesterSyntax(val, store))
        for someClass in store.objects(subject=thing, predicate=OWL.someValuesFrom):
            return "( %s SOME %s )" % (propString, manchesterSyntax(someClass, store))
        cardLookup = {
            OWL.maxCardinality: "MAX",
            OWL.minCardinality: "MIN",
            OWL.cardinality: "EQUALS",
        }
        for s, p, o in store.triples_choices((thing, list(cardLookup.keys()), None)):
            return "( %s %s %s )" % (propString, cardLookup[p], o)
    compl = list(store.objects(subject=thing, predicate=OWL.complementOf))
    if compl:
        return "( NOT %s )" % (manchesterSyntax(compl[0], store))
    else:
        prolog = "\n".join(["PREFIX %s: <%s>" % (k, nsBinds[k])
                           for k in nsBinds])
        qstr = (
            prolog
            + "\nSELECT ?p ?bool WHERE {?class a owl:Class; ?p ?bool ."
            + "?bool rdf:first ?foo }"
        )
        initb = {Variable("?class"): thing}
        for boolProp, col in store.query(qstr, processor="sparql", initBindings=initb):
            if not isinstance(thing, URIRef):
                return manchesterSyntax(col, store, boolean=boolProp)
        try:
            prefix, uri, localName = store.compute_qname(thing)
            qname = ":".join([prefix, localName])
            thing_label = store.label(thing).strip()
            if thing_label and (thing_label != localName):
                qname = qname + "(" + thing_label + ")"
        except Exception:
            if isinstance(thing, BNode):
                return thing.n3()
            return "<" + thing + ">"
            logger.debug(
                list(store.objects(subject=thing, predicate=RDF.type)))
            raise
            return "[]"  # +thing._id.encode('utf-8')+'</em>'

        return qname


class Class(AnnotatableTerms):
    def _serialize(self, graph):
        for cl in self.subClassOf:
            CastClass(cl, self.graph).serialize(graph)
        for cl in self.equivalentClass:
            CastClass(cl, self.graph).serialize(graph)
        for cl in self.disjointWith:
            CastClass(cl, self.graph).serialize(graph)
        if self.complementOf:
            CastClass(self.complementOf, self.graph).serialize(graph)

    def serialize(self, graph):
        for fact in self.graph.triples((self.identifier, None, None)):
            graph.add(fact)
        self._serialize(graph)

    def setupNounAnnotations(self, nounAnnotations):
        if isinstance(nounAnnotations, tuple):
            CN_sgProp, CN_plProp = nounAnnotations
        else:
            CN_sgProp = nounAnnotations
            CN_plProp = nounAnnotations

        if CN_sgProp:
            self.CN_sgProp.extent = [
                (self.identifier, self.handleAnnotation(CN_sgProp))
            ]
        if CN_plProp:
            self.CN_plProp.extent = [
                (self.identifier, self.handleAnnotation(CN_plProp))
            ]

    def __init__(
        self,
        identifier=None,
        subClassOf=None,
        equivalentClass=None,
        disjointWith=None,
        complementOf=None,
        graph=None,
        skipOWLClassMembership=False,
        comment=None,
        nounAnnotations=None,
        nameAnnotation=None,
        nameIsLabel=False,
        customNameSpace=None,
    ):
        super(Class, self).__init__(identifier,
                                    graph, nameAnnotation, nameIsLabel)

        if nounAnnotations:
            self.setupNounAnnotations(nounAnnotations)
        if (
            not skipOWLClassMembership
            and (self.identifier, RDF.type, OWL.Class) not in self.graph
            and (self.identifier, RDF.type, OWL.Restriction) not in self.graph
        ):
            self.graph.add((self.identifier, RDF.type, OWL.Class))

        self.subClassOf = subClassOf and subClassOf or []
        self.equivalentClass = equivalentClass and equivalentClass or []
        self.disjointWith = disjointWith and disjointWith or []
        if complementOf:
            self.complementOf = complementOf
        self.comment = comment and comment or []

        self.custom_namespace = customNameSpace

    def _get_extent(self, graph=None):
        for member in (graph is None and self.graph or graph).subjects(
            predicate=RDF.type, object=self.identifier
        ):
            yield member

    def _set_extent(self, other):
        if not other:
            return
        for m in other:
            self.graph.add((classOrIdentifier(m), RDF.type, self.identifier))

    @TermDeletionHelper(RDF.type)
    def _del_type(self):
        pass

    extent = property(_get_extent, _set_extent, _del_type)

    def _get_annotation(self, term=RDFS.label):
        for annotation in self.graph.objects(subject=self, predicate=term):
            yield annotation

    # type: ignore[arg-type,misc]
    annotation = property(_get_annotation, lambda x: x)

    def _get_extentQuery(self):
        return (Variable("CLASS"), RDF.type, self.identifier)

    def _set_extentQuery(self, other):
        pass

    extentQuery = property(_get_extentQuery, _set_extentQuery)

    def __hash__(self):
        """
        >>> b=Class(OWL.Restriction)
        >>> c=Class(OWL.Restriction)
        >>> len(set([b,c]))
        1
        """
        return hash(self.identifier)

    def __eq__(self, other):
        assert isinstance(other, Class), repr(other)
        return self.identifier == other.identifier

    def __iadd__(self, other):
        assert isinstance(other, Class)
        other.subClassOf = [self]
        return self

    def __isub__(self, other):
        assert isinstance(other, Class)
        self.graph.remove(
            (classOrIdentifier(other), RDFS.subClassOf, self.identifier))
        return self

    def __invert__(self):
        """
        Shorthand for Manchester syntax's not operator
        """
        return Class(complementOf=self)

    def __or__(self, other):
        """
        Construct an anonymous class description consisting of the union of
        this class and 'other' and return it
        """
        return BooleanClass(
            operator=OWL.unionOf, members=[self, other], graph=self.graph
        )

    def __and__(self, other):
        """
        Construct an anonymous class description consisting of the
        intersection of this class and 'other' and return it

        >>> exNs = Namespace('http://example.com/')
        >>> namespace_manager = NamespaceManager(Graph())
        >>> namespace_manager.bind('ex', exNs, override=False)
        >>> namespace_manager.bind('owl', OWL, override=False)
        >>> g = Graph()
        >>> g.namespace_manager = namespace_manager

        Chaining 3 intersections

        >>> female = Class(exNs.Female, graph=g)
        >>> human = Class(exNs.Human, graph=g)
        >>> youngPerson = Class(exNs.YoungPerson, graph=g)
        >>> youngWoman = female & human & youngPerson
        >>> youngWoman #doctest: +SKIP
        ex:YoungPerson THAT ( ex:Female AND ex:Human )
        >>> isinstance(youngWoman, BooleanClass)
        True
        >>> isinstance(youngWoman.identifier, BNode)
        True
        """
        return BooleanClass(
            operator=OWL.intersectionOf, members=[
                self, other], graph=self.graph
        )

    def _get_subClassOf(self):
        for anc in self.graph.objects(
            subject=self.identifier, predicate=RDFS.subClassOf
        ):
            yield Class(anc, graph=self.graph, skipOWLClassMembership=True)

    def _set_subClassOf(self, other):
        if not other:
            return
        for sc in other:
            self.graph.add(
                (self.identifier, RDFS.subClassOf, classOrIdentifier(sc)))

    @TermDeletionHelper(RDFS.subClassOf)
    def _del_subClassOf(self):
        pass

    subClassOf = property(_get_subClassOf, _set_subClassOf, _del_subClassOf)

    def _get_equivalentClass(self):
        for ec in self.graph.objects(
            subject=self.identifier, predicate=OWL.equivalentClass
        ):
            yield Class(ec, graph=self.graph)

    def _set_equivalentClass(self, other):
        if not other:
            return
        for sc in other:
            self.graph.add(
                (self.identifier, OWL.equivalentClass, classOrIdentifier(sc))
            )

    @TermDeletionHelper(OWL.equivalentClass)
    def _del_equivalentClass(self):
        pass

    equivalentClass = property(
        _get_equivalentClass, _set_equivalentClass, _del_equivalentClass
    )

    def _get_disjointWith(self):
        for dc in self.graph.objects(
            subject=self.identifier, predicate=OWL.disjointWith
        ):
            yield Class(dc, graph=self.graph)

    def _set_disjointWith(self, other):
        if not other:
            return
        for c in other:
            self.graph.add(
                (self.identifier, OWL.disjointWith, classOrIdentifier(c)))

    @TermDeletionHelper(OWL.disjointWith)
    def _del_disjointWith(self):
        pass

    disjointWith = property(
        _get_disjointWith, _set_disjointWith, _del_disjointWith)

    def _get_complementOf(self):
        comp = list(
            self.graph.objects(subject=self.identifier,
                               predicate=OWL.complementOf)
        )
        if not comp:
            return None
        elif len(comp) == 1:
            return Class(comp[0], graph=self.graph)
        else:
            raise Exception(len(comp))

    def _set_complementOf(self, other):
        if not other:
            return
        self.graph.add((self.identifier, OWL.complementOf,
                       classOrIdentifier(other)))

    @TermDeletionHelper(OWL.complementOf)
    def _del_complementOf(self):
        pass

    complementOf = property(
        _get_complementOf, _set_complementOf, _del_complementOf)

    def _get_parents(self):

        for parent in itertools.chain(self.subClassOf, self.equivalentClass):
            yield parent

        link = first(self.factoryGraph.subjects(RDF.first, self.identifier))
        if link:
            listSiblings = list(
                self.factoryGraph.transitive_subjects(RDF.rest, link))
            if listSiblings:
                collectionHead = listSiblings[-1]
            else:
                collectionHead = link
            for disjCls in self.factoryGraph.subjects(OWL.unionOf, collectionHead):
                if isinstance(disjCls, URIRef):
                    yield Class(disjCls, skipOWLClassMembership=True)
        for rdfList in self.factoryGraph.objects(self.identifier, OWL.intersectionOf):
            for member in OWLRDFListProxy([rdfList], graph=self.factoryGraph):
                if isinstance(member, URIRef):
                    yield Class(member, skipOWLClassMembership=True)

    parents = property(_get_parents)

    def isPrimitive(self):
        if (self.identifier, RDF.type, OWL.Restriction) in self.graph:
            return False
        # sc = list(self.subClassOf)
        ec = list(self.equivalentClass)
        for boolClass, p, rdfList in self.graph.triples_choices(
            (self.identifier, [OWL.intersectionOf, OWL.unionOf], None)
        ):
            ec.append(manchesterSyntax(rdfList, self.graph, boolean=p))
        for e in ec:
            return False
        if self.complementOf:
            return False
        return True

    def subSumpteeIds(self):
        for s in self.graph.subjects(predicate=RDFS.subClassOf, object=self.identifier):
            yield s

    def __repr__(self, full=False, normalization=True):
        """
        Returns the Manchester Syntax equivalent for this class
        """
        exprs = []
        sc = list(self.subClassOf)
        ec = list(self.equivalentClass)
        print('equi', ec)
        for boolClass, p, rdfList in self.graph.triples_choices(
            (self.identifier, [OWL.intersectionOf, OWL.unionOf], None)
        ):
            ec.append(manchesterSyntax(rdfList, self.graph, boolean=p))
        dc = list(self.disjointWith)
        c = self.complementOf
        if c:
            dc.append(c)
        klassKind = ""
        label = list(self.graph.objects(self.identifier, RDFS.label))
        label = label and "(" + label[0] + ")" or ""
        if sc:
            if full:
                scJoin = "\n                "
            else:
                scJoin = ", "
            necStatements = [
                isinstance(s, Class)
                and isinstance(self.identifier, BNode)
                and repr(CastClass(s, self.graph))
                or
                # repr(BooleanClass(classOrIdentifier(s),
                #                  operator=None,
                #                  graph=self.graph)) or
                manchesterSyntax(classOrIdentifier(s), self.graph)
                for s in sc
            ]
            if necStatements:
                klassKind = "Primitive Type %s" % label
            exprs.append(
                "SubClassOf: %s" % scJoin.join([str(n) for n in necStatements])
            )
            if full:
                exprs[-1] = "\n    " + exprs[-1]
        if ec:
            nec_SuffStatements = [
                isinstance(s, str)
                and s
                or manchesterSyntax(classOrIdentifier(s), self.graph)
                for s in ec
            ]
            if nec_SuffStatements:
                klassKind = "A Defined Class %s" % label
            exprs.append("EquivalentTo: %s" % ", ".join(nec_SuffStatements))
            if full:
                exprs[-1] = "\n    " + exprs[-1]
        if dc:
            exprs.append(
                "DisjointWith %s\n"
                % "\n                 ".join(
                    [manchesterSyntax(classOrIdentifier(s), self.graph)
                     for s in dc]
                )
            )
            if full:
                exprs[-1] = "\n    " + exprs[-1]
        descr = list(self.graph.objects(self.identifier, RDFS.comment))
        if full and normalization:
            klassDescr = (
                klassKind
                and "\n    ## %s ##" % klassKind
                + (descr and "\n    %s" % descr[0] or "")
                + " . ".join(exprs)
                or " . ".join(exprs)
            )
        else:
            klassDescr = (
                full
                and (descr and "\n    %s" % descr[0] or "")
                or "" + " . ".join(exprs)
            )
        return (
            isinstance(self.identifier, BNode)
            and "Some Class "
            or "Class: %s " % self.qname
        ) + klassDescr

    def get_expression(self, full=False, normalization=True):
        """
        Returns the Manchester Syntax equivalent for this class
        """
        exprs = {}
        sc = list(self.subClassOf)
        ec = list(self.equivalentClass)
        for boolClass, p, rdfList in self.graph.triples_choices(
            (self.identifier, [OWL.intersectionOf, OWL.unionOf], None)
        ):
            ec.append(manchesterSyntax(rdfList, self.graph, boolean=p))
        dc = list(self.disjointWith)
        c = self.complementOf
        if c:
            dc.append(c)
        klassKind = ""
        label = list(self.graph.objects(self.identifier, RDFS.label))
        label = label and "(" + label[0] + ")" or ""
        if sc:
            if full:
                scJoin = "\n                "
            else:
                scJoin = ", "
            necStatements = [
                isinstance(s, Class)
                and isinstance(self.identifier, BNode)
                and repr(CastClass(s, self.graph))
                or
                manchesterSyntax(classOrIdentifier(s), self.graph)
                for s in sc
            ]
            if necStatements:
                klassKind = "Primitive Type %s" % label
            exprs['subClassOf'] = scJoin.join([str(n) for n in necStatements])
            if full:
                exprs[-1] = "\n    " + exprs[-1]
        if ec:
            nec_SuffStatements = [
                isinstance(s, str)
                and s
                or manchesterSyntax(classOrIdentifier(s), self.graph)
                for s in ec
            ]
            if nec_SuffStatements:
                klassKind = "A Defined Class %s" % label
            exprs['equivalentTo'] = ", ".join(nec_SuffStatements)
            if full:
                exprs[-1] = "\n    " + exprs[-1]
        if dc:
            exprs['disjointWith'] = "\n                 ".join(
                [manchesterSyntax(classOrIdentifier(s), self.graph) for s in dc])

            if full:
                exprs[-1] = "\n    " + exprs[-1]
        return exprs
