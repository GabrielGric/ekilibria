import xml.etree.ElementTree as ET
import os

def build_windows_to_iana_map():
    base = os.path.dirname(os.path.abspath(__file__))
    xml_path = os.path.join(base, "data", "windowsZones.xml")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    mapping = {}
    for mapZone in root.findall(".//mapZone"):
        windows = mapZone.attrib['other']
        territory = mapZone.attrib['territory']
        iana = mapZone.attrib['type'].split(' ')[0]
        if territory == '001':
            mapping[windows] = iana
    return mapping
