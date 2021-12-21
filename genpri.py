from xml.dom import minidom
import itertools
import sys
import os
from os import walk
from optparse import OptionParser


def findItemGroupElementsWithName(itemGroups, withName):
    groupedElements = [x.getElementsByTagName(withName) for x in itemGroups]

    # flatten the nested lists of grouped Elements
    return list(itertools.chain(*groupedElements))


def removeDuplicates(theList):
    return list(set(theList))


def extractFilename(element):
    return element.attributes["Include"].value


def removePath(filename):
    return os.path.basename(filename)


def isGeneratedMOCFile(filename):
    return "moc_" in removePath(filename.lower())


def isGeneratedUIFile(filename):
    return "ui_" in removePath(filename.lower())


def isUIFormFile(filename):
    fname, ext = os.path.splitext(filename.lower())
    return ext == ".ui"


def isGeneratedQRCFile(filename):
    return "qrc_" in removePath(filename.lower())


def isQRCResourceFile(filename):
    fname, ext = os.path.splitext(filename.lower())
    return ext == ".qrc"


def isSourceFile(filename):
    return not isGeneratedMOCFile(filename) and not isGeneratedUIFile(filename) and not isGeneratedQRCFile(filename)


def extractFilesFromElements(elementName, itemGroups):
    elements = findItemGroupElementsWithName(itemGroups, elementName)

    filenames = map(extractFilename, elements)
    uniqFilenames = removeDuplicates(filenames)
    sanitisedFilenames = map(sanitise, uniqFilenames)

    return sanitisedFilenames


def unixifyPath(filename):
    return filename.replace('\\', '/')


def makePathRelative(filename):
    return "./" + filename


def sanitise(filename):
    return unixifyPath(makePathRelative(filename))


def writePRIFileList(fileHandle, filenames):
    if len(filenames) > 0:
        # loop over all but last filename
        for name in filenames[:-1]:
            fileHandle.write('\t' + "$$PWD/" + name + ' \\\n')

        # write last filename without trailing '\\' char
        fileHandle.write('\t' + "$$PWD/" + filenames[-1] + '\n')


def writePRISection(priFile, sectionName, fileList):
    if len(fileList) > 0:
        priFile.write(sectionName + ' += \\ \n')
        writePRIFileList(priFile,  fileList)
        priFile.write('\n')


def writePRIFile(filename, cpps, hpps, forms, qrcs):
    with open(filename, 'w') as f:
        writePRISection(f, "HEADERS", list(hpps))
        writePRISection(f, "SOURCES", list(cpps))
        writePRISection(f, "FORMS", list(forms))
        writePRISection(f, "RESOURCES", list(qrcs))


def getItemGroups(filterFilename):
    itemGroups = next(walk(filterFilename), (None,None,[]))[2]
    return itemGroups


def generatePRIFile(filterFilename, priFilename):
    print('Generating pri file <' + priFilename + '> for <' + filterFilename + '>')

    itemGroups = getItemGroups(filterFilename)

    customBuildCompile = filter(lambda x: ".cpp" in x, itemGroups)
    customBuildHeader = filter(lambda x: ".h" in x, itemGroups)
    customBuildUi = filter(lambda x: ".ui" in x, itemGroups)
    customBuildQrc = filter(lambda x: ".qrc" in x, itemGroups)

    allCppFiles = customBuildCompile
    allHeaderFiles = customBuildHeader
    allUiFiles = customBuildUi
    allQrcFiles = customBuildQrc

    sources = filter(isSourceFile, allCppFiles)
    headers = filter(isSourceFile, allHeaderFiles)
    forms = filter(isUIFormFile, allUiFiles)
    qrcs = filter(isQRCResourceFile, allQrcFiles)

    writePRIFile(namePri, sources, headers, forms, qrcs)


if __name__ == "__main__":
    usage = "usage: genpri - generate pri file, with 0 args from script location path, genpri <path> "
    parser = OptionParser(usage)
    options, args = parser.parse_args()

    try:
        dir,namePri = "",""
        if len(args) == 0:
            dir = os.path.dirname(os.path.abspath(__file__))
        elif len(args) == 1:
            dir = os.path.normpath(str(args[0]))
        else:
            parser.error("Incorrect number of arguments")
            exit()

        namePri = (os.path.normpath(dir)).split(os.sep)[-1] + ".pri"
        namePri = dir + '\\' + namePri
        generatePRIFile(dir, namePri)

    except IOError as e:
        print(e.strerror)
