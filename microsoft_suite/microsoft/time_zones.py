import xml.etree.ElementTree as ET


def build_windows_to_iana_map():
    xml_path = "data/windowsZones.xml"
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


if __name__ == "__main__":
    build_windows_to_iana_map()
