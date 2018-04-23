import wikidata_processing

class PopularWikidataPropertiesDetector:
    def __init__(self):
        self.properties = {}

    def record_property_presence(self, property):
        if property not in self.properties:
            self.properties[property] = 1
        else:
            self.properties[property] += 1

    def skip_property(self, property_name):
        known = ['P18','P1566','P31','P646','P421','P910','P94','P131','P373',
        'P625','P17', 'P856', 'P1376', 'P935', 'P1435', 'P2044', 'P4046', 'P1464',
        'P206', 'P41', 'P1200', 'P884', 'P2225', 'P227', 'P30', 'P1792', 'P361',
        'P1343', 'P706', 'P949', 'P242', 'P14', 'P214', 'P197', 'P126', 'P708',
        'P2053', 'P974', 'P1653', 'P268', 'P201', 'P395', 'P571', 'P84', 'P403',
        'P47', 'P2043', 'P138', 'P36', 'P140', 'P356', 'P1889', 'P1082', 'P190',
        'P998', 'P948', 'P159', 'P443', 'P3417', 'P982', 'P1997', 'P1448', 'P6',
        'P237', 'P1036', 'P1705', 'P281', 'P150', 'P2046', 'P473', 'P213',
        'P1619', 'P127', 'P1249', 'P2788', 'P691', 'P402', 'P762', 'P4080',
        'P1427', 'P677', 'P149', 'P15', 'P1064',
        ]
        if property_name in known:
            return True
        types = wikidata_processing.get_all_types_describing_wikidata_object(property_name)
        if "Q18608871" in types:
            # Wikidata property for items about people
            return True
        return False

    def print_popular_properties(self):
        limit = 200
        iata_code_property = 'P238'
        if iata_code_property in self.properties:
            limit = self.properties[iata_code_property] * 15 + 150
        for property in self.properties.keys():
            if self.properties[property] > limit:
                if not self.skip_property(property):
                    print("https://www.wikidata.org/wiki/Property:" + str(property))
        for property in self.properties.keys():
            if self.properties[property] > limit:
                if not self.skip_property(property):
                    print("'" + str(property) + "',")

