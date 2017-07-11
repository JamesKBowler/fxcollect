from collections import defaultdict
from settings import XML_FILE, CAT_URL
from urllib2 import urlopen
from memory_profiler import profile
import xml.etree.ElementTree as ET


class XMLCatalogue(object):
    """
    The XMLCatalogue class is resposiable for reading the FXCM xml catalogue.
    Once the catalogue has been downloaded, the information is extracted
    and converted into a Python dictionary.
    """
    def _update_catalog_xml(self):
        """
        Makes a HTTP request for the price history catalogue and saves
        it locally as an xml file.
        """
        xml = urlopen(CAT_URL).read()
        with open(XML_FILE, 'wb') as f:
            f.write(xml)

    def _xml_to_dict(self, stream):
        """
        Reads the locally saved xml file and converts to a Python
        dictionary.
        """
        print('[%%] Parsing catalogue to Dict')
        catalog = defaultdict(dict)
        for event, symbol in ET.iterparse(XML_FILE):
            if symbol.tag == 'symbol':
                if symbol.get('price-stream') == stream:
                    main_key = symbol.get('name')
                    values = symbol.attrib
                    catalog[main_key]['attribs'] = values
                    catalog[main_key]['time-frames'] = {}
                    child = symbol.getchildren()[0]
                    for tf in child.findall('timeframe'):
                        time_frame = tf.get('name')
                        v = tf.attrib
                        catalog[main_key]['time-frames'][time_frame] = v
            #symbol.clear()
        return dict(catalog)

    def start_parser(self, stream):
        """ Kicks off the process and returns the calalogue """
        self._update_catalog_xml()
        catalog = self._xml_to_dict(stream)
        return catalog
