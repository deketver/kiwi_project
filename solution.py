# -*- coding: utf-8 -*-
import sys
import os
import csv
import sqlite3
import re
from datetime import datetime
from datetime import timedelta
import os.path
import json


# osetrit moznost, kdy mam serii napriklad 6 letu, ze se v nem nevyskytuji nejaka repetitivni letiste
# upravit nektere metody, neco by slo udelat lepe?
# pridat logiku pro zpatecny lety - done
# pro uzivatele prepinace, kdy chce omezit jeste casy odlety, priletu, dobu pobytu?
# Zkusit otestovat, zda podava dobre reseni? Ale jak? Co pocty moznosti?
# otocit poradi printeni vysledku
# logika vypisovani do souboru
# pocitat celkovou dobu byti na ceste - done
# pridat jeste razeni od doby letu?
# napsat si sama nejake assertion testy? ale asi az v patek nebo o vikendu, az bude cas!
# zitra hlavne delat na praci a veci do skoly Veruuu :)


# zkusit vysortovat vysledky dle nejvyssih poctu navstivenych letist a zkonstrlovat :)

# pridat departure_after, arival_after, number of results for each direction do you wish to show?
# main priority - time traveled, price? - default is price
# max number of results shown
# max number of airports visited

def process_inputs(argv):
    """Function to read inputs from command line"""

    regex_airport = r"^[A-Z]{3}$"
    regex_bags = r"bags="
    regex_return = r"return"
    regex_max_airport = r"max_airports="
    regex_departure_after = r"departure_after="
    regex_return_after = r"return_after="
    regex_results_limit = r"results_limit="

    bags = 0
    return_trip = False
    source_file = argv[0]
    start = ""
    final_destination = ""
    max_airports = 7
    departure_after = None
    return_after = None
    result_limit = None

    if len(argv) < 3:
        print("Not enough input arguments, at least 3 arguments needed: source_file, departure, arrival")
        exit(0)

    # print(os.getcwd())
    if not os.path.exists(source_file):
        print("Source file was not found.\nMake sure to use \'/\' in file path when running on Linux and check the "
              "file name.\nSource "
              "file has to be the first argument after executing script.")
        exit(0)
    for item in argv[1:]:
        if re.search(regex_airport, item) is not None:
            if start == "":
                start = item
            else:
                final_destination = item
        elif re.search(regex_bags, item) is not None:
            try:
                bags = int(item.split("=")[1])
            except:
                print("Number of bags given is not integer, bags are set to 0.\n Correct format is e: --bags=1")
                bags = 0
        elif re.search(regex_return, item) is not None:
            return_trip = True
        elif re.search(regex_max_airport, item) is not None:
            try:
                max_airports = int(item.split("=")[1])
            except:
                print(
                    "Number of maximum airports visited given is not integer,set to default 7.\n Correct format is e: --maximum_airports=7")
        elif re.search(regex_departure_after, item) is not None:
            date_format = r"^[0-9]{4}-[0-9]{2}-[0-9]{2}"
            given_date = item.split("=")[1]
            if re.search(date_format, given_date) is not None:
                departure_after = given_date
            else:
                print(
                    "Departure after date was not in expected format --departure_after=YYYY-MM-DD, set to default None")
        elif re.search(regex_return_after, item) is not None:
            date_format = r"^[0-9]{4}-[0-9]{2}-[0-9]{2}"
            given_date = item.split("=")[1]
            if re.search(date_format, given_date) is not None:
                return_after = given_date
            else:
                print("Return after date was not in expected format --return_after=YYYY-MM-DD, set to default None")

        elif re.search(regex_results_limit, item) is not None:
            try:
                result_limit = int(item.split("=")[1])
            except:
                print(
                    "Results limit given is not integer,set to default None.\n Correct format is e: --results_limit=10")

        else:
            print("Argument ", item, "was not identified.")
            print("Possible arguments: source_file origin destination --bags=1 --return")
            print("Origin and Destination are airports in format AAA YYY")
            exit(0)

    return source_file, start, final_destination, bags, return_trip, max_airports, departure_after, return_after, result_limit


def test_file(source_file):
    """Function tests if given source file exists"""
    if not os.path.exists(source_file):
        raise Exception("Input file not found")
    return True


class FlightSearch:
    """FlightSearch class"""

    def __init__(self, source_file, start, final_destination, bags, return_trip):
        self.source_file = source_file
        self.start_destination = start,
        self.final_destination = final_destination,
        self.bags = bags
        self.return_trip = return_trip

    def open_source_file(self):
        # mozna nebude potreba?
        with open(self.source_file, 'r+') as file:
            reader = csv.DictReader(file)
            for row in reader:
                print(row)
                break

    def read_first_line(self):
        """Function returns first line of the source_file"""
        with open(self.source_file, 'r+') as file:
            for line in file:
                first_line = line.rstrip()
                break
            return first_line


class FlightDatabase:
    """To store flight information"""

    def __init__(self, source_file, columns):
        self.columns = columns
        # self.all_columns = self.columns + ", utc_departure, utc_arrival"

        self.connection = sqlite3.connect(":memory:")
        self.cursor = None
        self.source_file = source_file
        self.table_name = "flight_data"
        self.origin_table = None
        self.destination_table = None

    def create_connection(self):
        """Returns connection to in memory database"""
        # Mozna nebude potreba?
        self.connection = sqlite3.connect(":memory:")
        return

    def create_table(self):
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
        mark_list = ['?' for item in self.columns.split(',')]
        question_string = ','.join(mark_list)
        return question_string

    def read_data(self):
        self.cursor.execute("select * from flight_data;")
        read = self.cursor.fetchall()
        for row in read:
            print(row)

    def search_airports(self, origin, destination):
        # print("Select * from {0} WHERE {1}={2}".format(self.table_name, 'origin', "\'"+origin+"\'"))
        self.cursor.execute("Select * from {0} WHERE {1}={2}".format(self.table_name, 'origin', "\'" + origin + "\'"))
        result = self.cursor.fetchall()
        if result:
            self.origin_table = result
            print("Pocet ziskanych vysledku je:", len(result))
        else:
            print("Origin not found in table")
            exit(0)
        self.cursor.execute(
            "Select * from {0} WHERE {1}={2}".format(self.table_name, 'destination', "\'" + destination + "\'"))
        result = self.cursor.fetchall()
        if result:
            print("Pocet ziskanych vysledku je:", len(result))
            self.destination_table = result
        else:
            print("Destination not found in table")
            exit(0)

    def search_origin_airport(self, airport):
        self.cursor.execute("Select * from {0} WHERE {1}={2}".format(self.table_name, 'origin', "\'" + airport + "\'"))
        result = self.cursor.fetchall()
        if result:
            self.origin_table = result
            # print("Pocet ziskanych vysledku je:", len(result))
            return self.origin_table
        else:
            print("Origin not found in table")
            exit(0)


class Node:
    def __init__(self, data, parent, origin):
        self.data = data
        self.parent = parent
        self.ended_node = False
        self.arrived_destination = False  # possible not needed
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
        self.flight_no = self.data[0]
        self.origin = self.data[1]
        self.destination = self.data[2]
        self.departure_time = self.data[3]
        self.arrival_time = self.data[4]
        self.base_price = float(self.data[5])
        self.bag_price = float(self.data[6])
        self.bags_allowed = int(self.data[7])
        self.number_of_predecessor = self.parent.number_of_predecessor + 1
        # zkontrolovat - nepridava se mi to duplikovane?
        self.list_visited_airpt = self.parent.list_visited_airpt + [self.origin]

    def set_origin(self, origin):
        self.origin = origin

    def print_node_data(self):
        print(
            """Flight no: {0}, origin {1}, destination {2}, \n
            origin price {3}, cumulated price {4},\n
            departure time {5}, arrival time {6},\n
            number of bags allowed {7}, bags price {8},\n
            list of visited airports: {9}""".format(self.flight_no, self.origin,
                                                    self.destination, self.base_price,
                                                    self.current_price,
                                                    self.departure_time, self.arrival_time,
                                                    self.bags_allowed,
                                                    self.bag_price, self.list_visited_airpt))

    def return_parent(self):
        return self.parent


class Graph:
    def __init__(self, origin, destination, number_of_bags, data_table, max_number_airports=7, results_limit=None,
                 search_after=None, return_after=None):
        self.first_node = Node(None, None, origin)
        self.list_of_nodes = [self.first_node]  # maybe not neede?
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
        self.results_limit = results_limit
        self.search_after_date = search_after,
        self.return_after = return_after

    def add_node(self, node):
        self.list_of_nodes.append(node)

    def add_searched_results(self, parent: Node, searched_results):
        list_of_to_be_searched = []
        number_of_new_nodes = len(searched_results)
        # print("number of new nodes", number_of_new_nodes)
        for i in range(number_of_new_nodes):
            origin = searched_results[i][1]
            node = Node(searched_results[i], parent, origin)
            node.assign_data_node()
            # node.print_node_data()
            self.list_of_nodes.append(node)
            if node.bags_allowed < self.bags_required:
                node.ended_node = True
                self.list_of_ended_nodes.append(node)
                continue

            if node.destination == self.origin:
                node.ended_node = True
                self.list_of_ended_nodes.append(node)
                continue

            # tato podminka mi vyradila pulku reseni, mrknout se na reseni, zda ok?
            if node.destination in node.list_visited_airpt:
                node.ended_node = True
                self.list_of_ended_nodes.append(node)
                continue
            if node.number_of_predecessor >= self.max_number_airports:
                node.ended_node = True
                self.list_of_ended_nodes.append(node)
                continue
            if parent.arrival_time and (datetime.fromisoformat(parent.arrival_time) + timedelta(hours=1) > \
                                        datetime.fromisoformat(node.departure_time)):
                node.ended_node = True
                self.list_of_ended_nodes.append(node)
                continue
            if parent.arrival_time and (datetime.fromisoformat(parent.arrival_time) + \
                                        timedelta(hours=6) < datetime.fromisoformat(node.departure_time)):
                node.ended_node = True
                self.list_of_ended_nodes.append(node)
                continue
                # zde musim rozestringovat pripadne prijezdove datum, pricist k nemu hodinu a porovnat s aktualni node departure casem
            node.current_price = parent.current_price + self.bags_required * node.bag_price + node.base_price
            if node.destination == self.destination and node.ended_node is not True:
                node.arrived_destination = True
                self.list_of_last_nodes.append(node)
                self.list_of_ended_nodes.append(node)
                continue
            # print('got through all conditions')
            if node.ended_node is not True:
                new_searched_results = self.data_table.search_origin_airport(node.destination)
                # print(new_searched_results)
                self.add_searched_results(node, new_searched_results)
        return

    def print_results_file(self, exists=False):
        result_data = []
        for node in self.list_of_last_nodes:
            flight_line = []
            arrival = node.arrival_time
            departure = ""
            max_bags_line = 100
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
            results_dict = {"flights":[]}
            item_dict = {}
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
        if not exists:
            with open('results.csv', 'w+') as file:
                json.dump(result_data, file, indent=4)
        else:
            with open('results.csv', 'a+') as file:
                json.dump(result_data, file, indent=4)

    def print_last_nodes(self):
        for item in self.list_of_last_nodes:
            item.print_node_data()

    def get_last_nodes_len(self):
        print(len(self.list_of_last_nodes))

    def sort_results(self):
        self.list_of_last_nodes = sorted(self.list_of_last_nodes, key=lambda node: node.departure_time)
        self.list_of_last_nodes = sorted(self.list_of_last_nodes, key=lambda node: node.current_price)
        self.is_sorted = True
        return

    def test_results_exist(self):
        if len(self.list_of_last_nodes) < 1:
            print("No results found for given search combination")
            exit(0)
        return

    def print_whole_line(self, node, best_results=False):
        arrival = node.arrival_time
        departure = ""
        max_bags_line = 100
        while node.parent is not None:
            # print("Parent type", type(node.parent))
            # print("Is parrent None? ", node.parent is None)
            node.print_node_data()
            if node.bags_allowed < max_bags_line:
                max_bags_line = node.bags_allowed
            if node.parent.departure_time is None:
                departure = node.departure_time
                self.best_price = node.current_price
            node = node.parent
            # print("Node departure", node.departure_time)
        # departure = node.departure_time
        print("departure: ", departure, "arrival: ", arrival)
        time_traveled = datetime.fromisoformat(arrival) - datetime.fromisoformat(departure)
        print("Time totally traveled: ", time_traveled)
        if best_results:
            self.best_solution_time = time_traveled
            self.line_max_bags = max_bags_line

    def print_part_last_nodes(self, length=10):
        if len(self.list_of_last_nodes) > length:
            finish = length
        else:
            finish = len(self.list_of_last_nodes)
        for i in range(finish):
            print("Line start")
            self.print_whole_line(self.list_of_last_nodes[i])
            print("Line end\n")

    def print_best_results(self):
        if self.is_sorted is True:
            best_item = self.list_of_last_nodes[0]
            self.print_whole_line(best_item, True)
            print("Number of bags allowed at selected line: ", self.line_max_bags)
        else:
            self.sort_results()
            self.print_best_results()


def main(argv):
    """Main function"""
    # print(argv)
    source_file, start, final_destination, bags, return_trip, max_airports, departure_after, return_after, results_limit = process_inputs(argv)
    if test_file(source_file):
        #predelat do print result
        print("File found, Searched combination:\nOrigin: {0}, Destination: {1}, Bags: {2}, Return trip: {3}".format(
            start,
            final_destination,
            bags,
            return_trip))
        new_search = FlightSearch(source_file, start, final_destination, bags, return_trip)
        # new_search.open_source_file()
        columns = new_search.read_first_line()
        flight_table = FlightDatabase(source_file, columns)

        # Vytvoreni tabulky a naplneni daty
        flight_table.create_table()

        # abych otestovala, zda tam vubec zdrojove a cilove letiste v datech je:
        # flight_table.search_airports(start, final_destination)

        # ted budu chtit hledat jednotliva letiste a napojovat je na sebe
        # origin_node = Node(None, None, start) dle finalni architektury asi nebude potreba
        flights_graph = Graph(start, final_destination, bags, flight_table, max_airports, departure_after, results_limit)
        table = flight_table.search_origin_airport(start)
        flights_graph.add_searched_results(flights_graph.first_node, table)
        # print("Last nodes")

        flights_graph.get_last_nodes_len()
        flights_graph.test_results_exist()
        # flights_graph.print_last_nodes()
        flights_graph.sort_results()
        flights_graph.print_results_file()

        # kdyz bych chtela videt vsechny mozne vysledky
        # flights_graph.print_part_last_nodes()

        flights_graph.print_best_results()
        #print("From attribute: ", flights_graph.best_solution_time)

        if new_search.return_trip is True:
            print("\n Return trip \n")
            graph_return = Graph(final_destination, start, bags, flight_table, max_airports, return_after, results_limit)
            table_return = flight_table.search_origin_airport(final_destination)
            graph_return.add_searched_results(graph_return.first_node, table_return)
            graph_return.get_last_nodes_len()
            graph_return.test_results_exist()
            graph_return.sort_results()

            graph_return.print_results_file(True)

            # graph_return.print_part_last_nodes()
            graph_return.print_best_results()


if __name__ == "__main__":
    main(sys.argv[1:])
