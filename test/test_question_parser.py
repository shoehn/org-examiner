import unittest

import orgparse

from orgexaminer import Question


class TestParser(unittest.TestCase):

    def setUp(self):
        """Parse a quiz to be used in the tests."""
        self.quiz = orgparse.load('../sample/sample.org')

    def test_parser_loads_org_files(self):
        quiz = orgparse.load('../sample/sample.org')
        # By convention there may be only one first level
        # heading.
        self.assertEqual(1, len(quiz.children))
        # This sample has three questions
        self.assertEqual(3, len(quiz.children[0].children))

    def test_kprim_question_parses_correctly(self):
        """
        Test if all the elements of a multiple choice test
        are correctly parsed.

        :return: success
        """
        q = Question()

        # The third one is kprime
        q.parse_orgsnippet(self.quiz.children[0].children[2])

        # Check for success
        self.assertTrue(q.parse_success())

        self.assertEqual(q.QuestionTypes.KPRIME, q.question_type)
        self.assertEqual('K-Prime', q.question_name)
        self.assertEqual('This question type has four options, that have to be answered to be true or false.', q.question_text)
        self.assertEqual(None, q.question_defaultgrade)
        self.assertEqual(None, q.question_penalty)

        a = q.question_answers[0]  # Shortcut to the first answer
        self.assertEqual('true', a['correct'])
        self.assertEqual('This is the first option and it is true.', a['answer'])
        self.assertEqual('', a['feedback'])

        a = q.question_answers[1]  # Shortcut to the first answer
        self.assertEqual('false', a['correct'])
        self.assertEqual('This is the second option and it is false.', a['answer'])
        self.assertEqual('', a['feedback'])

        a = q.question_answers[2]  # Shortcut to the first answer
        self.assertEqual('true', a['correct'])
        self.assertEqual('Berlin is the capital of Germany', a['answer'])
        self.assertEqual('', a['feedback'])

        a = q.question_answers[3]  # Shortcut to the first answer
        self.assertEqual('false', a['correct'])
        self.assertEqual('Zurich is in Austria.', a['answer'])
        self.assertEqual('Serious? You mix up Austria and Switzerland.', a['feedback'])

    def test_text_question_parses_correctly(self):
        """
        Test if all the elements of a multiple choice test
        are correctly parsed.

        :return: success
        """
        q = Question()

        # The second one is text
        q.parse_orgsnippet(self.quiz.children[0].children[1])

        # Check for success
        self.assertTrue(q.parse_success())

        self.assertEqual(q.QuestionTypes.TEXT, q.question_type)
        self.assertEqual('Open question with text field', q.question_name)
        self.assertEqual('What are three advantages of <b>Berlin</b> being the capital of Germany?', q.question_text)
        self.assertEqual('3.00', q.question_defaultgrade)
        self.assertEqual(None, q.question_penalty)

    def test_mc_question_parses_correctly(self):
        """
        Test if all the elements of a multiple choice test
        are correctly parsed.

        :return: success
        """
        q = Question()

        # The first one is multichoice
        q.parse_orgsnippet(self.quiz.children[0].children[0])

        # Check for success
        self.assertTrue(q.parse_success())

        self.assertEqual(q.QuestionTypes.MULTICHOICE, q.question_type)
        self.assertEqual('Capitals of the world', q.question_name)
        self.assertEqual('What is the capital of Germany?', q.question_text)
        self.assertEqual(4, len(q.question_answers))

        a = q.question_answers[0]  # Shortcut to the first answer
        self.assertEqual(-33.33333, a['fraction'])
        self.assertEqual('Munich', a['answer'])
        self.assertEqual('Munich is the greatest city in Germany, but not the capital.', a['feedback'])

        a = q.question_answers[1]  # Shortcut to the first answer
        self.assertEqual(-33.33333, a['fraction'])
        self.assertEqual('Zurich', a['answer'])
        self.assertEqual('Zurich is not even in Germany??', a['feedback'])

        a = q.question_answers[3]  # Shortcut to the first answer
        self.assertEqual(-33.33333, a['fraction'])
        self.assertEqual('Cologne', a['answer'])
        self.assertEqual('Totally crazy city, but not the capital.', a['feedback'])

        a = q.question_answers[2]  # Shortcut to the first answer
        self.assertEqual(100, a['fraction'])
        self.assertEqual('Berlin', a['answer'])
        self.assertEqual('Yes, let\'s face it, that is the Capital of Germany.', a['feedback'])

        self.assertEqual('2.00', q.question_defaultgrade)
        self.assertEqual('false', q.question_single)
        self.assertEqual('0.33', q.question_penalty)
        self.assertEqual('true', q.question_shuffle_answers)


if __name__ == '__main__':
    unittest.main()
