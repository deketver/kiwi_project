# KIWI Flight Search Solution

### List of compulsory arguments:
- source_file - csv file with data
- origin - origin airport in format AMY
- destination - destination airport in format AMY


### List of optional arguments:
- '--bags=n', where n is integer (default = 0)
- '--return', sets to search also for return trip (defalt False)
- '--max_airports=n', sets maximum number of airports visited in single trip (default = 7)
- '--departure_after=YYYY-MM-DD', sets the date of the soonest possible departure date, results will be after this date (default None)
- '--return_after=YYYY-MM-DD', sets the date of the soonest possible return date, results for return flight will be shown after this date
- '--results_limit=n', where n is integer, sets maximum number of results returned for each trip (defalt None) 



