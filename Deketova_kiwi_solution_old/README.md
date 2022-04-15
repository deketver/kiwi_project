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
- '--return_after=YYYY-MM-DD', sets the date of the soonest possible return date, results for return flight will be shown after this date (default None)
- '--results_limit=n', where n is integer, sets maximum number of results returned for each trip (defalt None) 


## How to run
Execution file is: solution.py
How to run from command prompt or terminal, possible way to run depending on OS (example): 
- Windows: python solution.py example\example3.csv JBN EZO --bags=2 --departure_after=2021-09-02 --return_after=2021-09-07 --max_airports=3
- Linux: python3 solution.py example/example3.csv JBN EZO --bags=2 --return --departure_after=2021-09-09 --return_after=2021-09-07 --max_airports=7 --results_limit=2


## What program does

Program searches through all possible combinations based on input parameters given.<br>
The best rersults are printed in console. All results for given limitations are printed in JSON file, which is named according to the origin and destination airport.<br>
Program recursively searches flights from origin airports, until it reaches final destination. Every time, the new 'origin' airport is set based on the previous flight destination.<br>
Search ends when the desired final destination is met or there are not any other possible combinations for search, as the flights were excluded due to given conditions.<br>
Final results are sorted based on final total price. 


## Program returns
- For one-way trip, creates JSON file with results flight_search_origin_destination.json
- For return trip, creates additional JSON with results for return trip: flight_seach_destination_origin.json


