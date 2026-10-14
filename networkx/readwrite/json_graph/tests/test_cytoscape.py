import copy
import json

import pytest

import networkx as nx
from networkx.readwrite.json_graph import cytoscape_data, cytoscape_graph


def test_graph():
    G = nx.path_graph(4)
    H = cytoscape_graph(cytoscape_data(G))
    assert nx.is_isomorphic(G, H)


def test_input_data_is_not_modified_when_building_graph():
    G = nx.path_graph(4)
    input_data = cytoscape_data(G)
    orig_data = copy.deepcopy(input_data)
    # Ensure input is unmodified by cytoscape_graph (gh-4173)
    cytoscape_graph(input_data)
    assert input_data == orig_data


def test_graph_attributes():
    G = nx.path_graph(4)
    G.add_node(1, color="red")
    G.add_edge(1, 2, width=7)
    G.graph["foo"] = "bar"
    G.graph[1] = "one"
    G.add_node(3, name="node", id="123")

    H = cytoscape_graph(cytoscape_data(G))
    assert H.graph["foo"] == "bar"
    assert H.nodes[1]["color"] == "red"
    assert H[1][2]["width"] == 7
    assert H.nodes[3]["name"] == "node"
    assert H.nodes[3]["id"] == "123"

    d = json.dumps(cytoscape_data(G))
    H = cytoscape_graph(json.loads(d))
    assert H.graph["foo"] == "bar"
    assert H.graph[1] == "one"
    assert H.nodes[1]["color"] == "red"
    assert H[1][2]["width"] == 7
    assert H.nodes[3]["name"] == "node"
    assert H.nodes[3]["id"] == "123"


def test_digraph():
    G = nx.DiGraph()
    nx.add_path(G, [1, 2, 3])
    H = cytoscape_graph(cytoscape_data(G))
    assert H.is_directed()
    assert nx.is_isomorphic(G, H)


def test_multidigraph():
    G = nx.MultiDiGraph()
    nx.add_path(G, [1, 2, 3])
    H = cytoscape_graph(cytoscape_data(G))
    assert H.is_directed()
    assert H.is_multigraph()


def test_multigraph():
    G = nx.MultiGraph()
    G.add_edge(1, 2, key="first")
    G.add_edge(1, 2, key="second", color="blue")
    H = cytoscape_graph(cytoscape_data(G))
    assert nx.is_isomorphic(G, H)
    assert H[1][2]["second"]["color"] == "blue"


def test_exception():
    with pytest.raises(nx.NetworkXError):
        G = nx.MultiDiGraph()
        cytoscape_data(G, name="foo", ident="foo")


@pytest.mark.parametrize(
    "graph_type", [nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph]
)
def test_tuple_node_identifiers(graph_type):
    G = graph_type()
    first = ("a", ("b", "c"))
    second = ("b", ("c", "d"))
    G.add_edge(first, second, weight=7)
    G.nodes[first]["id"] = "first-node"

    data = json.loads(json.dumps(cytoscape_data(G)))
    ids = {node["data"]["id"] for node in data["elements"]["nodes"]}
    for edge in data["elements"]["edges"]:
        assert edge["data"]["source"] in ids
        assert edge["data"]["target"] in ids

    H = cytoscape_graph(data)
    assert set(H) == set(G)
    assert H.has_edge(first, second)
    if G.is_multigraph():
        assert H[first][second][0]["weight"] == 7
    else:
        assert H[first][second]["weight"] == 7


def test_custom_identifiers_with_legacy_endpoints():
    G = nx.path_graph(2)
    G.nodes[0]["custom_id"] = "first"
    G.nodes[1]["custom_id"] = "second"
    data = cytoscape_data(G, ident="custom_id")
    edge = data["elements"]["edges"][0]["data"]
    assert edge["source"] == "first"
    assert edge["target"] == "second"
    assert set(cytoscape_graph(data, ident="custom_id")) == set(G)

    # Keep accepting the node-value endpoints produced by earlier releases.
    edge["source"], edge["target"] = 0, 1
    assert set(cytoscape_graph(data, ident="custom_id")) == set(G)
