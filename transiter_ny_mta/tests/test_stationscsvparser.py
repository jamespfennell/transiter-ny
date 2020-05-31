from transiter import parse
from transiter_ny_mta import StationsCsvParser

EXAMPLE_CSV = b"""
Station ID,Complex ID,GTFS Stop ID,Division,Line,Stop Name,Borough,Daytime Routes,Structure,GTFS Latitude,GTFS Longitude,North Direction Label,South Direction Label
2,2,R03,BMT,Astoria,Astoria Blvd,Q,N W,Elevated,40.770258,-73.917843,Ditmars Blvd,Manhattan
""".strip()


def test():
    expected_rules = [
        parse.DirectionRule(id="9", priority=9, stop_id="R03N", name="Ditmars Blvd"),
        parse.DirectionRule(id="10", priority=10, stop_id="R03S", name="Manhattan"),
    ]
    parser = StationsCsvParser()
    parser.load_content(EXAMPLE_CSV)
    actual_rules = list(parser.get_direction_rules())

    # Num rules = 9 special rules + 2 rules in the example CSV
    assert 9 + 2 == len(actual_rules)

    assert expected_rules == actual_rules[-2:]
