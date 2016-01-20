from unittest import TestCase

from .parser import lexer, parser
from .tree import *
from .pretty import Prettifier, prettify


class TestLexer(TestCase):
    """Test lexer
    """
    def test_basic(self):

        lexer.input('subject:test desc:(house OR car) AND "big garage"~2 dirt~0.3')
        self.assertEqual(lexer.token().value, Word("subject"))
        self.assertEqual(lexer.token().type, "COLUMN")
        self.assertEqual(lexer.token().value, Word("test"))
        self.assertEqual(lexer.token().value, Word("desc"))
        self.assertEqual(lexer.token().type, "COLUMN")
        self.assertEqual(lexer.token().type, "LPAREN")
        self.assertEqual(lexer.token().value, Word("house"))
        self.assertEqual(lexer.token().type, "OR_OP")
        self.assertEqual(lexer.token().value, Word("car"))
        self.assertEqual(lexer.token().type, "RPAREN")
        self.assertEqual(lexer.token().type, "AND_OP")
        self.assertEqual(lexer.token().value, Phrase('"big garage"'))
        t = lexer.token()
        self.assertEqual(t.type, "APPROX")
        self.assertEqual(t.value, "2")
        self.assertEqual(lexer.token().value, Word("dirt"))
        t = lexer.token()
        self.assertEqual(t.type, "APPROX")
        self.assertEqual(t.value, "0.3")
        self.assertEqual(lexer.token(), None)


class TestParser(TestCase):
    """Test base parser
    """

    def test_simplest(self):
        tree = (
            AndOperation(
                Word("foo"),
                Word("bar")))
        parsed = parser.parse("foo bar")
        self.assertEqual(str(parsed), str(tree))
        self.assertEqual(parsed, tree)
        self.assertEqual(parser.parse("foo AND bar"), tree)

    def test_simple_field(self):
        tree = (
            SearchField(
                "subject",
                Word("test")))
        parsed = parser.parse("subject:test")
        self.assertEqual(str(parsed), str(tree))
        self.assertEqual(parsed, tree)

    def test_minus(self):
        tree = (
            AndOperation(
                AndOperation(
                    Minus(
                        Word("test")),
                    Minus(
                        Word("foo"))),
                Minus(
                    Word("bar"))))
        parsed = parser.parse("-test AND -foo AND NOT bar")
        self.assertEqual(str(parsed), str(tree))
        self.assertEqual(parsed, tree)

    def test_plus(self):
        tree = (
            AndOperation(
                AndOperation(
                    Plus(
                        Word("test")),
                    Word("foo")),
                Plus(
                    Word("bar"))))
        parsed = parser.parse("+test AND foo AND +bar")
        self.assertEqual(str(parsed), str(tree))
        self.assertEqual(parsed, tree)

    def test_phrase(self):
        tree = (
            AndOperation(
                Phrase('"a phrase (AND a complicated~ one)"'),
                Phrase('"Another one"')))
        parsed = parser.parse('"a phrase (AND a complicated~ one)" AND "Another one"')
        self.assertEqual(str(parsed), str(tree))
        self.assertEqual(parsed, tree)

    def test_approx(self):
        tree = (
            AndOperation(
                Proximity(
                    Phrase('"foo bar"'),
                    3),
                AndOperation(
                    Fuzzy(
                        Word('baz'),
                        0.3),
                    Fuzzy(
                        Word('fou'),
                        0.5))))
        parsed = parser.parse('"foo bar"~3 baz~0.3 fou~')
        self.assertEqual(str(parsed), str(tree))
        self.assertEqual(parsed, tree)

    def test_groups(self):
        tree = (
           OrOperation(
               Word('test'),
               Group(
                   AndOperation(
                       SearchField(
                           "subject",
                           FieldGroup(
                               OrOperation(
                                   Word('foo'),
                                   Word('bar')))),
                       Word('baz')))))
        parsed = parser.parse('test OR (subject:(foo OR bar) AND baz)')
        self.assertEqual(str(parsed), str(tree))
        self.assertEqual(parsed, tree)

    def test_combinations(self):
        # self.assertEqual(parser.parse("subject:test desc:(house OR car)").pval, "")
        tree = (
            AndOperation(
                SearchField(
                    "subject",
                    Word("test")),
                AndOperation(
                    SearchField(
                        "desc",
                        FieldGroup(
                            OrOperation(
                                Word("house"),
                                Word("car")))),
                    Minus(
                        Proximity(
                            Phrase('"approximatly this"'),
                            3)))))
        parsed = parser.parse('subject:test desc:(house OR car) AND NOT "approximatly this"~3')

        self.assertEqual(str(parsed), str(tree))
        self.assertEqual(parsed, tree)


class TestPrettify(TestCase):

    big_tree = AndOperation(
        Group(OrOperation(Word("baaaaaaaaaar"), Word("baaaaaaaaaaaaaz"))), Word("fooooooooooo"))
    fat_tree = AndOperation(
        SearchField(
            "subject",
            FieldGroup(
                OrOperation(
                    Word("fiiiiiiiiiiz"),
                    AndOperation(Word("baaaaaaaaaar"), Word("baaaaaaaaaaaaaz"))))),
        AndOperation(Word("fooooooooooo"), Word("wiiiiiiiiiz")))

    def test_one_liner(self):
        tree = AndOperation(Group(OrOperation(Word("bar"), Word("baz"))), Word("foo"))
        self.assertEqual(prettify(tree), "( bar OR baz ) AND foo")

    def test_small(self):
        prettify = Prettifier(indent=8, max_len=20)
        self.assertEqual(
            "\n" + prettify(self.big_tree), """
(
        baaaaaaaaaar
        OR
        baaaaaaaaaaaaaz
)
AND
fooooooooooo""")
        self.assertEqual(
            "\n" + prettify(self.fat_tree), """
subject: (
        fiiiiiiiiiiz
        OR
                baaaaaaaaaar
                AND
                baaaaaaaaaaaaaz
)
AND
fooooooooooo
AND
wiiiiiiiiiz""")

    def test_small_inline_ops(self):
        prettify = Prettifier(indent=8, max_len=20, inline_ops=True)
        self.assertEqual("\n" + prettify(self.big_tree), """
(
        baaaaaaaaaar OR
        baaaaaaaaaaaaaz ) AND
fooooooooooo""")
        self.assertEqual("\n" + prettify(self.fat_tree), """
subject: (
        fiiiiiiiiiiz OR
                baaaaaaaaaar AND
                baaaaaaaaaaaaaz ) AND
fooooooooooo AND
wiiiiiiiiiz""")

    def test_normal(self):
        prettify = Prettifier(indent=4, max_len=50)
        self.assertEqual("\n" + prettify(self.big_tree), """
(
    baaaaaaaaaar OR baaaaaaaaaaaaaz
)
AND
fooooooooooo""")
        self.assertEqual("\n" + prettify(self.fat_tree), """
subject: (
    fiiiiiiiiiiz
    OR
        baaaaaaaaaar AND baaaaaaaaaaaaaz
)
AND
fooooooooooo
AND
wiiiiiiiiiz""")

    def test_normal_inline_ops(self):
        prettify = Prettifier(indent=4, max_len=50, inline_ops=True)
        self.assertEqual("\n" + prettify(self.big_tree), """
(
    baaaaaaaaaar OR baaaaaaaaaaaaaz ) AND
fooooooooooo""")
        self.assertEqual("\n" + prettify(self.fat_tree), """
subject: (
    fiiiiiiiiiiz OR
        baaaaaaaaaar AND baaaaaaaaaaaaaz ) AND
fooooooooooo AND
wiiiiiiiiiz""")
