import json
from collections import namedtuple


Question = namedtuple('Question', ['question', 'answers'])


class HARSQuiz:

    RESULTS = {
        'ru': ['отсутствие тревоги 👍', 'средняя выраженность тревожного расстройства 😐', 'тяжелая тревога 😦'],
        'en': ['mild anxiety severity', 'mild to moderate anxiety severity', 'moderate to severe anxiety severity']}

    def __init__(self, chat_id, lang, questions):
        self.chat_id = chat_id
        self.lang = lang
        self.questions = questions
        # Init state
        self.question_number = 0
        self.is_completed = False
        self.answers = []

    def get_question(self):
        return Question(
            "\u2753({}/{}) {}".format(
                (self.question_number + 1), len(self.questions[self.lang]['questions']),
                self.questions[self.lang]['questions'][self.question_number]),
            self.questions[self.lang]['answers'])

    def save_answer(self, answer):
        self.answers.append(answer)
        self.question_number += 1
        if self.question_number == len(self.questions[self.lang]['questions']):
            self.is_completed = True

    def get_result(self):
        if not self.is_completed:
            raise ValueError("Can't calculate result for incomplete test")
        result = sum(self.answers)
        if result <= 17:
            description = self.RESULTS[self.lang][0]
        elif result <= 24:
            description = self.RESULTS[self.lang][1]
        else:
            description = self.RESULTS[self.lang][2]
        return '{}:\n{}/{}\n{}'.format(
            'Результат' if self.lang == 'ru' else 'Result',
            result, len(self.questions[self.lang]['questions']) * 4, description)


class BaseQuizStorage:

    QuizClass = None

    def __init__(self):
        self.quizes = {}

    def get_or_create(self, chat_id, lang):
        if chat_id not in self.quizes:
            self.quizes[chat_id] = self.QuizClass(chat_id, lang, self.questions)
        return self.quizes[chat_id]


class HARSQuizStorage(BaseQuizStorage):

    QuizClass = HARSQuiz

    def __init__(self):
        super().__init__()
        with open('hars.json') as hars_file:
            self.questions = json.loads(hars_file.read())


class MADRSQuizStorage(BaseQuizStorage):

    QuizClass = NotImplemented

    def __init__(self):
        super().__init__()
        with open('madrs.json') as madrs_file:
            self.madrs_data = json.loads(madrs_file.read())
