from rdflib import OWL, XSD, RDF, RDFS
"""
Common entities that will be added to each ontology.
"""
datatype = {OWL.rational,
            OWL.real,
            RDF.PlainLiteral,
            RDF.XMLLiteral,
            RDFS.Literal,
            XSD.anyURI,
            XSD.base64Binary,
            XSD.boolean,
            XSD.byte,
            XSD.dateTime,
            XSD.dateTimeStamp,
            XSD.decimal,
            XSD.double,
            XSD.float,
            XSD.hexBinary,
            XSD.int,
            XSD.integer,
            XSD.language,
            XSD.long,
            XSD.Name,
            XSD.NCName,
            XSD.negativeInteger,
            XSD.NMTOKEN,
            XSD.nonNegativeInteger,
            XSD.nonPositiveInteger,
            XSD.normalizedString,
            XSD.positiveInteger,
            XSD.short,
            XSD.string,
            XSD.token,
            XSD.unsignedByte,
            XSD.unsignedInt,
            XSD.unsignedLong,
            XSD.unsignedShort}


annotation_properties = {OWL.backwardCompatibleWith,
                         OWL.deprecated,
                         OWL.incompatibleWith,
                         OWL.priorVersion,
                         OWL.versionInfo,
                         RDFS.comment,
                         RDFS.isDefinedBy,
                         RDFS.seeAlso,
                         RDFS.label}
