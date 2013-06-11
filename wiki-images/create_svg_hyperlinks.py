#!/usr/bin/env python

""" Add in wiki hyperlinks to SVG flowcharts, since draw.io doesn't seem to support them.
    Takes a link-free .svg file as an argument, and exports a .linked.svg file.
    Stores text->link mapping data in a .svglinks file of the same name.
"""

import sys
import os
import json
import xml.etree.ElementTree as ET

# Make sure we were passed an input file
try:
    fname_input = sys.argv[1]
except IndexError:
    print "Usage: {} input.svg".format(sys.argv[0])
    sys.exit(1)

# Determine output filenames
fname_output = os.path.splitext(fname_input)[0] + ".linked.svg"
fname_cache = os.path.splitext(fname_input)[0] + ".svglinks"

# Load in the SVG xmldata
ET.register_namespace("","http://www.w3.org/2000/svg")
ET.register_namespace("xlink","http://www.w3.org/1999/xlink")
tree = ET.parse(fname_input)

# Sanity check to make sure there are no links already
try:
    next(tree.iter(ET.QName("http://www.w3.org/2000/svg","a")))
except StopIteration:
    pass   # we're cool
else:
    print "ERROR: This SVG file already contains hyperlinks"
    sys.exit(1)

# Manually append xlink reference, because I can't figure out how to do it automatically
tree.getroot().set("xmlns:xlink", "http://www.w3.org/1999/xlink")

# Load the mapping cache, if it exists
if os.path.exists(fname_cache):
    with open(fname_cache) as f:
        mapping = json.load(f)
else:
    mapping = {}

# We want all the text elements and HTML divs
element_types_to_modify = (ET.QName("http://www.w3.org/2000/svg","text"), ET.QName("http://www.w3.org/2000/svg","switch"))

# Find all the direct parents of the elements we want
parents = []
for el in tree.iter():
    good = False
    for t in element_types_to_modify:
        if el.find(str(t)) is not None:
            good = True
            break
    
    if good:
        parents.append(el)

# Go through and put links around the items we want
for parent in parents:
    for n, el in enumerate(parent):
        if el.tag not in element_types_to_modify:
            continue

        text = el.text

        if text is None:
            # Get text from all children
            text = ""
            for subel in el.iter():
                if subel.text is not None and subel.text != "[Object]":
                    text += subel.text
                if subel.tail is not None:
                    text += subel.tail

        # Skip the weird extra elements draw.io inserts
        if text == "[Object]":
            continue

        if text in mapping:
            print "Used cached mapping for {!r} -> {!r}.".format(text, mapping[text])
        else:
            mapping[text] = raw_input("Mapping for {!r}? ".format(text))

        # Ignore empty links
        if mapping[text] == "":
            continue

        link_el = ET.Element("a", {"xlink:href":mapping[text]})
        link_el.append(el)
        parent.remove(el)
        parent.insert(n, link_el)

# Save the mapping cache
with open(fname_cache, "w") as f:
    json.dump(mapping, f, indent=0)

# Write the output file
tree.write(fname_output)

print "Wrote {!r}.".format(fname_output)
