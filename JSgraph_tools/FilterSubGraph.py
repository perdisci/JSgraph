##
# Copyright (C) 2018 University of Georgia. All rights reserved.
#
# This file is subject to the terms and conditions defined at
# https://github.com/perdisci/JSgraph/blob/master/LICENSE.txt
#
##

import sys

fontsize = 'node[margin="0,0"];'


def read_file(filename):
    f = open(filename, "r")
    lines = f.readlines()
    f.close()
    return lines[1:-1]


def get_node_pair(line):
    if is_edge(line):
        return (line.split("->")[0].strip(),
                line.split("->")[1].split("[")[0].split(";")[0].strip())


def get_node(line):
    if not is_edge(line):
        return line.split(";")[0].split(" [label=")[0].strip()


def is_edge(line):
    return len(line.split("->")) >= 2


def find_descendants(node_id, lines, ignored_node_ids=[]):
    # return_list=[]
    # return_list.append(node_id)
    return_list = list(node_id)
    i = 0
    while i < len(lines):
        line = lines[i]
        if is_edge(line):
            parent_node, self_node = get_node_pair(line)
            if (parent_node in return_list and
                    self_node not in ignored_node_ids):
                return_list.append(self_node)
        i += 1
    return return_list


def find_ancestors(node_id, lines, ignored_node_ids=[]):
    # return_list=[]
    # return_list.append(node_id)
    return_list = list(node_id)
    i = len(lines)-1
    while i >= 0:
        line = lines[i]
        if is_edge(line):
            parent_node, self_node = get_node_pair(line)
            if (self_node in return_list and
                    parent_node not in ignored_node_ids):
                return_list.append(parent_node)
        i -= 1
    return return_list


def output_node_or_edge(i, lines):
    line = lines[i]
    print line[:-1]
    i += 1
    if i >= len(lines):
        return i-1
    line = lines[i]
    while (not line.startswith("Node_")):
        print line[:-1]
        i += 1
        if i < len(lines):
            line = lines[i]
        else:
            break
    return i-1


def judge_and_output_highlight_style(node_id, highted_node_ids):
    if node_id in highted_node_ids:
        print node_id, '[penwidth=2, color=red]'


def out_put_filter_lines(ancestors, descendants, lines, highted_node_ids=[]):
    print "digraph G {"
    print fontsize
    i = 0
    while i < len(lines):
        line = lines[i]
        if is_edge(line):
            parent_node, self_node = get_node_pair(line)
            if parent_node in descendants or self_node in ancestors:
                i = output_node_or_edge(i, lines)

        else:
            self_node = get_node(line)
            if self_node in descendants or self_node in ancestors:
                i = output_node_or_edge(i, lines)
                if self_node in highted_node_ids:
                    judge_and_output_highlight_style(self_node,
                                                     highted_node_ids)
        i += 1
    print "}"


def out_put_filter_lines_descendants(descendants, lines, highted_node_ids=[]):
    print "digraph G {"
    print fontsize
    i = 0
    while i < len(lines):
        line = lines[i]
        if is_edge(line):
            parent_node, self_node = get_node_pair(line)
            if parent_node in descendants and self_node in descendants:
                i = output_node_or_edge(i, lines)

        else:
            self_node = get_node(line)
            if self_node in descendants:
                i = output_node_or_edge(i, lines)
                if self_node in highted_node_ids:
                    judge_and_output_highlight_style(self_node,
                                                     highted_node_ids)
        i += 1
    print "}"


def out_put_filter_lines_ancestors(ancestors, lines, highted_node_ids=[]):
    print "digraph G {"
    print fontsize
    i = 0
    while i < len(lines):
        line = lines[i]
        if is_edge(line):
            parent_node, self_node = get_node_pair(line)
            if self_node in ancestors and parent_node in ancestors:
                i = output_node_or_edge(i, lines)

        else:
            self_node = get_node(line)
            if self_node in ancestors:
                i = output_node_or_edge(i, lines)
                if self_node in highted_node_ids:
                    judge_and_output_highlight_style(self_node,
                                                     highted_node_ids)
        i += 1
    print "}"


def filter_node_id(filename, node_id, method, ignored_node_ids=[],
                   highted_node_ids=[]):
    lines = read_file(filename)
    ignored_node_ids_descendants = find_descendants(ignored_node_ids, lines)
    descendants = find_descendants(node_id, lines,
                                   ignored_node_ids_descendants)
    ancestors = find_ancestors(node_id, lines, ignored_node_ids)
    # print descendants
    # print ancestors
    if method == 'B':
        out_put_filter_lines(ancestors, descendants, lines, highted_node_ids)
    elif method == 'A':
        out_put_filter_lines_ancestors(ancestors, lines, highted_node_ids)
    elif method == 'D':
        out_put_filter_lines_descendants(descendants, lines, highted_node_ids)


def main():
    ignored_node_ids = []
    highted_node_ids = []
    node_ids = [a.strip() for a in sys.argv[2].split(',')]
    if len(sys.argv) >= 5:
        highted_node_ids = [a.strip() for a in sys.argv[4].split(',')]
    if len(sys.argv) >= 6:
        ignored_node_ids = [a.strip() for a in sys.argv[5].split(',')]
        # print ignored_node_ids
    filter_node_id(sys.argv[1], node_ids, sys.argv[3], ignored_node_ids,
                   highted_node_ids)


if __name__ == '__main__':
    main()
