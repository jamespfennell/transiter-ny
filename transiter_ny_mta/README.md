# Transiter NY MTA Package
 
This Python package provides
custom Transiter feed parsers for the realtime data feeds produced
by the MTA.
Currently it provides parsers for the Subway 
    (both realtime trips and alerts)
    but will be expanded to include the LIRR and MetroNorth
    once some upstream bugs in Transiter are resolved.

Having custom parsers for the NYC Subway, rather than relying purely on 
Transiter's built-in parsers, is necessary for a few reasons:

- The subway's realtime feeds use a GTFS Realtime extension to send extra
    data, such as which track each train will stop at. It's necessary
    to add extra logic to Transiter's GTFS Realtime parser in order to see
    this extra data.
    
- There are a couple of small bugs in the realtime feed which
    the parser fixes; for example, the J and Z trains are 'backwards'
    in Williamsburg and Bushwick.

