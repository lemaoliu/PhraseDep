from nltk import Tree
from copy import deepcopy
import sys
import NewTree
import argparse
import os
import re
import sys
import codecs

parser = argparse.ArgumentParser(description='')
parser.add_argument('gr_or_gp', type=int, metavar='',help='Generate Rules -- 0, Generate Parts -- 1, generate from conll -- 2')
parser.add_argument('--inputf', type=str, metavar='', help='')
parser.add_argument('--rulef', type=str, metavar='', help='')
parser.add_argument('--hm', type=int, metavar='', help='')
parser.add_argument('--vm', type=int, metavar='', help='')
parser.add_argument('--unary_collapse', action='store_true', help='')
parser.add_argument('--language', type=str, metavar='', help='')
parser.add_argument('--backoff_rule',action='store_true',help='')

parser.add_argument('--dep_from_conll', action='store_true', help='')
parser.add_argument('--conll_dep_file', type=str, metavar='', help='')

# parser.add_argument('--rulef', required=False, type=str, metavar='', help='')
# parser.add_argument('--rulef', action='store_true', help='')

A = parser.parse_args()

use_back_off_rule = A.backoff_rule
unary_collapse = A.unary_collapse
language_setting = A.language
dep_from_conll = A.dep_from_conll

def generate_rule(treebank_file):
    # if you use unicode here, there is a bug...
    f = open(treebank_file, "r")
    pos_set = set([])
    nt_set = set([])
    full_rule_set = set([])
    s_ind = 0
    for sentence in f:
        if language_setting == "chn":
            sentence = sentence.decode('utf-8')
        s_ind += 1
        if s_ind % 10 == 0:
            sys.stderr.write("Sentence:\t" + str(s_ind) + "\n")
            sys.stderr.write("Rule number:\t" + str(len(full_rule_set)) + "\n")
        tree = Tree.fromstring(sentence, remove_empty_top_bracketing=False)
        preterminals = [t.label() for t in tree.subtrees(lambda t: t.height() == 2)]
        pos_set.update(preterminals)

        # sys.stderr.write(t.pprint())
        # First, collapse the unary, notice that the POS tags should not be affected
        if unary_collapse:
            NewTree.collapse_unary(tree)
        bt = NewTree.get_binarize_lex(tree)
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
    #core_pos_set = [pos for pos in pos_set if pos[0] <= 'Z' and pos[0] >= 'A']
    
    # print core_pos_set
    # Generate the back-off rules
    backoff_rule_set = set([])
    for r in full_rule_set:
        args = r.split(" ")
    #   #print "___".join(args)
        nt_set.add(args[1])
        #print args[1]
        for i in xrange(1, len(args)-1):
    #        #sys.stdout.write("*" + args[i] + "*")
            if args[i] in pos_set:
    #            # change the pos to others
    #            #print "for rule " + " ".join(args)
    #            for pos in core_pos_set:
                args_copy = deepcopy(args)
                args_copy[i] = "BPOS|"
    #                if (" ".join(args_copy)) not in full_rule_set:
                backoff_rule_set.add(" ".join(args_copy))
    #                #print "\tadding: " + " ".join(args_copy)
    #    #sys.stdout.write("\n")


    ind = 0
    for r in full_rule_set:
        print str(ind) + " " + r
        ind += 1
    if use_back_off_rule:
        for r in backoff_rule_set:
            print str(ind) + " " + r
            ind += 1
        for pos in pos_set:
            print str(ind) + " 1 BPOS| " + pos
            ind += 1
        # for nt in nt_set:
        #     print str(ind) + " 0 "+ nt +" BPOS| BPOS| 0"
        #     ind += 1
        #     print str(ind) + " 0 "+ nt +" BPOS| BPOS| 1"
        #     ind += 1


def generate_part(treebank_file, rule_file):
    # This generate the gold parts file for the use of C++
    rule_dic = read_rule_file(rule_file)
    f = open(treebank_file, "r")
    s_ind = -1
    corpus = []
    if dep_from_conll:
        corpus = read_corpus(A.conll_dep_file)
    for sentence in f:
        if language_setting == "chn":
            sentence = sentence.decode('utf-8')
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
            if isinstance(nt, str) or isinstance(nt, unicode):
                continue
            elif nt.height() == 2:
                continue
            else:
                #print rule_dic
                info = NewTree.get_span_info(nt,rule_dic)
                parts.append(info)

        work_tree = deepcopy(t)
        NewTree.lexLabel(work_tree)
        parent_dic, dep_label_set = NewTree.getParentDic(work_tree)
        print len(t.leaves()), len([item for item in parts if item != None])
        print " ".join(t.leaves())
        if not dep_from_conll:
            print " ".join([x.label() for x in t.subtrees(lambda t: t.height() == 2)])
            parent_list = []
            label_list = []
            for ind in xrange(1, (len(t.leaves()) + 1)):
                p = str(int(parent_dic[str(ind)]) - 1)
                parent_list.append(p)
            print " ".join(parent_list)
            for ind in xrange(1, (len(t.leaves()) + 1)):
                l = dep_label_set[str(ind)]
                label_list.append(l)
            print " ".join(label_list)
        else:
            dep_sentence = corpus[s_ind]
            if language_setting == "chn":
                dep_sentence = dep_sentence.decode('utf-8')
            pos_list = [line[4] for line in dep_sentence]
            parent_list = [str(int(line[6])-1) for line in dep_sentence]
            label_list = [line[7] for line in dep_sentence]
            # print " ".join(word_list)
            print " ".join(pos_list)
            print " ".join(parent_list)
            print " ".join(label_list)
        for p in parts:
            if p != None:
                print " ".join(p)
            else:
                pass
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
        if language_setting == "chn":
            line = line.decode('utf-8')
        if line[:-1] == "":
            corpus.append(sentence)
            sentence = []
            continue
        else:
            line = line[:-1]
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
        label_list = [line[7] for line in sentence]
        # print " ".join(word_list)
        print len(word_list), '0'
        print " ".join(word_list)
        print " ".join(pos_list)
        print " ".join(parent_list)
        print " ".join(label_list)

def generate_conll(inputf):
    f = open(inputf, "r")
    s_ind = 0
    for sentence in f:
        if language_setting == "chn":
            sentence = sentence.decode('utf-8')
        s_ind += 1
        if s_ind % 10 == 0:
            sys.stderr.write("Sentence:\t" + str(s_ind) + "\n")
        t = Tree.fromstring(sentence, remove_empty_top_bracketing=False)
        deps = NewTree.generateDep(t)
        NewTree.print_conll_lines(deps,sys.stdout)
        sys.stdout.write("\n")
    f.close()


if __name__ == '__main__':
    # sentence = """(S (NP (NP (JJ Influential) (NNS members)) (PP (IN of) (NP (DT the) (NNP House) (NNP Ways) (CC and) (NNP Means) (NNP Committee)))) (VP (VBD introduced) (NP (NP (NN legislation)) (SBAR (WHNP (WDT that)) (S (VP (MD would) (VP (VB restrict) (SBAR (WHADVP (WRB how)) (S (NP (DT the) (JJ new) (NN savings-and-loan) (NN bailout) (NN agency)) (VP (MD can) (VP (VB raise) (NP (NN capital)))))) (, ,) (S (VP (VBG creating) (NP (NP (DT another) (JJ potential) (NN obstacle)) (PP (TO to) (NP (NP (NP (DT the) (NN government) (POS 's)) (NN sale)) (PP (IN of) (NP (JJ sick) (NNS thrifts)))))))))))))) (. .))"""
    # t = Tree.fromstring(sentence, remove_empty_top_bracketing=False)
    # for pos in t.treepositions(order='postorder'):
    #     print t[pos]


    NewTree.HORZMARKOV = A.hm
    NewTree.VERTMARKOV = A.vm

    # NewTree.init_rules_stanford()
    # print NewTree.dic_head_rules

    if A.language == "chn":
        NewTree.LANGUAGE = "chn"
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr)
    else:
        NewTree.LANGUAGE = "eng"

    if A.gr_or_gp == 0:
        generate_rule(A.inputf)
    elif A.gr_or_gp == 1:
        generate_part(A.inputf,A.rulef)
    elif A.gr_or_gp == 2:
        generate_from_conll(A.inputf)
    else:
        generate_conll(A.inputf)
