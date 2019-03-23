import datetime
import unittest
from unittest import mock
from transiter_nycsubway import servicestatusxmlupdater
from transiter import models

class TestServiceStatusXmlParser(unittest.TestCase):

    SYSTEM_ID = '11'
    STATUS_ID = '1'
    MESSAGE_TITLE = '2'
    MESSAGE_CONTENT = '3'
    STATUS_PRIORITY = 4
    ROUTE_ONE = 'M'
    ROUTE_TWO = 'SI'
    CREATION_TIME = datetime.datetime.fromtimestamp(5)
    START_TIME = datetime.datetime.fromtimestamp(6)
    END_TIME = None
    XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <Siri xmlns:ns2="http://www.ifopt.org.uk/acsb" xmlns="http://www.siri.org.uk/siri" xmlns:ns4="http://datex2.eu/schema/1_0/1_0" xmlns:ns3="http://www.ifopt.org.uk/ifopt">
    <ServiceDelivery>
    <ResponseTimestamp>2018-09-13T20:51:24.5539640-04:00</ResponseTimestamp>
    <SituationExchangeDelivery>
    <ResponseTimestamp>2018-09-13T20:51:24.5539640-04:00</ResponseTimestamp>
    <Status>true</Status>
    <Situations>
    <PtSituationElement>
        <CreationTime>{creation_time}</CreationTime>
        <SituationNumber>{status_id}</SituationNumber>
        <PublicationWindow>
            <StartTime>{start_time}</StartTime>
        </PublicationWindow>
        <Summary xml:lang="EN"></Summary>
        <Description xml:lang="EN">{message_content}</Description>
        <LongDescription></LongDescription>
        <Planned>false</Planned>
        <ReasonName>{message_title}</ReasonName>
        <MessagePriority>{status_priority}</MessagePriority>
        <Source>
            <SourceType>directReport</SourceType>
        </Source>
        <Affects>
            <VehicleJourneys>
                <AffectedVehicleJourney>
                    <LineRef>MTA NYCT_{route_one}</LineRef>
                    <DirectionRef>1</DirectionRef>
                </AffectedVehicleJourney>
                <AffectedVehicleJourney>
                    <LineRef>MTA NYCT_{route_two}</LineRef>
                    <DirectionRef>1</DirectionRef>
                </AffectedVehicleJourney>
            </VehicleJourneys>
        </Affects>
    </PtSituationElement>
    </Situations>
    </SituationExchangeDelivery>
    </ServiceDelivery>
    </Siri>
    """.format(
        creation_time = CREATION_TIME.isoformat(),
        start_time = START_TIME.isoformat(),
        status_id = STATUS_ID,
        message_content = MESSAGE_CONTENT,
        message_title = MESSAGE_TITLE,
        status_priority=STATUS_PRIORITY,
        route_one = ROUTE_ONE,
        route_two = ROUTE_TWO
    )

    PARSED_DATA = [{
        'status_id': STATUS_ID,
        'status_type': MESSAGE_TITLE,
        'status_priority': STATUS_PRIORITY,
        'message_title': MESSAGE_TITLE,
        'message_content': MESSAGE_CONTENT,
        'creation_time': CREATION_TIME,
        'start_time': START_TIME,
        'end_time': None,
        'route_ids': [ROUTE_ONE, ROUTE_TWO]
    }]

    def test_parse(self):
        """[NYC Subway XML updater] XML parser"""
        parser = servicestatusxmlupdater.ServiceStatusXmlParser(self.XML)
        actual_data = parser.parse()

        expected_model = models.RouteStatus()
        expected_model.id = self.STATUS_ID
        expected_model.type = self.MESSAGE_TITLE
        expected_model.priority = self.STATUS_PRIORITY
        expected_model.message_title = self.MESSAGE_TITLE
        expected_model.message_content = self.MESSAGE_CONTENT
        expected_model.start_time = self.START_TIME
        expected_model.creation_time = self.CREATION_TIME

        self.assertListEqual([expected_model], actual_data)

