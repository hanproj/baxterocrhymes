from collections import ChainMap
from itertools import chain
import pathlib
import re
import sys
from clldutils.misc import slug
from collections import defaultdict

from cldfbench import CLDFSpec, Dataset as BaseDataset


# function is also in sinopy, for convenience reused here
def is_chinese(name):
    """
    Check if a symbol is a Chinese character.

    Note
    ----

    Taken from http://stackoverflow.com/questions/16441633/python-2-7-test-if-characters-in-a-string-are-all-chinese-characters
    """
    if not name:
        return False
    for ch in name:
        ordch = ord(ch)
        if not (0x3400 <= ordch <= 0x9fff) and not (0x20000 <= ordch <= 0x2ceaf) \
                and not (0xf900 <= ordch <= ordch) and not (0x2f800 <= ordch <= 0x2fa1f): 
                return False
    return True


def parse_line(line):
    phrases = line.split("、")
    out = []
    for phrase in phrases:
        chars = []
        rhymes = []
        rhyme = ""
        for char in phrase:
            if char in "abcdefghijklmnopqrstuvw" and char != "x":
                rhyme = char
            elif is_chinese(char):
                chars += [char]
                rhymes += [rhyme]
                rhyme = ""
        rhyme_words, rhyme_word_idxs, rhyme_idxs = [], [], []
        for i, (char, rhyme) in enumerate(zip(chars, rhymes)):
            if rhyme:
                rhyme_words += [char]
                rhyme_word_idxs += [str(i+1)]
                rhyme_idxs += [rhyme]
        out += [[
            phrase, chars, rhyme_words, rhyme_word_idxs,
            rhyme_idxs]]
                
    return out


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "baxterocrhymes"

    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        return CLDFSpec(
                dir=self.cldf_dir, module='Generic',
                metadata_fname='cldf-metadata.json'
                )

        
    def cmd_download(self, args):
        """
        Download files to the raw/ directory. You can use helpers methods of `self.raw_dir`, e.g.

        >>> self.raw_dir.download(url, fname)
        """
        self.raw_dir.download(
                "https://github.com/digling/shijing/raw/v1.0/S_shijing_rhymes.corrected.txt",
                "S_shijing_rhymes.corrected.txt"
                )

        
    def cmd_makecldf(self, args):
        """
        Convert the raw data to a CLDF dataset.
        """

        args.writer.cldf.add_component('LanguageTable')
        args.writer.cldf.add_component(
            'ExampleTable',
            'Poem_ID',
            {"name": "Entry_IDS", "datatype": "string", "separator": " "},
            {'name': 'Stanza_Number', 'datatype': 'integer'},
            {'name': 'Line_Number', 'datatype': 'integer'},
            {"name": "Phrase_Number", "datatype": "integer"},
            {"name": "Rhyme_Words", "datatype": "string", "separator": " "},
            {"name": "Rhyme_Word_Indices", "datatype": "string", "separator": " "},
            {"name": "Rhyme_IDS", "datatype": "string", "separator": " "},
        )
        args.writer.cldf.add_component(
            "EntryTable",
            "MiddleChinese",
            "OCBS",
            {"name": "Example_IDS", "datatype": "string", "separator": " "},
            )

        args.writer.cldf.add_table('poems.csv', 'ID', 'Title')
        args.writer.cldf.add_foreign_key(
                'ExampleTable', 'Poem_ID', 'poems.csv', 'ID'
                )
        args.writer.cldf.add_foreign_key(
                "EntryTable", "Example_IDS", "examples.csv", "ID")
        
        args.writer.objects['LanguageTable'].append(
                {
                    'ID': 'OldChinese', 
                    'Name': 'Old Chinese', 
                    'Glottocode': ''}
                )
    
        P = {}
        with open(self.raw_dir / "S_shijing_rhymes.corrected.txt") as f:
            poems_ = f.read().split("\n\n\n\n")
            for poem in poems_:
                in_poem = False
                for row in poem.split("\n"):
                    if row.startswith("?"):
                        pass

                    elif row.strip() and row[0].isdigit():
                        name = row
                        in_poem = True
                        stanza = 1
                        P[name] = {stanza: []}
                    elif in_poem:
                        if row.strip():
                            P[name][stanza] += [row.strip()]
                        else:
                            stanza += 1
                            P[name][stanza] = []
        args.log.info("parsed data")
        
        poems = {}
        idx = 1
        entries = defaultdict(list)
        for i, name in enumerate(P):
            poem_id, poem_name = name.split(". ")
            args.writer.objects["poems.csv"].append({
                "ID": poem_id,
                "Title": poem_name,
                })
            args.log.info("Analyzing poem {0} / {1}".format(i+1, name))
            for stanza in P[name]:
                for i, row in enumerate(P[name][stanza]):
                    for j, (
                            phrase, chars, rhyme_words, rhyme_word_idxs,
                            rhyme_idxs
                            ) in enumerate(parse_line(row)):
                        for word in rhyme_words:
                            entries[word] += [idx]
                        args.writer.objects["ExampleTable"].append({
                            "ID": idx,
                            "Primary_Text": phrase,
                            "Analyzed_Word": chars,
                            "Gloss": "",
                            "Poem_ID": poem_id,
                            "Stanza_Number": stanza,
                            "Line_Number": i+1,
                            "Phrase_Number": j+1,
                            "Language_ID": "OldChinese",
                            "Rhyme_Words": rhyme_words,
                            "Rhyme_Word_Indices": rhyme_word_idxs ,
                            "Rhyme_IDS": ["{0}-{1}-{2}".format(
                                poem_id, stanza, rid) for rid in rhyme_idxs]
                            })
                        idx += 1
        for i, (entry, occs) in enumerate(entries.items()):
            args.writer.objects["EntryTable"].append({
                "ID": i+1,
                "Language_ID": "OldChinese",
                "Headword": entry,
                "Example_IDS": occs
                })



        # output

        #args.writer.cldf.properties['dc:creator'] = "Johann-Mattis List" 

        #language = {
        #    'ID': "OldChinese",
        #    'Name': "Old Chinese",
        #    'Glottocode': "",
        #}
        #args.writer.objects['LanguageTable'] = [language]

        #args.writer.objects['EntryTable'] = entries
        #args.writer.objects['SenseTable'] = senses
        #args.writer.objects['ExampleTable'] = examples
        #args.writer.objects['media.csv'] = media
