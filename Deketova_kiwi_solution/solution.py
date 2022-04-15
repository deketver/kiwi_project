# -*- coding: utf-8 -*-
import os
import sqlite3
import re
from datetime import datetime
from datetime import timedelta
import os.path
import json
import argparse


def process_inputs():
    """Function to read inputs from command line
    arguments: argv - list of input information provided by user"""

    parser = argparse.ArgumentParser()
    parser.add_argument("source_file", type=str, help="path to source file") #another possibility argparse.FileType('r', encoding='utf-8')
    parser.add_argument("origin", type=str, help="origin airport")
    parser.add_argument("destination", type=str, help="destination airport")
    parser.add_argument("--return", dest="R", help="searches also for return trip", action="store_true")
    parser.add_argument("--bags", type=int, help="sets number of bags for given trip", action="store", default=0)
    parser.add_argument("--max_airports", type=int, help="sets maximum number of airports visited in the trip", action="store", default=7)
    parser.add_argument("--departure_after", type=str, help="departure after date in YYYY-MM-DD format")
    parser.add_argument("--return_after", type=str, help="return after date in YYYY-MM-DD format")
    parser.add_argument("--results_limit", type=int, help="sets maximum number of results displayed", action="store")

    args = parser.parse_args()

    source_file = args.source_file
    origin = args.origin
    destination = args.destination
    return_trip = args.R 
    bags = args.bags
    max_airports = args.max_airports
    departure_after = args.departure_after
    return_after = args.return_after
    result_limit = args.results_limit

    if departure_after:
        date_format = r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
        if re.search(date_format, departure_after) is None:
            print(
                "Departure after date was not in expected format --departure_after=YYYY-MM-DD, set to default None\n")
            departure_after = None

    if return_after:
        date_format = r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
        if re.search(date_format, return_after) is None:
            print(
              "Departure after date was not in expected format --departure_after=YYYY-MM-DD, set to default None\n")
       
    return source_file, origin, destination, bags, return_trip, max_airports, departure_after, return_after, result_limit


def test_file(source_file):
    """
    Function tests if given source file exists
    params: source_file - path to given file"""
    if not os.path.exists(source_file):
        raise Exception("Input file not found")
    return True

def read_first_line(source_file):
    """Function returns first line of the source_file"""
    with open(source_file, 'r+') as file:
        for line in file:
            first_line = line.rstrip()
            break
        return first_line

class FlightDatabase:
    """
    To store all flights information - data from csv file.
    Creates a database in :memory:, database consists only of one table.
    """

    def __init__(self, source_file, columns):
        self.columns = columns
        self.connection = sqlite3.connect(":memory:")
        self.cursor = None
        self.source_file = source_file
        self.table_name = "flight_data"
        self.origin_table = None
        self.destination_table = None

    def create_table(self):
        """
        Method creates data table and inserts data from source csv file.
        """
        self.cursor = self.connection.cursor()
        self.cursor.execute("Create table flight_data (" + self.columns + ");")
        first_row = 0
        with open(self.source_file, 'r+') as file:
            for line in file:
                if first_row > 0:
                    line = line.rstrip()
                    line = line.split(',')
                    self.cursor.execute(
                        "Insert into flight_data (" + self.columns + ") values (" + self.questionmark_str() + ");",
                        line)
                    self.connection.commit()
                else:
                    first_row += 1

    def questionmark_str(self) -> str:
        """
        Methods to get string of '?' needed for table data insert.
        return: question_string - string of question marks, number of which corresponds with number of columns in table
        """""
        mark_list = ['?' for item in self.columns.split(',')]
        question_string = ','.join(mark_list)
        return question_string

    def search_airports(self, origin: str, destination: str):
        """
        Method checks weather origin and destination airports are present in dataset.
        :param origin: origin airport
        :param destination: destination airport
        """
        self.cursor.execute("Select * from {0} WHERE {1}={2}".format(self.table_name, 'origin', "\'" + origin + "\'"))
        result = self.cursor.fetchall()
        if not result:
            print("Origin not found in table")
            exit(0)
        self.cursor.execute(
            "Select * from {0} WHERE {1}={2}".format(self.table_name, 'destination', "\'" + destination + "\'"))
        result = self.cursor.fetchall()
        if not result:
            print("Destination not found in table")
            exit(0)
        return

    def search_origin_airport(self, airport):
        """
        Method sets self.origin_table containing flight table data for origin airport given.
        :param airport: origin airport, for which are we searching flights
        """
        self.cursor.execute("Select * from {0} WHERE {1}={2}".format(self.table_name, 'origin', "\'" + airport + "\'"))
        result = self.cursor.fetchall()
        if result:
            self.origin_table = result
            return self.origin_table
        else:
            print("Origin not found in table")
            exit(0)


class Node:
    """
    Node class.
    One Node represents given flight will all given flight information.
    Node has an information about its ancestor - parent (Node)
    """

    def __init__(self, data, parent, origin):
        self.data = data
        self.parent = parent
        self.ended_node = False
        self.current_price = 0
        self.origin = origin
        self.destination = ""
        self.departure_time = None
        self.arrival_time = None
        self.bag_price = None
        self.flight_no = ""
        self.base_price = 0
        self.bags_allowed = None
        self.number_of_predecessor = 0
        self.list_visited_airpt = []

    def assign_data_node(self):
        """
        Method reads corresponding data for node and assigns it to appropriate class attributes.
        """
        self.flight_no = self.data[0]
        self.origin = self.data[1]
        self.destination = self.data[2]
        self.departure_time = self.data[3]
        self.arrival_time = self.data[4]
        self.base_price = float(self.data[5])
        self.bag_price = float(self.data[6])
        self.bags_allowed = int(self.data[7])
        self.number_of_predecessor = self.parent.number_of_predecessor + 1
        self.list_visited_airpt = self.parent.list_visited_airpt + [self.origin]

    def set_origin(self, origin):
        self.origin = origin

    def print_node_data(self):
        """
        Method prints attributes data for given Node.
        """
        print(
            """Flight no: {0}, origin {1}, destination {2}, \n
            origin price {3}, cumulated price {4},\n
            departure time {5}, arrival time {6},\n
            number of bags allowed {7}, bags price {8}""".format(self.flight_no, self.origin,
                                                                 self.destination, self.base_price,
                                                                 self.current_price,
                                                                 self.departure_time, self.arrival_time,
                                                                 self.bags_allowed,
                                                                 self.bag_price))


class Graph:
    def __init__(self, origin, destination, number_of_bags, data_table, max_number_airports=7, search_after=None,
                 results_limit=None):
        self.first_node = Node(None, None, origin)
        self.list_of_last_nodes = []
        self.list_of_ended_nodes = []
        self.destination = destination
        self.origin = origin
        self.bags_required = number_of_bags
        self.data_table = data_table
        self.max_number_airports = max_number_airports
        self.is_sorted = False
        self.best_solution_time = None
        self.best_price = 0
        self.line_max_bags = 0
        self.search_after_date = search_after
        self.results_limit = results_limit

    def add_searched_results(self, parent: Node, searched_results):
        """
        Function goes through all results obtained from SQL select for given origin airport
        to see where are all possible flights going. Then based on restriction recursively calls to search
        for following flights from given destination airport to see, whether this line of flights finishes in destination
        given by the user.
        params: parent (required type Node) - creating new nodes for given parent
                searched_results - queried results on data table for given airport
        """
        number_of_new_nodes = len(searched_results)
        for i in range(number_of_new_nodes):
            origin = searched_results[i][1]
            node = Node(searched_results[i], parent, origin)
            node.assign_data_node()

            # whether flight meets conditions for number of required bags
            if node.bags_allowed < self.bags_required:
                node.ended_node = True
                self.list_of_ended_nodes.append(node)
                continue

            # if I got back to the airport I was starting at, exclude this result
            if node.destination == self.origin:
                node.ended_node = True
                self.list_of_ended_nodes.append(node)
                continue

            # if I got back to the airport I already visited before, exclude this result
            if node.destination in node.list_visited_airpt:
                node.ended_node = True
                self.list_of_ended_nodes.append(node)
                continue

            # if I got over the limit of number of visited airports and I still have not arrived, exclude this result
            if node.number_of_predecessor > self.max_number_airports:
                node.ended_node = True
                self.list_of_ended_nodes.append(node)
                continue

            # if search_after_date is provided by user, only flights after this date are valid
            if self.search_after_date and datetime.fromisoformat(node.departure_time) < datetime.fromisoformat(
                    self.search_after_date):
                node.ended_node = True
                self.list_of_ended_nodes.append(node)
                continue

            # if there is not more than 1 hour for transfer flight, exclude this result
            if parent.arrival_time and (datetime.fromisoformat(parent.arrival_time) + timedelta(hours=1) > \
                                        datetime.fromisoformat(node.departure_time)):
                node.ended_node = True
                self.list_of_ended_nodes.append(node)
                continue

            # if there is more than 6 hours for transfer flight, exclude this result
            if parent.arrival_time and (datetime.fromisoformat(parent.arrival_time) + \
                                        timedelta(hours=6) < datetime.fromisoformat(node.departure_time)):
                node.ended_node = True
                self.list_of_ended_nodes.append(node)
                continue

            # calculate current price for given flight line
            node.current_price = parent.current_price + self.bags_required * node.bag_price + node.base_price

            # if we arrived to requested destination and the flight was not excluded, add this result
            if node.destination == self.destination and node.ended_node is not True:
                self.list_of_last_nodes.append(node)
                self.list_of_ended_nodes.append(node)
                continue

            # we are still not desired destination, but flight was not excluded on conditions, search results for this
            # airport
            if node.ended_node is not True:
                new_searched_results = self.data_table.search_origin_airport(node.destination)
                self.add_searched_results(node, new_searched_results)

        return

    def print_results_file(self):
        """
        Method creates json file with all possible flights whose are matching given search conditions.
        """
        result_data = []
        # if there is limit for returned results provided by user, we track number of printed results
        limit_counter = 0
        #  to recreate the whole flight line based on the last (arrival) node, loop through all successful nodes
        for node in self.list_of_last_nodes:
            # store flight line information in flight_line
            flight_line = []
            arrival = node.arrival_time
            departure = ""
            max_bags_line = 1000
            final_node = node

            while node.parent is not None:
                flight_line.append(node)
                if node.bags_allowed < max_bags_line:
                    max_bags_line = node.bags_allowed
                if node.parent.departure_time is None:
                    departure = node.departure_time
                node = node.parent
            time_traveled = datetime.fromisoformat(arrival) - datetime.fromisoformat(departure)
            flight_line.reverse()
            results_dict = {"flights": []}
            for index in range(len(flight_line)):
                item = flight_line[index]
                item_dict = {"flight_no": item.flight_no, "origin": item.origin, "destination": item.destination,
                             "departure": item.departure_time, "arrival": item.arrival_time,
                             "base_price": item.base_price, "bag_price": item.bag_price,
                             "bags_allowed": item.bags_allowed}
                results_dict["flights"].append(item_dict)
            results_dict["bags_allowed"] = max_bags_line
            results_dict["bags_count"] = self.bags_required
            results_dict["destination"] = self.destination
            results_dict["origin"] = self.origin
            results_dict["total_price"] = final_node.current_price
            results_dict["travel_time"] = str(time_traveled)
            result_data.append(results_dict)
            if self.results_limit:
                limit_counter += 1
                if limit_counter >= self.results_limit:
                    break

        file_name = "flight_search_" + self.origin + "_" + self.destination + ".json"
        with open(file_name, 'w+') as file:
            json.dump(result_data, file, indent=4)

    def print_last_nodes(self):
        """
        Method loops through all resulted flight lines and prints flight data.
        """
        for item in self.list_of_last_nodes:
            item.print_node_data()

    def sort_results(self):
        # sort given results based on keys
        self.list_of_last_nodes = sorted(self.list_of_last_nodes, key=lambda node: node.departure_time)
        self.list_of_last_nodes = sorted(self.list_of_last_nodes, key=lambda node: node.current_price)
        self.is_sorted = True
        return

    def test_results_exist(self):
        """
        Method tests whether there are any search results obtained for given inputs.
        """
        if len(self.list_of_last_nodes) < 1:
            print("No results found for given search combination")
            exit(0)
        return


def main():
    """
    Main function
    """
    source_file, start, final_destination, bags, return_trip, max_airports, departure_after, return_after, results_limit = process_inputs()
    if test_file(source_file):

        print("File found, Searched combination:\nOrigin: {0}, Destination: {1}, Bags: {2}, Return trip: {3}, "
              "Results limit: {4}, Max airports visited: {5}\n".format(start,
                                                                       final_destination,
                                                                       bags,
                                                                       return_trip, results_limit, max_airports))

        if return_after is not None and return_trip is False:
            print("WARNING")
            print('--return_after date is valid only for return trip, this parameter is not being processed.')

        if return_trip and departure_after and return_after:
            if datetime.fromisoformat(departure_after) > datetime.fromisoformat(return_after):
                print("WARNING")
                print("Return after date is before departure date.")
                print("Departure date given: {0},\nReturn date given: {1}".format(departure_after, return_after))
                print("Return after date is set to None")
                return_after = None

        columns = read_first_line(source_file)
        # flight_table to store all data from given csv. input file
        flight_table = FlightDatabase(source_file, columns)
        # create table and insert data
        flight_table.create_table()

        # test weather origin and destination airports are present in dataset
        flight_table.search_airports(start, final_destination)
        flights_graph = Graph(start, final_destination, bags, flight_table, max_airports, departure_after,
                              results_limit)

        # create initial database search for
        table = flight_table.search_origin_airport(start)
        flights_graph.add_searched_results(flights_graph.first_node, table)
        flights_graph.test_results_exist()
        flights_graph.sort_results()
        # print all results into json file
        flights_graph.print_results_file()

        if return_trip is True:
            # to check weather there was condition for departure after:
            return_after = departure_after if return_after is None else return_after

            # Graph for return trip
            graph_return = Graph(final_destination, start, bags, flight_table, max_airports, return_after,
                                 results_limit)
            table_return = flight_table.search_origin_airport(final_destination)
            graph_return.add_searched_results(graph_return.first_node, table_return)
            graph_return.test_results_exist()
            graph_return.sort_results()

            # print all results into json file
            graph_return.print_results_file()

if __name__ == "__main__":
    main()
