from collections import defaultdict, namedtuple
import pydecode.model
import pydecode.nlp
import nltk
import itertools
import numpy as np
import lex

ParseInput = namedtuple("ParseInput", ["words", "tags", "deps", "index"])

class ReconstructionModel(pydecode.model.DynamicProgrammingModel):

    def loss(self, y, yhat):
        a = y.treepositions()
        b = yhat.treepositions()
        count = len([i for i in a if i in b])
             
        return count / float(len(a))

    def max_loss(self, y):
        return 1.0

    def set_grammar(self, grammar):
        self.grammar = grammar

    def set_from_disk(self, path):
        self.path = path

    def initialize(self, X, Y):
        self.bins = [1, 2, 3, 5, 8, 20, 40]

        # Preprocessor
        self.preprocessor = pydecode.model.Preprocessor()
        for x in X:
            for word, tag in zip(x.words, x.tags):
                self.preprocessor.add(self._preprocess_word(word, tag))
            self.preprocessor.add(self._preprocess_word("*END*", "*END*"))
        super(ReconstructionModel, self).initialize(X, Y)

    def _preprocess_word(self, word, tag):
        return {"WORD": word, "TAG": tag}

    def _preprocess(self, x):
        if ("PP", x) in self.cache:
            return self.cache["PP", x]
        else:
            p = self.preprocessor.transform(
                [self._preprocess_word(word, tag)
                 for word, tag in zip(x.words, x.tags)] \
                    + [self._preprocess_word("*END*", "*END*")])
            self.cache["PP", x] = p
        return p

    def dynamic_program(self, x):
        sentence = [self.grammar.nonterms[tag]
                    for tag in x.tags]

        if self.path and x.index:
            graph = pydecode.load(self.path + "graphs%s.graph"%x.index)
            
            encoder = lex.LexicalizedCFGEncoder(sentence, self.grammar)
            encoder.load(self.path + "encoder%s.pickle"%x.index)
            return graph, encoder
        else:
            #mod_of = lex.make_mod(x.words, x.deps)
            return lex.cky(sentence, self.grammar, x.deps)

    def parts_features(self, x, parts):
        p = self._preprocess(x)
        o = parts

        # Parts are of the following form.
        POS_i = 0
        POS_j = 1
        POS_k = 2
        HEAD = 3
        MOD = 4
        RULE = 5

        X = self.grammar.rule_table[o[:, RULE]][0]
        Y = self.grammar.rule_table[o[:, RULE]][1]
        Z = self.grammar.rule_table[o[:, RULE]][2]


        # dist = o[:, HEAD] - o[:, MOD]
        # bdist = np.digitize(dist, self.bins)
        # direction = dist >= 0
        # base = [(p["WORD"][o[:, HEAD]], p["WORD"][o[:, MOD]]),
        #         (p["WORD"][o[:, HEAD]], p["TAG"][ o[:, MOD]]),
        #         (p["TAG"][o[:, HEAD]],  p["WORD"][o[:, MOD]]),
        #         (p["TAG"][o[:, HEAD]],  p["TAG"][ o[:, MOD]])]
        # t = base
        # t += [(direction, bdist) + b for b in base]

        # for d in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        #     t += [(p["TAG"][o[:, HEAD] + d[0]],
        #            p["TAG"][o[:, HEAD]],
        #            p["TAG"][o[:, MOD] + d[1]],
        #            p["TAG"][o[:, MOD]])]
        t = [(o[:, RULE],)]
        return t

    def templates(self):
        t = [(len(self.grammar.rule_table),)]
        # def s(t):
        #     return self.preprocessor.size(t)
        # base = [(s("WORD"), s("WORD")),
        #         (s("WORD"), s("TAG")),
        #         (s("TAG"),  s("WORD")),
        #         (s("TAG"),  s("TAG"))]
        # t = base
        # t += [(2, len(self.bins) + 1) + b for b in base]
        # t += [(s("TAG"), s("TAG"),
        #        s("TAG"), s("TAG"))] * 4
        return t


def read_data_set(dep_file, ps_file, limit):
    """
    Read in the X, Y data from files.

    Parameters
    -----------

    dep_file : string
       Dependencies in CoNLL format.

    ps_file : string
       Binrarized phrase structures in bracket format with head annotations.
    """
    deps = pydecode.nlp.read_csv_records(dep_file, limit=limit)
    pss = []
    for i, l in enumerate(open(ps_file)):
        pss.append(nltk.ImmutableTree.fromstring(l))
        if i > limit: break


    X = []
    Y = []
    f = pydecode.nlp.CONLL
    for i, (record, ps) in enumerate(itertools.izip(deps, pss)):
        heads = record[:, f["HEAD"]]
        n = len(heads)
        dep_matrix = np.zeros((n, n))
        for m, h in enumerate(heads, 1):
            # Drop the root.
            if int(h) == 0: continue
            dep_matrix[int(h)-1, int(m)-1] = 1

        X.append(ParseInput(tuple(record[:, f["WORD"]]),
                            tuple(record[:, f["TAG"]]),
                            tuple(map(tuple,dep_matrix)),
                            index=i))
        Y.append(ps)
        assert len(ps.leaves()) == n, "%d %d"%(n, len(ps.leaves()))

    return X, Y
