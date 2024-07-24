from dataclasses import dataclass
from pathlib import Path
import sys
import threading

@dataclass
class Query:
    """ Dns will store a dictionary of list of queries, (A, CN, NS)
    where the key is the domain name"""
    domain_name: str
    data: str
class Dns:
    def __init__(self):
        self.master = self._load_dns()
        self.lock = threading.Lock()
    # Helper functions - Start
    def process_A_record(self, domain_name: str) -> list[Query]:
        # Finds every A record corresponding to the domain name
        response = []
        a_list = self.master['A']
        for i in range(len(a_list)):
            if (a_list[i].domain_name == domain_name):
                response.append(a_list[i])
        if (response == []):
            return None
        return response
    
    def process_CNAME_record(self, domain_name: str) -> Query:
        # Finds every CNAME record corresponding to the domain name
        cname_list = self.master['CNAME']
        for i in range(len(cname_list)):
            if (cname_list[i].domain_name == domain_name):
                return cname_list[i]
        return None
    
    def process_NS_record(self, domain_name: str) -> list[Query]:
        # Finds every NS record corresponding to the domain name
        response = []
        ns_list = self.master['NS']
        for i in range(len(ns_list)):
            if (ns_list[i].domain_name == domain_name):
                response.append(ns_list[i])
        if (response == []):
            return None
        return response
    
    def check_cname_exists(self, domain_name: str):
        if (self.process_CNAME_record(domain_name) is not None):
            return True
        return False
    
    def check_a_exists(self, domain_name: str):
        if (self.process_a_record(domain_name) is not None):
            return True
        return False
    
    def check_ns_exists(self, domain_name: str):
        if (self.process_ns_record(domain_name) is not None):
            return True
        return False
    
    def closest_ancestor(self, domain_name: str) -> list[str]:
        """ Returns a string, that is the domain name of the closest ancestor
        defaults to return "." (root server) if no ancestor is found
        """
        # Finds the ancestor NS closest to the domain name: shld always return a value
        ns_list = self.master['NS']
        parts = domain_name.split('.')
        for i in range(len(parts)):
            zone = '.'.join(parts[i:])
            if any(zone == ns.domain_name for ns in ns_list):
                return zone
            elif (zone == ""):
                return "."
        return None
    
    def referral(self, domain_name: str) -> str:
        """ Generates a referral given in the authority and additional sections """
        authority = self.closest_ancestor(domain_name)
        response = f"AUTHORITY SECTION:\n"
        a_records = [] # List of a records - list[Query]
        ns_record = self.process_NS_record(authority)
        if (ns_record == None):
            return None
        for i in range(len(ns_record)):
            response += f"{authority}  NS  {ns_record[i].data}\n"
            a_record = self.process_A_record(ns_record[i].data)
            if (a_record is not None):
                a_records.extend(a_record)
        if a_records != []:
            # NS -> A
            response += f"ADDITIONAL SECTION:\n"
            for i in range(len(a_records)):
                response += f"{a_records[i].domain_name}  A  {a_records[i].data}\n"
        return response + "\n"
    # Helper Functions - End

    def process_A_query(self, domain_name: str) -> str:
        a_record = self.process_A_record(domain_name)
        response = ""
        if (a_record is not None):
            response += f"ANSWER SECTION:\n"
            for i in range(len(a_record)):
                response += f"{a_record[i].domain_name}  A  {a_record[i].data}\n"
        else:
            cname_record = self.process_CNAME_record(domain_name)
            # loop to check cname until it reaches the end, then process A record
            if (cname_record is not None):
                response += f"ANSWER SECTION:\n"
                cname_record = self.process_CNAME_record(domain_name)
                while (cname_record is not None):
                    # prev_record keeps a record of the last cname, which is used to process A record
                    prev_record = cname_record
                    response += f"{cname_record.domain_name}  CNAME  {cname_record.data}\n"
                    cname_record = self.process_CNAME_record(cname_record.data)
                # Cname has been checked, now process A records, if not exists, do referral
                if (prev_record is not None):
                    a_record = self.process_A_record(prev_record.data)
                    if (a_record is None):
                        response += self.referral(domain_name)
                        return response
                    for i in range(len(a_record)):
                        response += f"{a_record[i].domain_name}  A  {a_record[i].data}\n"
                # When cname cannot return A record
            else:
                response += self.referral(domain_name)
        return response + "\n"
    
    def process_CNAME_query(self, domain_name: str) -> str:
        """ Processes CNAME record queries given domain name """
        response = ""
        print(domain_name)
        if (self.check_cname_exists(domain_name)):
            response += f"ANSWER SECTION:\n"
            cname_record = self.process_CNAME_record(domain_name)
            while (cname_record is not None):
                response += f"{cname_record.domain_name}  CNAME  {cname_record.data}\n"
                cname_record = self.process_CNAME_record(cname_record.data)
        else:
            response += self.referral(domain_name)
        # If CNAME is found, then send response
        # If not, then send a referral
        return response
    
    def process_NS_query(self, domain_name: str) -> str:
        """ Processes NS record queries given domain name"""
        response = ""
        ns_record = self.process_NS_record(domain_name)
        if (ns_record is not None):
            response += "ANSWER SECTION:\n"
            for i in range(len(ns_record)):
                response += f"{ns_record[i].domain_name}  NS  {ns_record[i].data}\n"
        else:
            response += self.referral(domain_name)
        # If NS is found, then send response
        # If not, then send a referral
        return response + "\n"
    
    def add_padding(self, response: str):
        lines = response.split('\n')
        width = 20
        formatted_lines = []
        for line in lines:
            if (line.endswith(":")):
                formatted_line = f'{line:<{width}}'
            else:
                components = line.split("  ")
                if (len(components) == 2):
                    formatted_line = f"{components[0]:<{width}} {components[1]:<{width}}"
                elif (len(components) == 3):
                    formatted_line = f"{components[0]:<{width}} {components[1]:<10} {components[2]:<{width}}"
                else:
                    # ID header
                    formatted_line = f'{components[0]:<{width}}'
            formatted_lines.append(formatted_line)
        formatted_response = '\n'.join(formatted_lines)
        return formatted_response
    
    def process_query(self, domain_name: str, type: str, id: int) -> str:
        """Tie all the functions together to process any query"""
        with self.lock:
            response = f"ID: {id}\n\nQUESTION SECTION:\n{domain_name}  {type}\n"
            if type == 'A':
                response += self.process_A_query(domain_name)
            elif type == 'CNAME':
                response += self.process_CNAME_query(domain_name)
            elif type == 'NS':
                response += self.process_NS_query(domain_name)
        # Process the query
        # Attempt to match the qname
        # If not matched, check CNAME, and change qname to the CNAME and start again
        return self.add_padding(response)
    
    def _load_dns(self) -> dict[str, list[Query]]:
        """ Separate record types into a dictionary of lists (key: type ; value: Query(qname, data))
        Only accepts records of A, CNAME and NS as per specification
        """
        queries = {}
        possible_types = ("A", "CNAME", "NS") # valid record types
        filepath = Path("master.txt")
        if not filepath.exists():
            sys.exit(f'Error: master.txt does not exist')
        with open("master.txt", 'r') as f:
            for line in f:
                domain_name, type, data = line.split()
                if (type not in possible_types):
                    continue
                if (type in queries):
                    queries[type].append(Query(domain_name, data))
                else:
                    queries[type] = [Query(domain_name, data)]
        return queries

                    
