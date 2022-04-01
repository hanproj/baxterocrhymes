# CLDF dataset derived from Baxter's "Old Chinese Reconstruction" from 1992

## How to prepare data

```
$ pip install -e .
$ cldfbench download cldfbench_baxterocrhymes.py
```

To make the CLDF, run:
```
$ cldfbench makecldf cldfbench_baxterocrhymes.py
```

## How to construct a rhyme network

```python
from cldfbench_baxterocrhymes import Dataset as Baxter
from pycldf import Dataset
import networkx as nx
from collections import defaultdict
import itertools

ds = Dataset.from_metadata(Baxter().cldf_dir / "cldf-metadata.json"))
G = nx.Graph()
nodes = defaultdict(list)
for row in ds.objects("ExampleTable"):
    for char, rid in zip(row.data["Rhyme_Words"], row.data["Rhyme_IDS"]):
        if char in G:
            G.nodes[char]["occurrence"] += 1
        else:
            G.add_node(char, occurrence=1)
        nodes[rid] += [char]
for rid, chars in nodes.items():
    for charA, charB in itertools.combinations(chars, r=2):
        try:
            G[charA][charB]["weight"] += 1
        except:
            G.add_edge(charA, charB, weight=1)
```
