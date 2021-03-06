#!/usr/bin/python


import re
import sys
from operator import add
from pyspark import SparkContext


def computeContribs(urls, rank):
    """Calculates URL contributions to the rank of other URLs."""
    num_urls = len(urls)
    for url in urls:
        yield (url, rank / num_urls)


def parseNeighbors(urls):
    """Parses a urls pair string into urls pair."""
    parts = re.split(r',', urls)
    return parts[0], parts[1]


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print >> sys.stderr, "Usage: pagerank <HDFS Input file> <iterations>"
        exit(-1)

    # Initialize the spark context.
    sc = SparkContext(appName="PythonPageRank")

    # Loads in input file. It should be in format(comma seperated) of:
    #     URL,neighbor URL
    #     URL,neighbor URL
    #     URL,neighbor URL
    #     ...
    lines = sc.textFile(sys.argv[1], 1)

    # Loads all URLs from input file and initialize their neighbors.
    links = lines.map(lambda urls: parseNeighbors(urls)).distinct().groupByKey().cache()

    # Loads all URLs with other URL(s) link to from input file and initialize ranks of them to one.
    ranks = links.map(lambda (url, neighbors): (url, 1.0))

    # Calculates and updates URL ranks continuously using PageRank algorithm.
    for iteration in xrange(int(sys.argv[2])):
        # Calculates URL contributions to the rank of other URLs.
        contribs = links.join(ranks).flatMap(
            lambda (url, (urls, rank)): computeContribs(urls, rank))

        # Re-calculates URL ranks based on neighbor contributions.
        ranks = contribs.reduceByKey(add).mapValues(lambda rank: rank * 0.85 + 0.15)

    # Collects all URL ranks and dump them to console.
    for (link, rank) in ranks.collect():
        print "%s has rank: %s." % (link, rank)
