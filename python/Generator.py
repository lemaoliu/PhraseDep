from nltk import Tree
from copy import deepcopy
import sys
import NewTree
import argparse
import os
import re
import sys

parser = argparse.ArgumentParser(description='')
parser.add_argument('gr_or_gp', type=int, metavar='',help='Generate Rules -- 0, Generate Parts -- 1, generate from conll -- 2')
parser.add_argument('--inputf', type=str, metavar='', help='')
parser.add_argument('--rulef', type=str, metavar='', help='')
# parser.add_argument('--rulef', required=False, type=str, metavar='', help='')
# parser.add_argument('--rulef', action='store_true', help='')

A = parser.parse_args()

unary_collapse = False

def generate_rule(treebank_file):
    # if you use unicode here, there is a bug...
    f = open(treebank_file, "r")
    full_rule_set = set([])
    s_ind = 0
    for sentence in f:
        s_ind += 1
        if s_ind % 10 == 0:
            sys.stderr.write(str(s_ind) + "\n")
            sys.stderr.write(str(len(full_rule_set)) + "\n")
        t = Tree.fromstring(sentence, remove_empty_top_bracketing=False)
        # sys.stderr.write(t.pprint())
        # First, collapse the unary, notice that the POS tags should not be affected
        if unary_collapse:
            NewTree.collapse_unary(t)
        bt = NewTree.get_binarize_lex(t)
        # Extract rules from the tree
        rule_set = NewTree.generate_rules(bt)
        #sys.stderr.write("1:\t" + str(len(rule_set)) + "\n")

        # Add them to the full set
        #sys.stderr.write( "start adding\n")
        for sr in rule_set:
            # sys.stderr.write(sr + "\n")
            full_rule_set.add(sr)
        #sys.stderr.write("2:\t" + str(len(full_rule_set)) + "\n")
        #sys.stderr.write( "finish adding\n")

    f.close()
    ind = 0
    for r in full_rule_set:
        print str(ind) + " " + r
        ind += 1


def generate_part(treebank_file, rule_file):
    # This generate the gold parts file for the use of C++
    rule_dic = read_rule_file(rule_file)
    f = open(treebank_file, "r")
    s_ind = 0
    for sentence in f:
        s_ind += 1
        if s_ind % 10 == 0:
            sys.stderr.write(str(s_ind) + "\n")
        parts = []
        t = Tree.fromstring(sentence, remove_empty_top_bracketing=False)
        if unary_collapse:
            NewTree.collapse_unary(t)
        bt = NewTree.get_binarize_lex(t)
        for pos in bt.treepositions(order='postorder'):
            nt = bt[pos]
            if isinstance(nt, str):
                continue
            elif nt.height() == 2:
                continue
            else:
                #print rule_dic
                info = NewTree.get_span_info(nt,rule_dic)
                parts.append(info)

        work_tree = deepcopy(t)
        NewTree.lexLabel(work_tree)
        parent_dic = NewTree.getParentDic(work_tree)

        print len(t.leaves()), len(parts)
        print " ".join(t.leaves())
        print " ".join([x.label() for x in t.subtrees(lambda t: t.height() == 2)])
        parent_list = []
        for ind in xrange(1, (len(t.leaves()) + 1)):
            p = str(int(parent_dic[str(ind)]) - 1)
            parent_list.append(p)
        print " ".join(parent_list)
        for p in parts:
            print " ".join(p)
    f.close()

def read_rule_file(rulef):
    rule_dic = {}
    f = open(rulef, "r")
    for line in f:
        l = line.split(' ', 1)
        #print l[1].strip()
        rule_dic[l[1].strip()] = l[0]
    f.close()
    return rule_dic

def read_corpus(filename):
    f = open(filename, "r")
    corpus = []
    sentence = []
    for line in f:
        if line.strip() == "":
            corpus.append(sentence)
            sentence = []
            continue
        else:
            line = line.strip()
            cline = line.split("\t")
            sentence.append(cline)
    f.close()
    return corpus

def generate_from_conll(inputf):
    corpus = read_corpus(inputf)
    for sentence in corpus:
        word_list = [line[1] for line in sentence]
        pos_list = [line[4] for line in sentence]
        parent_list = [str(int(line[6])-1) for line in sentence]
        # print " ".join(word_list)
        print len(word_list), '0'
        print " ".join(word_list)
        print " ".join(pos_list)
        print " ".join(parent_list)




if __name__ == '__main__':
    # sentence = """(S (NP (NP (JJ Influential) (NNS members)) (PP (IN of) (NP (DT the) (NNP House) (NNP Ways) (CC and) (NNP Means) (NNP Committee)))) (VP (VBD introduced) (NP (NP (NN legislation)) (SBAR (WHNP (WDT that)) (S (VP (MD would) (VP (VB restrict) (SBAR (WHADVP (WRB how)) (S (NP (DT the) (JJ new) (NN savings-and-loan) (NN bailout) (NN agency)) (VP (MD can) (VP (VB raise) (NP (NN capital)))))) (, ,) (S (VP (VBG creating) (NP (NP (DT another) (JJ potential) (NN obstacle)) (PP (TO to) (NP (NP (NP (DT the) (NN government) (POS 's)) (NN sale)) (PP (IN of) (NP (JJ sick) (NNS thrifts)))))))))))))) (. .))"""
    # t = Tree.fromstring(sentence, remove_empty_top_bracketing=False)
    # for pos in t.treepositions(order='postorder'):
    #     print t[pos]
    if A.gr_or_gp == 0:
        generate_rule(A.inputf)
    elif A.gr_or_gp == 1:
        generate_part(A.inputf,A.rulef)
    else:
        generate_from_conll(A.inputf)
