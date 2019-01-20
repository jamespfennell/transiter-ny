import datetime
import re
from xml.etree import ElementTree
import dateutil.parser

from transiter import models
from transiter.services.update import routestatusupdater

def update(feed, content):

    parser = ServiceStatusXmlParser(content)
    route_statuses = parser.parse()
    routestatusupdater.sync_route_statuses(
        feed.system,
        route_statuses
    )
    return True


class ServiceStatusXmlParser:

    NAMESPACE = '{http://www.siri.org.uk/siri}'

    def __init__(self, raw_xml):
        self._raw_xml = raw_xml

    def parse(self):
        route_statuses = []
        root = ElementTree.fromstring(self._raw_xml)
        situations = self._find_descendent_element(root, 'Situations')
        for situation in situations:
            route_status = models.RouteStatus()
            model_attr_to_xml_tag = {
                'id': 'SituationNumber',
                'type': 'ReasonName',
                'message_title': 'ReasonName',
                'message_content': 'Description',
                'creation_time': 'CreationTime'
            }
            for model_attr, xml_tag in model_attr_to_xml_tag.items():
                route_status.__setattr__(
                    model_attr,
                    self._get_content_in_child_element(situation, xml_tag)
                )
            route_status.creation_time = self._time_string_to_datetime(
                self._get_content_in_child_element(
                    situation,
                    'CreationTime'
                )
            )
            route_status.priority = int(
                self._get_content_in_child_element(
                    situation,
                    'MessagePriority'
                ))

            publication_window = self._find_child_element(
                situation, 'PublicationWindow')
            route_status.start_time = self._time_string_to_datetime(
                self._get_content_in_child_element(
                    publication_window,
                    'StartTime'
                )
            )
            route_status.end_time = self._time_string_to_datetime(
                self._get_content_in_child_element(
                    publication_window,
                    'EndTime'
                )
            )

            route_status.route_ids = set()
            for route_string in self._get_content_in_descendent_elements(
                    situation, 'LineRef'):
                index = route_string.rfind('_')
                route_status.route_ids.add(route_string[index+1:])

            regex_str = '(?P<title>([A-Z]+ )*[A-Z]{2,})'
            regex = re.compile(regex_str)
            match = regex.match(route_status.message_content)
            if match is not None:
                new_title = match.group('title').capitalize()
                new_content = route_status.message_content[len(new_title):].strip()
                route_status.message_title = new_title
                route_status.message_content = new_content

            route_statuses.append(route_status)
        return route_statuses

    @classmethod
    def _get_content_in_child_element(cls, element, tag):
        child_element = cls._find_child_element(element, tag)
        if child_element is None:
            return None
        return child_element.text.strip()

    @classmethod
    def _find_child_element(cls, element, tag):
        return element.find(cls.NAMESPACE + tag)

    @classmethod
    def _find_descendent_element(cls, element, tag):
        for descendent in element.iter(cls.NAMESPACE + tag):
            return descendent

    @classmethod
    def _get_content_in_descendent_elements(cls, element, tag):
        for descendent in element.iter(cls.NAMESPACE + tag):
            yield descendent.text.strip()

    @staticmethod
    def _time_string_to_datetime(time_string):
        if time_string is None:
            return None
        return dateutil.parser.parse(time_string)

