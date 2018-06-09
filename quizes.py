from collections import namedtuple


Question = namedtuple('Question', ['question', 'answers'])


class BaseQuiz:

    def __init__(self, id, questions, lang, question_number=0, answers=None):
        self.id = id
        self.questions = questions
        self.lang = lang
        self.question_number = question_number
        self.answers = [] if answers is None else answers

    def get_question(self):
        raise NotImplementedError

    def save_answer(self, answer):
        self.answers.append(answer)
        self.question_number += 1

    def get_result(self):
        raise NotImplementedError

    @property
    def is_completed(self):
        return self.question_number == self.questions_count

    @property
    def questions_count(self):
        raise NotImplementedError


class HARSQuiz(BaseQuiz):

    RESULTS = {
        'ru': ['отсутствие тревоги 👍', 'средняя выраженность тревожного расстройства 😐', 'тяжелая тревога 😦'],
        'en': ['mild anxiety severity', 'mild to moderate anxiety severity', 'moderate to severe anxiety severity']}

    type_ = 'hars'

    def get_question(self):
        return Question(
            "\u2753({}/{}) {}".format(
                (self.question_number + 1), self.questions_count,
                self.questions[self.lang]['questions'][self.question_number]),
            self.questions[self.lang]['answers'])

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
            result, self.questions_count * 4, description)

    @property
    def questions_count(self):
        return len(self.questions[self.lang]['questions'])


class MADRSQuiz(BaseQuiz):

    RESULTS = {
        'en': ['normal 👍', 'mild depression 😐', 'moderate depression 😔', 'severe depression 😨'],
        'ru': ['норма 👍', 'слабая депрессия 😐', 'умеренная депрессия 😔', 'тяжелая депрессия 😨']}

    type_ = 'madrs'

    def get_question(self):
        return Question(
            "\u2753({}/{}) {}".format(
                (self.question_number + 1), self.questions_count,
                self.questions[self.lang][self.question_number]['question']),
            self.questions[self.lang][self.question_number]['answers'])

    def get_result(self):
        if not self.is_completed:
            raise ValueError("Can't calculate result for incomplete test")
        result = sum(self.answers)
        if result <= 6:
            description = self.RESULTS[self.lang][0]
        elif result <= 19:
            description = self.RESULTS[self.lang][1]
        elif result <= 34:
            description = self.RESULTS[self.lang][2]
        else:
            description = self.RESULTS[self.lang][3]
        return '{}:\n{}/{}\n{}'.format(
            'Результат' if self.lang == 'ru' else 'Result',
            result, self.questions_count * 6, description)

    @property
    def questions_count(self):
        return len(self.questions[self.lang])
