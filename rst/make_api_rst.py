#!/usr/local/bin/python3
# coding=utf-8
from collections import OrderedDict
from string import Template
from os import mkdir

import re
from qgis import core, gui, analysis
from shutil import rmtree

limit = False
class_limit = 'QgsAdvancedDigitizingCanvasItem'

# Make sure :numbered: is only specified in the top level index - see
# sphinx docs about this.
document_header = """
:tocdepth: 1

Welcome to the QGIS Python API documentation project!
==============================================================

.. toctree::
   :maxdepth: 1
   :caption: Contents:

"""

document_footer = """
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`"""

package_header = """

PACKAGENAME
===================================

.. toctree::
   :maxdepth: 2
   :caption: PACKAGENAME:

"""

sub_group_header = """
SUBGROUPNAME
-----------------------------------

.. toctree::
   :maxdepth: 1
   :caption: SUBGROUPNAME:

"""


def generate_docs():
    """Generate RST documentation by introspection of QGIS libs.

    The function will create a docs directory (removing it first if it
    already exists) and then populate it with an autogenerated sphinx
    document hierarchy with one RST document per QGIS class.

    The generated RST documents will be then parsed by sphinx's autodoc
    plugin to extract python API documentation from them.

    After this function has completed, you should run the 'make html'
    sphinx command to generate the actual html output.
    """
    rmtree('build', ignore_errors=True)
    rmtree('api', ignore_errors=True)
    mkdir('api')
    index = open('api/index.rst', 'w')
    # Read in the standard rst template we will use for classes
    index.write(document_header)

    with open('rst/qgis_pydoc_template.txt', 'r') as template_file:
        template_text = template_file.read()
    template = Template(template_text)

    # Iterate over every class in every package and write out an rst
    # template based on standard rst template
    if (not limit):
        packages = {'core': core, 'gui': gui, 'analysis': analysis}
    else:
        packages = {'gui': gui}

    for package_name, package in packages.items():
        package_subgroups = extract_package_subgroups(package)
        mkdir('api/%s' % package_name)
        index.write('   %s/index\n' % package_name)

        package_index = open('api/%s/index.rst' % package_name, 'w')
        # Read in the standard rst template we will use for classes
        package_index.write(
            package_header.replace('PACKAGENAME', package_name))
        for package_subgroup, classes in package_subgroups.items():
            package_index.write(
                '   %s/index\n' % package_subgroup)
            mkdir('api/%s/%s' % (package_name, package_subgroup))
            subgroup_index = open('api/%s/%s/index.rst' % (
                package_name, package_subgroup), 'w')
            # Read in the standard rst template we will use for classes
            subgroup_index.write(
                sub_group_header.replace('SUBGROUPNAME', package_subgroup))
            for class_name in classes:
                prefix = class_name[0:3]
                if prefix != 'Qgs':
                    continue
                print(class_name)
                substitutions = {
                    'PACKAGE': package_name,
                    'SUBGROUP': package_subgroup,
                    'CLASS': class_name
                }
                class_template = template.substitute(**substitutions)
                class_rst = open(
                    'api/%s/%s/%s.rst' % (
                        package_name,
                        package_subgroup,
                        class_name), 'w')
                print(class_template, file=class_rst)
                class_rst.close()
                subgroup_index.write(
                    '   %s\n' % class_name)
            subgroup_index.close()
        package_index.close()

    index.write(document_footer)
    index.close()


def current_subgroup(class_name):
    """A helper to determine the current subgroup given the class name.

    For example we want to know if we are dealing with the composer classes,
    the geometry classes etc. In the case of QgsComposerStyle the extracted
    subgroup would be 'Composer'.

    :param class_name: The class name that we want to extract the subgroup
        name for. e.g. 'QgsComposerStyle', or None if parsing fails.
    :type class_name: str, None

    :returns: The subgroup name e.g. 'Composer'

    :raises: No exceptions are raises - in the event of error, None is
        returned.
    """
    stripped_prefix = class_name.replace('Qgs', '')
    try:
        first_word = re.search('^[A-Z][a-z]*', stripped_prefix).group(0)
    except AttributeError:
        return None

    return first_word


def extract_package_subgroups(package):
    """Extract the subgroups from the package provided.

    Groups are defined by any classes that have the same prefix (excluding
    the 'Qgs' prefix. So for example::

        QgsComposerItem
        QgsComposer

    Would both be part of the `Composer` groups. Classes that do no have other
    classes with a similar prefix will be consider part of the 'main'
    package group and not of a subgroup.

    TODO: Add rules so that items can eb explicitly placed into groups where
    needed.

    :param package: The  package to extract groups from e.g. qgis.core.
    :type package: object

    :returns: A dictionary where keys are subgroup names and values are
        lists of class names that are part of that subgroup.
    :rtype: OrderedDict
    """
    classes = dir(package)
    result = OrderedDict()

    # First get a list of all unique subgroups
    candidates = list()
    subgroups = list()
    for class_name in classes:
        if limit and not class_name.startswith(class_limit):
            continue
        prefix = class_name[0:3]
        if prefix != 'Qgs':
            continue
        subgroup = current_subgroup(class_name)
        if subgroup is None:
            continue
        if subgroup not in candidates:
            # make it a candidate - it will become a subgroup when another
            # class is found that belongs to the same subgroup
            candidates.append(subgroup)
        elif subgroup not in subgroups:
            # It has already been found once before so make a group
            subgroups.append(subgroup)
            result[subgroup] = []
    # Bucket for all classes lacking an obvious subgroup
    subgroups.append('other')
    result['other'] = []
    # Now look through the list again, this time adding the classes into
    # their relevant subgroups or other as appropriate
    for class_name in classes:
        if limit and not class_name.startswith(class_limit):
            continue
        prefix = class_name[0:3]
        if prefix != 'Qgs':
            continue
        subgroup = current_subgroup(class_name)
        if subgroup is None:
            continue
        if subgroup in result.keys():
            result[subgroup].append(class_name)
        else:
            result['other'].append(class_name)

    return result

if __name__ == "__main__":
    generate_docs()