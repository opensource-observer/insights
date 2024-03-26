from dataclasses import dataclass
from typing import Any


@dataclass
class Query():
    name: str
    _aggregator: str
    grouping: str
    args: dict
    _str: str = ''
    
    def aggregator(self, *args, **kwargs):
        
        return self._aggregator.format(**kwargs)
    
    def build(self, *args, **kwargs):
        self._str = """SELECT {} FROM {} {}""".format(self.aggregator(**kwargs), self.name, self.grouping)

class QueryComposer():
    
    def __init__(self, query, conn, qname='q1'):
        self.curr = qname
        query.build()
        self.query = query._str
        self.conn = conn
    
    def __str__(self):
        pass

    def compose(self, right):
        right.args['label'] = self.curr
        self.query = """SELECT {} FROM ({}) AS {} {}""".format(right.aggregator(**right.args), self.query, right.name, right.grouping)
        self.curr = right.name
        #return self.query
    
    def execute(self):
        return self.conn.execute(self.query)
        
    