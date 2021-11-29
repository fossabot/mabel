"""
Implement a Relation, a relation is analogous to a database table.

Internally it is stored as a list of tuples with the values and a dictionary
recording the schema and other information about the relation.

Relations are approximately twice as fast as DictSets.

- self.data is an array of tuples
- self.header is a dictionary
    {
        "column": {
            "type": type
            "min": smallest
            "max": largest
            "count": count
            "unique": number of unique
        }
    }

    Only "type" can be assumed to be present, especially after a select operation
"""
import sys
import os

sys.path.insert(1, os.path.join(sys.path[0], "../../../.."))

from typing import Iterable, Tuple 
from mabel.data.internals.dictset import DictSet


class Relation():

    __slots__ = ("header", "data")

    def __init__(self, data: Iterable[Tuple] = [], header: dict = {}):
        self.data = data
        self.header = header

    def apply_selection(self, predicate):
        """
        Apply a Selection operation to a Relation, this filters the data in the 
        relation to just the entries which match the predicate.

        Parameters:
            predicate (callable):
                A function which can be applied to a tuple to determine if it 
                should be returned in the target Relation.

        Returns:
            Relation
        """
        # selection invalidates what we thought we knew about counts etc
        new_header = {k:{ "type":v.get("type") } for k,v in self.header.items()}
        return Relation(filter(predicate, self.data), new_header)

    def apply_projection(self, attributes):
        if not isinstance(attributes, (list, tuple)):
            attributes = [attributes]
        attribute_indices = []
        new_header = {k:v for k,v in self.header.items() if k in attributes}
        for index, attribute in enumerate(self.header.keys()):
            if attribute in attributes:
                attribute_indices.append(index)
        
        def _inner_projection():
            for tup in self.data:
                yield tuple([tup[indice] for indice in attribute_indices])

        return Relation(_inner_projection(), new_header)


    def materialize(self):
        self.data = list(self.data)
    
    def from_dictset(self, dictset: DictSet):
        """
        Load a Relation from a DictSet.

        In this case, the entire Relation is loaded into memory.
        """
        self.header = dictset.types()
        self.data = [
            tuple([row.get(k) for k,v in self.header.items()]) for row in dictset.collect_list()
        ]

    def to_dictset(self):
        """
        Convert a Relation to a DictSet, this will fill every column so missing entries
        will be populated with Nones.
        """
        def _inner_to_dictset():
            yield from [{k:row[i] for i, (k,v) in enumerate(self.header.items())} for row in self.data]
        return DictSet(_inner_to_dictset())


if __name__ == "__main__":
    from mabel.data import STORAGE_CLASS
    data = [
        {"number": "1", "description": "Stole ten dollars from a guy at the Camden Market"},
        {"number": "2", "description": "Took money from car coin holder"},
        {"number": "3", "description": "Copped a feel off old (Miss Jones?) but I think she liked..."},
        {"number": "4", "description": "Blew Dad’s chance to be elected Mayor."},
        {"number": "5", "description": "Picked my nose in public"},
        {"number": "6", "description": "Took Borrowed money from tip jar"},
        {"number": "7", "description": "I stole money from cars a lot"},
        {"number": "8", "description": "I did my best friend's girl A LOT"},
        {"number": "9", "description": "Cheated alot on my school tests"},
        {"number": "10", "description": "Experimented with (Baking soda?)"},
        {"number": "11", "description": "Took beer glass from cafe for ... as a present for Joy"},
        {"number": "12", "description": "Made a lady think I was god"},
        {"number": "18", "description": "Told an inappropriate story at Hank Lang's birthday party"},
        {"number": "23", "description": "Peed in the back of a cop car"},
        {"number": "26", "description": "Robbed a stoner blind"},
        {"number": "27", "description": "Made fun of people with accents"},
        {"number": "28", "description": "Stole those pine tree air freshers"},
        {"number": "29", "description": "Harassed a reporter"},
        {"number": "30", "description": "Stole a motorcycle"},
        {"number": "32", "description": "Bullied Wally Panser"},
        {"number": "33", "description": "Been a lazy lover"},
        {"number": "35", "description": "Stole organ from Reverend Hash Brown"},
        {"number": "37", "description": "Stole laptop"},
        {"number": "40", "description": "Broke Dodge and Earl Jr.'s clubhouse"},
        {"number": "41", "description": "Snatched a kid's Halloween candy when he came to my trailer to trick or treat"},
        {"number": "42", "description": "Cut holes in all of Dad's shirts to show his nipples."},
        {"number": "43", "description": "Racked a rich guy"},
        {"number": "44", "description": "Picked on a French kid"},
        {"number": "49", "description": "I've been wasteful"},
        {"number": "50", "description": "Kicked Tom out of band"},
        {"number": "51", "description": "Slept with Ralph's mom"},
        {"number": "53", "description": "Put used gum under almost every table I've ever sat at"},
        {"number": "56", "description": "Stole liquor from liquor store"},
        {"number": "56", "description": "Larceny of a kitty cat"},
        {"number": "57", "description": "Told Joy Dan Dodd messed himself on the golf course because she thought he was cute"},
        {"number": "57", "description": "Gave Randy a 'swirlie' when he was five"},
        {"number": "58", "description": "Fixed a high school football game"},
        {"number": "59", "description": "Everything I did to Dad"},
        {"number": "60", "description": "Pulled fire alarm"},
        {"number": "61", "description": "Stole Mom's car (but I gave it back)"},
        {"number": "62", "description": "Faked death to break up with a girl"},
        {"number": "62", "description": "Siphoned gas"},
        {"number": "63", "description": "Wasted electricity"},
        {"number": "64", "description": "Spray painted the bridge"},
        {"number": "64", "description": "Picked on Kenny James"},
        {"number": "65", "description": "Cost Dad the election"},
        {"number": "66", "description": "Let mice out at school play"},
        {"number": "67", "description": "Stole beer from a golfer"},
        {"number": "67", "description": "Ran over Crackers"},
        {"number": "68", "description": "Blew up mailboxes"},
        {"number": "69", "description": "Cheated on high school tests Alot"},
        {"number": "71", "description": "Took magazine from neighbor's porch"},
        {"number": "72", "description": "Cheated on girlfriend and lied about it"},
        {"number": "73", "description": "Accidentally started a forest fire"},
        {"number": "73", "description": "Always took a penny, never left a penny"},
        {"number": "74", "description": "Always ruined Joy’s Christmas"},
        {"number": "75", "description": "Took wine from church"},
        {"number": "76", "description": "Stole Borrowed Mom's car"},
        {"number": "77", "description": "Shoved an old lady out of the ... "},
        {"number": "78", "description": "Got drunk on Easter"},
        {"number": "79", "description": "Killed cat trying to see if it ... "},
        {"number": "80", "description": "Parked in handicap ... "},
        {"number": "82", "description": "Borrowed silverware from Crab Shack"},
        {"number": "83", "description": "Blew up mailboxes"},
        {"number": "84", "description": "Faked death to break up with a girl"},
        {"number": "85", "description": "Took clothes from ... laundramat"},
        {"number": "86", "description": "Stole a car from a one-legged girl"},
        {"number": "87", "description": "... paid ..."},
        {"number": "87", "description": "I broke into houses"},
        {"number": "88", "description": "Told Randy he would (land?) if he jumped"},
        {"number": "88", "description": "Left cigarette ..."},
        {"number": "89", "description": "Broke into a house, had a party and didn't clean up"},
        {"number": "91", "description": "Made fun of Maggie Lester for having a moustache"},
        {"number": "98", "description": "Told Dodge & Earl Jr. we would have a father/son day at Mystery Fun Land and didn't take them"},
        {"number": "102", "description": "Harmed and possibly killed innocent people by second-hand smoke"},
        {"number": "107", "description": "Put bleach in ... laundry detergent"},
        {"number": "108", "description": "Lost Dad's Mustang"},
        {"number": "109", "description": "Fixed wiring so neighbors (nosy ones) didn't have power for a week"},
        {"number": "111", "description": "Accidentally broke Tom's Toe"},
        {"number": "111", "description": "Ruined Joy's chili"},
        {"number": "112", "description": "Let Donny Jones serve jail time for a crime I committed"},
        {"number": "116", "description": "Parked in a handicapped spot"},
        {"number": "117", "description": "Killed cat trying to see if it would land on its feet"},
        {"number": "119", "description": "Ruined Joy's chance to get into art school"},
        {"number": "126", "description": "Helped myself to the tip jar at Crab Shack"},
        {"number": "127", "description": "Stole a badge from a police officer"},
        {"number": "136", "description": "I've been a litterbug"},
        {"number": "139", "description": "Stole beer from a golfer"},
        {"number": "140", "description": "Took ... pickup ..."},
        {"number": "140", "description": "Forgot ... pick up ... school"},
        {"number": "142", "description": "Had egg fight down a main street"},
        {"number": "143", "description": "Farted in Joy's Face"},
        {"number": "144", "description": "Pulled whiskers from Randy's chin"},
        {"number": "145", "description": "Dumped Jessie to marry Joy"},
        {"number": "146", "description": "Puked in drum set"},
        {"number": "147", "description": "Had egg fight down a main street"},
        {"number": "147", "description": "Shot Gwen Waters in the ass with a BB"},
        {"number": "147", "description": "Forgot to pick up kids at school"},
        {"number": "148", "description": "Accidentally neutered Joy's breeding dog"},
        {"number": "149", "description": "Screwed up Joy's baby parts"},
        {"number": "150", "description": "Fix Randy"},
        {"number": "151", "description": "Beat up Joy's nitpicking Internet friend"},
        {"number": "152", "description": "Told Joy Bruce Willis was a ghost"},
        {"number": "153", "description": "Broke Joy's fancy figurine"},
        {"number": "154", "description": "Gave Joy a tape worm"},
        {"number": "154", "description": "Put sugar in Ray's gas tank"},
        {"number": "155", "description": "Sold Joy's hair"},
        {"number": "156", "description": "Told Joy Dan Dodd messed himself on the golf course"},
        {"number": "157", "description": "Gave Joy 236 bladder infections"},
        {"number": "157", "description": "Aimed and set off bottle rockets at Randy when he was on a date"},
        {"number": "158", "description": "Made Randy steal electronics and got caught"},
        {"number": "159", "description": "Stole P's HD Cart"},
        {"number": "160", "description": "Set off bottle rockets at Randy with Ralph"},
        {"number": "164", "description": "Burned down a barn at the Right Choice Ranch"},
        {"number": "171", "description": "Went to Sex Anonymous support group to pick up girls"},
        {"number": "174", "description": "Ruined Dodge's Career Day"},
        {"number": "183", "description": "Never took Joy's side"},
        {"number": "186", "description": "Was mean to the Crazy Witch Lady."},
        {"number": "188", "description": "Slept with Linda (Unknown) who was married"},
        {"number": "202", "description": "Stole a wallet from a guy at a gas station"},
        {"number": "203", "description": "Stole various snacks and drinks from a local quick stop"},
        {"number": "204", "description": "Seduced seven virgins"},
        {"number": "205", "description": "Gave Joy's car a dent, said it was a hit and run"},
        {"number": "206", "description": "Refused to dance with Too-Tall Maggie at the eighth grade dance"},
        {"number": "207", "description": "I've been wasteful"},
        {"number": "213", "description": "Never let Randy have anything better than me"},
        {"number": "239", "description": "Made a kid scared of the boogeyman"},
        {"number": "241", "description": "Made Derek Stone late for work"},
        {"number": "258", "description": "Took Donny away from his mother for for 2 years"},
        {"number": "259", "description": "Took Randy's one touchdown"},
        {"number": "260", "description": "Neglected Randy"},
        {"number": "260", "description": "Neglected Randy"},
        {"number": "261", "description": "Ruined Joy's wedding"},
        {"number": "262", "description": "Slept with Crab Man's fiancée"},
        {"number": "263", "description": "Broke bus stop while looking for Poncho the blue fish"},
        {"number": "264", "description": "Punched college student"},
        {"number": "265", "description": "Punch Tom in gut"},
        {"number": "265", "description": "Didn't pay taxes"},
        {"number": "266", "description": "Never gave Mom a good Mother's Day"},
        {"number": "267", "description": "Lost my own car because I'm an idiot"},
        {"number": "269", "description": "Got Catalina deported"},
        {"number": "270", "description": "Kept a guy locked in a truck"},
        {"number": "273", "description": "Kept myself from being an adult"},
        {"number": "277", "description": "Broke up Randy & Pinky"}
    ]
    ds = DictSet(data, storage_class=STORAGE_CLASS.MEMORY)

    rel = Relation()
    rel.from_dictset(ds)


    print(sys.getsizeof(rel))
    print(sys.getsizeof(ds))

    from mabel.utils.timer import Timer

    with Timer("rel"):
        for i in range(1000):
            r = rel.apply_selection(lambda x: x[0] == "270")

    with Timer("ds"):
        for i in range(1000):
            d = ds.select(lambda x: x["number"] == "270")
