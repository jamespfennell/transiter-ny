#
# (c) James Fennell 2019. Released under the MIT License.
#
"""
Module that provides the parser for the NYC Subway's ServiceStatusSubway.xml feed.
"""
import re
from xml.etree import ElementTree

import dateutil.parser
from transiter import models


# Additional arguments are accepted for forwards compatibility
# noinspection PyUnusedLocal
def parse(binary_content, *args, **kwargs):
    return ServiceStatusXmlParser(binary_content).parse()


class ServiceStatusXmlParser:
    NAMESPACE = "{http://www.siri.org.uk/siri}"

    def __init__(self, raw_xml):
        self._raw_xml = raw_xml

    def parse(self):
        route_statuses = []
        root = ElementTree.fromstring(self._raw_xml)
        situations = self._find_descendent_element(root, "Situations")
        for situation in situations:
            alert = models.Alert()
            model_attr_to_xml_tag = {
                "id": "SituationNumber",
                "header": "ReasonName",
                "description": "Description",
                "creation_time": "CreationTime",
            }
            for model_attr, xml_tag in model_attr_to_xml_tag.items():
                alert.__setattr__(
                    model_attr, self._get_content_in_child_element(situation, xml_tag)
                )
            if alert.description is None:
                alert.description = ""
            alert.creation_time = self._time_string_to_datetime(
                self._get_content_in_child_element(situation, "CreationTime")
            )
            alert.priority = int(
                self._get_content_in_child_element(situation, "MessagePriority")
            )

            publication_window = self._find_child_element(
                situation, "PublicationWindow"
            )
            alert.start_time = self._time_string_to_datetime(
                self._get_content_in_child_element(publication_window, "StartTime")
            )
            alert.end_time = self._time_string_to_datetime(
                self._get_content_in_child_element(publication_window, "EndTime")
            )

            alert.route_ids = set()
            for route_string in self._get_content_in_descendent_elements(
                situation, "LineRef"
            ):
                index = route_string.rfind("_")
                alert.route_ids.add(route_string[index + 1 :])

            regex_str = "(?P<title>([A-Z]+ )*[A-Z]{2,})"
            regex = re.compile(regex_str)

            match = regex.match(alert.description)
            if match is not None:
                new_title = match.group("title").capitalize()
                new_content = alert.description[len(new_title) :].strip()
                alert.description = new_content
                alert.header += " ({})".format(new_title)

            delay = "delay" in alert.description.lower()
            if not delay:
                for condition in self._get_content_in_descendent_elements(
                    situation, "Condition"
                ):
                    if "delay" in condition.lower():
                        delay = True

            if delay:
                alert.effect = alert.Effect.SIGNIFICANT_DELAYS
            else:
                alert.effect = alert.Effect.MODIFIED_SERVICE

            planned = self._get_content_in_child_element(situation, "Planned") == "true"
            if planned:
                alert.cause = alert.Cause.MAINTENANCE
            else:
                alert.cause = alert.Cause.ACCIDENT

            route_statuses.append(alert)
        return route_statuses

    @classmethod
    def _get_content_in_child_element(cls, element, tag):
        child_element = cls._find_child_element(element, tag)
        if child_element is None:
            return None
        if child_element.text is None:
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
            if descendent is None or descendent.text is None:
                continue
            yield descendent.text.strip()

    @staticmethod
    def _time_string_to_datetime(time_string):
        if time_string is None:
            return None
        return dateutil.parser.parse(time_string)
