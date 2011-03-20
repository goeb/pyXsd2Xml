#!/usr/bin/env python

import os
import sys
import xml.dom.minidom
import getopt
import re

def main(argv):
    
    opts, args = getopt.getopt(argv, "", ["xsd-file=", "output-file="])
    
    for opt, value in opts:
        if opt == '--xsd-file':
            inputFile = value
        elif opt == '--output-dir':
            outputFile = value

    xsdAst = parseXsd(inputFile)
    logDebug(xsdAst)
    typeList = xsdAst.keys()
    typeList.sort()
    for typeName in typeList:
        o = xsdAst[typeName]
        logDebug("------------- type=", o.name, "----------------")
        logDebug(o)
        print indentXml(o.generateXmlValue(True))

def logDebug(*args):
    return
    L = map(str, args)
    s = ' '.join(L)
    sys.stderr.write(s)
    sys.stderr.write('\n')

def generateXml(xsdAst):
    return "toto"

def indentXml(xml):
    indentation = -1
    indentedXml = ''
    L = len(xml)
    for c in range(0, L-1):
        if xml[c] == '\n': continue
        elif xml[c] == '<':
            if xml[c+1] == '/':
                # closing tag
                indentedXml = indentedXml + '\n' + (' ' * 4 * indentation)
                indentation = indentation-1
            else:
                # opening tag
                indentation = indentation+1
                indentedXml = indentedXml + '\n' + (' ' * 4 * indentation)
            
            
        elif xml[c] == '>' and xml[c-1] == '/':
            # closing tag
            indentation = indentation-1
        
        indentedXml = indentedXml + xml[c]

    indentedXml = indentedXml + xml[L-1]
    return indentedXml



def createComplexType(xmlNode):
    for child in xmlNode.childNodes:
        if child.nodeName == 'xsd:sequence':
            o = SequenceType(xmlNode)
            logDebug("createComplexType:", o)
            return o

        elif child.nodeName == 'xsd:choice':
            return ChoiceType(xmlNode)

        elif child.nodeName == 'xsd:complexContent':
            return ComplexContentType(xmlNode)

def getAttribute(xmlNode, name):
    'xmlNode must be a DOM node.'
    if xmlNode.hasAttribute(name):
        value = xmlNode.getAttribute(name)
    else:
        value = None

    return value

class XsdType:

    def __init__(self):
        self.name = None
        self.ancestorName = None
        self.ancestorObject = None
        self.baseType = None

    def __repr__(self):
        result = '[' + self.name + ' / '
        result = result + str(self.ancestorName) + ', '
        result = result + str(self.baseType)
        try:
            for e in self.elements:
                result = result + str(e)
        except:
            pass # no element
        result = result + ']'

        return result

def consolidateTypeName(typeName):
    if typeName is None: return typeName
    else:
        return re.sub('_Type$', '', typeName)

class Element:

    def __init__(self, xmlNode):
        self.name = xmlNode.getAttribute('name')
        self.typeName = consolidateTypeName(getAttribute(xmlNode, 'type'))
        self.minOccurs = getAttribute(xmlNode, 'minOccurs') # for optional
        self.typeObject = None

        if self.typeName is None:
            # case of an inline type of NULL type
            # (included in the element)
            #print "Element:", self.name, "type is none"
            # TODO
            self.typeName = 'NULL'


    def resolveTypeLinks(self, xsdAst):
        try:
            o = xsdAst[self.typeName]
            self.typeObject = o
        except:
            # case of a basic type
            self.typeObject = BasicType(self.typeName, None, None, None)

    def generateXmlValue(self, withDecoration):
        xml = ''
        if self.typeObject.name == 'ENUMERATED':
            xml = xml + '<' + self.name + '/>'
        else:
            xml = xml + '<' + self.name + '>'
            logDebug("xml=", xml)
            xml = xml + self.typeObject.generateXmlValue(False)
            xml = xml + '</' + self.name + '>'

        return xml

    def __repr__(self):
        result = '[el:' + self.name + ', ' + self.typeName + ']'
        return result
        
class ComplexType(XsdType):

    def __init__(self):
        XsdType.__init__(self)
        self.elements = []
        self.minOccurs = None
        self.maxOccurs = None

    def consolidateInheritanceValues(self):
        pass # TODO

    def resolveInheritanceLink(self, xsdAst):
        pass # TODO

    def generateXmlValue(self, withDecoration):
        return '<!--ComplexType--/>'

    def resolveInheritanceLink(self, xsdAst):
        'resolve links for types of elements'
        for element in self.elements:
            element.resolveTypeLinks(xsdAst)


class ComplexContentType(ComplexType):
    def __init__(self, xmlNode):
        ComplexType.__init__(self)
        self.name = consolidateTypeName(getAttribute(xmlNode, 'name'))

class ChoiceType(ComplexType):
    def __init__(self, xmlNode):
        ComplexType.__init__(self)
        self.name = consolidateTypeName(getAttribute(xmlNode, 'name'))

        for child in xmlNode.childNodes:
            if child.nodeName == 'xsd:choice':
                #self.minOccurs = getAttribute(xmlNode, 'minOccurs')
                #self.maxOccurs = getAttribute(xmlNode, 'maxOccurs')

                for element in child.childNodes:
                    if element.nodeName == 'xsd:element':
                        e = Element(element)
                        self.elements.append(e)
                        
            else:
                # ignore
                pass
        logDebug("ChoiceType.__init__:", self)
    
    def generateXmlValue(self, withDecoration):
        xml = ''
        element = self.elements[0]
        xml = xml + element.generateXmlValue(True)
        xml = xml + '\n'
            
        if withDecoration:
            xml = '<' + self.name + '>' + xml + '</' + self.name + '>'

        return xml

class SequenceType(ComplexType):

    def __init__(self, xmlNode):
        ComplexType.__init__(self)
        self.name = consolidateTypeName(getAttribute(xmlNode, 'name'))
        for child in xmlNode.childNodes:
            if child.nodeName == 'xsd:sequence':
                self.minOccurs = getAttribute(xmlNode, 'minOccurs')
                self.maxOccurs = getAttribute(xmlNode, 'maxOccurs')

                for element in child.childNodes:
                    if element.nodeName == 'xsd:element':
                        e = Element(element)
                        self.elements.append(e)
                        logDebug("SequenceType", self.name, ": element added: ", e.name, "of type:", e.typeName)
                        
            else:
                # ignore
                pass
        logDebug("SequenceType.__init__:", self)

    def generateXmlValue(self, withDecoration):
        xml = ''
        for element in self.elements:
            xml = xml + element.generateXmlValue(True)
            xml = xml + '\n'
            
        if withDecoration:
            xml = '<' + self.name + '>' + xml + '</' + self.name + '>'

        return xml

class BasicType():
    def __init__(self, name, minInclusive, maxInclusive, length):
        self.name = consolidateTypeName(name)
        self.minInclusive = minInclusive
        self.maxInclusive = maxInclusive
        self.length = length

    def generateXmlValue(self, withDecoration):
        if self.name == 'char': xml = 'a'
        elif self.name == 'xsd:string':
            if self.length is not None:
                xml = 'b' * self.length
            else: xml = 'bbbb'

        elif self.name == 'xsd:integer':
            if self.minInclusive is not None:
                xml = str(self.minInclusive)
            elif self.maxInclusive is not None:
                xml = str(self.maxInclusive)
            else:
                xml = '444'

        elif self.name == 'xsd:hexBinary':
            xml = 'FFFFCDAB'

        elif self.name == 'NULL':
            xml = ''

        elif self.name == 'ENUMERATED':
            xml = ''

        elif self.name == 'char':
            xml = 'c'

        else:
            sys.stderr.write("Unsupported basic type: " + self.name + '\n')
            raise 1111

        return xml



class SimpleType(XsdType):

    def __init__(self, xmlNode):
        XsdType.__init__(self)
        self.length = None
        self.minInclusive = None
        self.maxInclusive = None
        self.enumeratedValues = []

        self.name = consolidateTypeName(getAttribute(xmlNode, 'name'))

        for child in xmlNode.childNodes:
            if child.nodeName == 'xsd:restriction':
                self.setRestrictions(child)

    def setRestrictions(self, xmlNode):
        self.ancestorName = consolidateTypeName(getAttribute(xmlNode, 'base'))
        # xsd:pattern not managed TODO
        for child in xmlNode.childNodes:
            if child.nodeName == 'xsd:length':
                self.length = int(getAttribute(child, 'value'))

            elif child.nodeName == 'xsd:minInclusive':
                self.minInclusive = int(getAttribute(child, 'value'))

            elif child.nodeName == 'xsd:maxInclusive':
                self.maxInclusive = int(getAttribute(child, 'value'))

            elif child.nodeName == 'xsd:enumeration':
                value = getAttribute(child, 'value')
                self.enumeratedValues.append(value)

    def generateXmlValue(self, withDecoration):
        'Return a string being a possible value for the current type'
        xml = ''
        if len(self.enumeratedValues) > 0:
            xml = '<' + self.enumeratedValues[0] + '/>'
        else:
            basicType = BasicType(self.baseType, self.minInclusive, self.maxInclusive, self.length)
            xml = basicType.generateXmlValue(False)

        if withDecoration:
            xml = '<' + self.name + '>' + xml + '</' + self.name + '>'

        return xml


    def consolidateInheritanceValues(self):
        'Copy values of ancestor locally.'
        #print "consolidateInheritanceValues self=", self.name, "ancestorName=", self.ancestorName
        if self.ancestorObject is not None:
            self.ancestorObject.consolidateInheritanceValues()

            if self.length is None:
                self.length = self.ancestorObject.length
            
            if self.minInclusive is None:
                self.minInclusive = self.ancestorObject.minInclusive
            
            if self.maxInclusive is None:
                self.maxInclusive = self.ancestorObject.maxInclusive

            self.baseType = self.ancestorObject.baseType
            #print "baseType of ", self.name, ": ", self.baseType

        else:
            self.baseType = self.ancestorName


    def resolveInheritanceLink(self, xsdAst):
        if self.ancestorName is not None:
            try:
                o = xsdAst[self.ancestorName]
                self.ancestorObject = o
            except:
                pass

def consolidateInheritance(xsdAst):
    for typeName in xsdAst.keys():
        o = xsdAst[typeName]
        o.resolveInheritanceLink(xsdAst)

    for typeName in xsdAst.keys():
        o = xsdAst[typeName]
        o.consolidateInheritanceValues()



def parseXsd(inputFile):

    dom = xml.dom.minidom.parse(inputFile)
    schemaNode = dom.getElementsByTagName("xsd:schema")[0]

    simpleTypes = []
    complexTypes = []
    for node in schemaNode.childNodes:
        if node.nodeName == 'xsd:simpleType':
            simpleTypes.append(node)
        elif node.nodeName == 'xsd:complexType':
            complexTypes.append(node)

    xsdAst = { }
    for typeNode in simpleTypes:
        o = SimpleType(typeNode)
        xsdAst[o.name] = o
        #print "Type", o.name, "found."

    for typeNode in complexTypes:
        o = createComplexType(typeNode)
        if o is not None: xsdAst[o.name] = o

    logDebug("before consolidateInheritance...xsdAst=")
    logDebug(xsdAst)
    consolidateInheritance(xsdAst)

    return xsdAst


if __name__ == "__main__":
    main(sys.argv[1:])

