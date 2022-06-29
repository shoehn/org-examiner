import sys

from lxml.etree import CDATA
from orgparse import load
from lxml import etree


#
# Utility functions to make writing XML easier
#
def add_node_with_text(parent, name, text):
    """Add a node to the parent with text wrapped in a text node."""
    node1 = etree.SubElement(parent, name)
    subnode_text = etree.SubElement(node1, 'text')
    subnode_text.text = text


def add_html_node_with_text(parent, name, text):
    """Add a node to the parent with text wrapped in a text node."""
    node1 = etree.SubElement(parent, name)
    subnode_text = etree.SubElement(node1, 'text', attrib={'format': 'html'})
    subnode_text.text = CDATA(text)


def add_node_with_content(xml_root, name, content):
    """Add a node and add the content as text to that node."""
    node2 = etree.SubElement(xml_root, name)
    node2.text = content


def add_node_answer(xml_root, fraction, text, feedback):
    """Create an answer node."""
    node3 = etree.SubElement(xml_root, 'answer', attrib={'fraction': fraction})
    subnode_text = etree.SubElement(node3, 'text', attrib={'format': 'html'})
    subnode_text.text = CDATA(text)
    add_html_node_with_text(node3, 'feedback', feedback)


def add_category(xml_root, name, description):
    """Add the category node to the quiz."""
    # The header is a question of type category
    category_node = etree.SubElement(xml_root, 'question', attrib={'type': 'category'})

    add_node_with_text(category_node, 'category', "$course$/top/" + name)
    add_node_with_text(category_node, 'info', description)


def add_node_weight(rootnode, rownumber, correct):
    firstweight = etree.SubElement(rootnode, 'weight', attrib={'rownumber': rownumber, 'columnnumber': '1'})
    secondweight = etree.SubElement(rootnode, 'weight', attrib={'rownumber': rownumber, 'columnnumber': '2'})

    if correct:
        v1 = etree.SubElement(firstweight, 'value')
        v1.text = '1.000'
        v2 = etree.SubElement(secondweight, 'value')
        v2.text = '0.000'
    else:
        v1 = etree.SubElement(firstweight, 'value')
        v1.text = '0.000'
        v2 = etree.SubElement(secondweight, 'value')
        v2.text = '1.000'


class Question(object):
    """Internal data structure to store parsed questions."""
    from enum import Enum

    class QuestionTypes(Enum):
        """
        Represents the question types and stores
        the moodle xml keywords as their values.
        """
        MULTICHOICE = 'multichoice'
        KPRIME = 'kprime'
        TEXT = 'essay'
        UNKNOWN = 'unknown'

    def __init__(self):
        self.question_penalty = None
        self.question_defaultgrade = None
        self.question_single = None
        self.question_shuffle_answers = None
        self.question_answers = None
        self.question_text = None
        self.question_name = None
        self.question_type = self.QuestionTypes.UNKNOWN

    def parse_orgsnippet(self, org_question):
        """Parses the questions into an internal data structure.

        This helps to make the code testable and more maintainable.
        """
        self.question_type = self.determine_question_type(org_question)

        # These are the same for all implemented question types
        self.question_name = org_question.heading.strip()
        self.question_text = org_question.body.strip()
        # Read the properties
        self.question_shuffle_answers = org_question.get_property('shuffleanswers')
        self.question_single = org_question.get_property('single')
        self.question_defaultgrade = org_question.get_property('defaultgrade')
        self.question_penalty = org_question.get_property('penalty')

        if self.question_type == self.QuestionTypes.KPRIME:
            # Parse the answers:
            self.question_answers = []
            plausible_sum = 0
            for a in org_question.children:
                # Undo the workaround that - is not allowed in a org-mode tag
                correct = a.tags.pop()
                self.question_answers.append(
                    {'answer': a.heading.strip(), 'feedback': a.body.strip(), 'correct': correct})

        if self.question_type == self.QuestionTypes.MULTICHOICE:
            self.question_name = org_question.heading.strip()
            self.question_text = org_question.body.strip()

            # Parse the answers:
            self.question_answers = []
            plausible_sum = 0
            for a in org_question.children:
                # Undo the workaround that - is not allowed in a org-mode tag
                fraction = float(a.tags.pop().replace('_', '-', 1).replace('_', '.', 1))
                plausible_sum += fraction
                self.question_answers.append(
                    {'answer': a.heading.strip(), 'feedback': a.body.strip(), 'fraction': fraction})

            if plausible_sum > 1 or plausible_sum < -1:
                print(
                    'Warning: the sum of the fraction should be 0. Otherwise always selecting all answers is a winning '
                    'strategy.')
                print('Checksum is: ' + str(plausible_sum))

    def parse_success(self):
        return self.question_type != self.QuestionTypes.UNKNOWN

    def determine_question_type(self, snippet):
        """
        Determine the type of the test in the given org snippet.
        :return: TestType
        """
        if len(snippet.children) == 0:
            # TODO implement debugging with a log framework
            return self.QuestionTypes.TEXT

        t = snippet.children[0].tags.pop()
        if t == 'true' or t == 'false':
            return self.QuestionTypes.KPRIME

        if t is not None:
            return self.QuestionTypes.MULTICHOICE

        return self.QuestionTypes.UNKNOWN


def add_kprime_to_xml(parent, question):
    kprime_node = etree.SubElement(parent, 'question', attrib={'type': question.question_type.value})

    add_node_with_text(kprime_node, 'name', question.question_name)
    add_node_with_text(kprime_node, 'questiontext', question.question_text)
    add_node_with_text(kprime_node, 'generalfeedback', '')

    add_node_with_content(kprime_node, 'defaultgrade', question.question_defaultgrade)
    add_node_with_content(kprime_node, 'penalty', question.question_penalty)
    add_node_with_content(kprime_node, 'single', question.question_single)
    add_node_with_content(kprime_node, 'shuffleanswers', question.question_shuffle_answers)

    add_node_with_text(kprime_node, 'scoringmethod', 'kprime')

    row1 = etree.SubElement(kprime_node, 'row', attrib={'number': '1'})
    add_html_node_with_text(row1, 'optiontext', question.question_answers[0]['answer'])
    add_html_node_with_text(row1, 'feedbacktext', question.question_answers[0]['feedback'])

    row2 = etree.SubElement(kprime_node, 'row', attrib={'number': '2'})
    add_html_node_with_text(row2, 'optiontext', question.question_answers[1]['answer'])
    add_html_node_with_text(row2, 'feedbacktext', question.question_answers[1]['feedback'])

    row3 = etree.SubElement(kprime_node, 'row', attrib={'number': '3'})
    add_html_node_with_text(row3, 'optiontext', question.question_answers[2]['answer'])
    add_html_node_with_text(row3, 'feedbacktext', question.question_answers[2]['feedback'])

    row4 = etree.SubElement(kprime_node, 'row', attrib={'number': '4'})
    add_html_node_with_text(row4, 'optiontext', question.question_answers[3]['answer'])
    add_html_node_with_text(row4, 'feedbacktext', question.question_answers[3]['feedback'])

    # The column 1 and 2 give the "Richtig" or "Falsch" titles
    col1 = etree.SubElement(kprime_node, 'column', attrib={'number': '1'})
    add_node_with_text(col1, 'responsetext', 'Richtig')

    col2 = etree.SubElement(kprime_node, 'column', attrib={'number': '2'})
    add_node_with_text(col2, 'responsetext', 'Falsch')

    nrow = 1

    for opts in question.question_answers:
        isTrue = opts['correct'] == 'true'
        add_node_weight(kprime_node, str(nrow), isTrue)
        nrow += 1


def add_text_to_xml(parent, question):
    text_node = etree.SubElement(parent, 'question', attrib={'type': question.question_type.value})
    add_node_with_text(text_node, 'name', question.question_name)
    add_html_node_with_text(text_node, 'questiontext', question.question_text)
    add_node_with_text(text_node, 'generalfeedback', '')
    add_node_with_content(parent, 'defaultgrade', question.question_defaultgrade)
    add_node_with_content(parent, 'penalty', question.question_penalty)

    # I set these as defaults, since I do not want to bother with them
    add_node_with_content(parent, 'responseformat', 'editor')
    add_node_with_content(parent, 'responserequired', '1')
    add_node_with_content(parent, 'responsefieldlines', '15')
    add_node_with_content(parent, 'minwordlimit', '')
    add_node_with_content(parent, 'maxwordlimit', '')
    add_node_with_content(parent, 'attachments', '0')
    add_node_with_content(parent, 'attachmentsrequired', '0')
    add_node_with_content(parent, 'filetypeslist', '')
    add_node_with_text(parent, 'graderinfo', '')
    add_node_with_text(parent, 'responsetemplate', '')


def add_mc_to_xml(parent, question):
    mc_node = etree.SubElement(parent, 'question', attrib={'type': question.question_type.value})
    add_node_with_text(mc_node, 'name', question.question_name)
    add_html_node_with_text(mc_node, 'questiontext', question.question_text)
    add_node_with_text(mc_node, 'generalfeedback', '')

    add_node_with_content(mc_node, 'defaultgrade', question.question_defaultgrade)
    add_node_with_content(mc_node, 'penalty', question.question_penalty)
    add_node_with_content(mc_node, 'single', question.question_single)
    add_node_with_content(mc_node, 'shuffleanswers', question.question_shuffle_answers)

    # TODO what do I want to do with these? Make them as default but configurable via properties?
    add_html_node_with_text(mc_node, 'correctfeedback', 'Die Antwort ist richtig!')
    add_html_node_with_text(mc_node, 'partiallycorrectfeedback', 'Die Antwort ist teilweise richtig!')
    add_html_node_with_text(mc_node, 'incorrectfeedback', 'Die Antwort ist falsch!')

    for a in question.question_answers:
        add_node_answer(mc_node, str(a['fraction']), a['answer'], a['feedback'])


if __name__ == "__main__":
    # To get started load the sample file
    # TODO: get the filename from command line args
    quiz = load('../sample/sample.org')

    tree = etree.ElementTree(etree.Element('quiz'))
    xmlroot = tree.getroot()

    org_category = quiz.children[0]
    add_category(xmlroot, org_category.heading, org_category.body.strip())

    if quiz.children[0].children is None:
        print("No questions in file")
        sys.exit(1)

    for org_question in quiz.children[0].children:
        q = Question()
        q.parse_orgsnippet(org_question)
        if q.parse_success():
            print("Adding question: " + org_question.heading)
            if q.question_type == q.QuestionTypes.KPRIME:
                add_kprime_to_xml(xmlroot, q)
            elif q.question_type == q.QuestionTypes.TEXT:
                add_text_to_xml(xmlroot, q)
            elif q.question_type == q.QuestionTypes.MULTICHOICE:
                add_mc_to_xml(xmlroot, q)

        else:
            print("Error parsing question: " + org_question.heading)
            sys.exit(1)

    tree.write('sample.xml', pretty_print=True)
