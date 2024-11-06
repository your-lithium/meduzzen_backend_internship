from app.schemas.company_schemas import CompanyCreateRequest, CompanyUpdateRequest
from app.schemas.quiz_result_schemas import Answers
from app.schemas.quiz_schemas import (
    Answer,
    AnswerList,
    Question,
    QuestionList,
    QuizCreateRequest,
    QuizUpdateRequest,
)
from app.schemas.user_schemas import SignInRequest, SignUpRequest, UserUpdateRequest

test_user_1 = SignUpRequest(
    name="test user 1",
    username="test1",
    email="test1@test.com",
    password="testpassword1",
)
expected_test_user_1 = {
    "name": "test user 1",
    "username": "test1",
    "email": "test1@test.com",
    "disabled": False,
}
test_user_1_signin = SignInRequest(
    email="test1@test.com",
    password="testpassword1",
)
test_user_1_update = UserUpdateRequest(
    name="updated test user 1", password="updatedtestpassword1"
)
expected_test_user_1_update = {
    "name": "updated test user 1",
    "username": "test1",
    "email": "test1@test.com",
    "disabled": False,
}

test_user_2 = SignUpRequest(
    name="test user 2",
    username="test2",
    email="test2@test.com",
    password="testpassword2",
)
expected_test_user_2 = {
    "name": "test user 2",
    "username": "test2",
    "email": "test2@test.com",
    "disabled": False,
}

test_user_3 = SignUpRequest(
    name="test user 3",
    username="test3",
    email="test3@test.com",
    password="testpassword3",
)
expected_test_user_3 = {
    "name": "test user 3",
    "username": "test3",
    "email": "test3@test.com",
    "disabled": False,
}

test_company_1 = CompanyCreateRequest(
    name="test company 1", description="company for testing #1", is_public=True
)
expected_test_company_1 = {
    "name": "test company 1",
    "description": "company for testing #1",
    "is_public": True,
}
test_company_1_update = CompanyUpdateRequest(
    name="updated test company 1", is_public=False
)
expected_test_company_1_update = {
    "name": "updated test company 1",
    "description": "company for testing #1",
    "is_public": False,
}

test_company_2 = CompanyCreateRequest(
    name="test company 2", description="company for testing #2", is_public=True
)
expected_test_company_2 = {
    "name": "test company 2",
    "description": "company for testing #2",
    "is_public": True,
}

test_company_3 = CompanyCreateRequest(
    name="test company 3", description="company for testing #3", is_public=True
)
expected_test_company_3 = {
    "name": "test company 3",
    "description": "company for testing #3",
    "is_public": True,
}

test_quiz_1 = QuizCreateRequest(
    name="test quiz 1",
    description="quiz for testing #1",
    frequency=1,
    questions=QuestionList(
        [
            Question(
                question="is this a question?",
                answers=AnswerList([Answer(options={0: "yes", 1: "no"}, correct=[0])]),
            ),
            Question(
                question="what animals are cats?",
                answers=AnswerList(
                    [
                        Answer(
                            options={
                                0: "house cat",
                                1: "dog",
                                2: "tiger",
                                3: "parrot",
                                4: "raccoon",
                                5: "lion",
                            },
                            correct=[0, 2, 5],
                        )
                    ]
                ),
            ),
        ]
    ),
)
expected_test_quiz_1 = {
    "name": "test quiz 1",
    "description": "quiz for testing #1",
    "frequency": 1,
    "questions": [
        {
            "question": "is this a question?",
            "answers": [{"options": {"0": "yes", "1": "no"}, "correct": [0]}],
        },
        {
            "question": "what animals are cats?",
            "answers": [
                {
                    "options": {
                        "0": "house cat",
                        "1": "dog",
                        "2": "tiger",
                        "3": "parrot",
                        "4": "raccoon",
                        "5": "lion",
                    },
                    "correct": [0, 2, 5],
                }
            ],
        },
    ],
}
test_quiz_1_update = QuizUpdateRequest(
    name="updated test quiz #1",
    questions=QuestionList(
        [
            Question(
                question="what animals are cats?",
                answers=AnswerList(
                    [
                        Answer(
                            options={
                                0: "house cat",
                                1: "dog",
                                2: "tiger",
                                3: "parrot",
                                4: "raccoon",
                                5: "lion",
                            },
                            correct=[0, 2, 5],
                        )
                    ]
                ),
            ),
            Question(
                question="are dogs cats?",
                answers=AnswerList([Answer(options={0: "yes", 1: "no"}, correct=[1])]),
            ),
        ]
    ),
)
expected_test_quiz_1_update = {
    "name": "updated test quiz #1",
    "description": "quiz for testing #1",
    "frequency": 1,
    "questions": [
        {
            "question": "what animals are cats?",
            "answers": [
                {
                    "options": {
                        "0": "house cat",
                        "1": "dog",
                        "2": "tiger",
                        "3": "parrot",
                        "4": "raccoon",
                        "5": "lion",
                    },
                    "correct": [0, 2, 5],
                }
            ],
        },
        {
            "question": "are dogs cats?",
            "answers": [{"options": {"0": "yes", "1": "no"}, "correct": [1]}],
        },
    ],
}
test_quiz_1_answers = Answers([[1], [0, 2, 5]])
expected_test_quiz_1_answers = {"answered": 2, "correct": 1}

test_quiz_2 = QuizCreateRequest(
    name="test quiz 2",
    description="quiz for testing #2",
    frequency=2,
    questions=QuestionList(
        [
            Question(
                question="is this a question?",
                answers=AnswerList([Answer(options={0: "yes", 1: "no"}, correct=[0])]),
            ),
            Question(
                question="what animals are birds?",
                answers=AnswerList(
                    [
                        Answer(
                            options={
                                0: "house cat",
                                1: "dog",
                                2: "pigeon",
                                3: "parrot",
                                4: "raccoon",
                                5: "magpie",
                            },
                            correct=[2, 3, 5],
                        )
                    ]
                ),
            ),
        ]
    ),
)
expected_test_quiz_2 = {
    "name": "test quiz 2",
    "description": "quiz for testing #2",
    "frequency": 2,
    "questions": [
        {
            "question": "is this a question?",
            "answers": [{"options": {"0": "yes", "1": "no"}, "correct": [0]}],
        },
        {
            "question": "what animals are birds?",
            "answers": [
                {
                    "options": {
                        "0": "house cat",
                        "1": "dog",
                        "2": "pigeon",
                        "3": "parrot",
                        "4": "raccoon",
                        "5": "magpie",
                    },
                    "correct": [2, 3, 5],
                }
            ],
        },
    ],
}

test_quiz_3 = QuizCreateRequest(
    name="test quiz 3",
    description="quiz for testing #3",
    frequency=1,
    questions=QuestionList(
        [
            Question(
                question="is this a question?",
                answers=AnswerList([Answer(options={0: "yes", 1: "no"}, correct=[0])]),
            ),
            Question(
                question="what animals are generally domestic?",
                answers=AnswerList(
                    [
                        Answer(
                            options={
                                0: "house cat",
                                1: "dog",
                                2: "pigeon",
                                3: "parrot",
                                4: "raccoon",
                                5: "magpie",
                                6: "lion",
                            },
                            correct=[1, 2, 3],
                        )
                    ]
                ),
            ),
        ]
    ),
)
expected_test_quiz_3 = {
    "name": "test quiz 3",
    "description": "quiz for testing #3",
    "frequency": 1,
    "questions": [
        {
            "question": "is this a question?",
            "answers": [{"options": {"0": "yes", "1": "no"}, "correct": [0]}],
        },
        {
            "question": "what animals are generally domestic?",
            "answers": [
                {
                    "options": {
                        "0": "house cat",
                        "1": "dog",
                        "2": "pigeon",
                        "3": "parrot",
                        "4": "raccoon",
                        "5": "magpie",
                        "6": "lion",
                    },
                    "correct": [1, 2, 3],
                }
            ],
        },
    ],
}

expected_test_user_1_rating = (1 + 1 + 0) / (2 * 3)
expected_test_user_2_rating = (2 + 0 + 1) / (2 * 3)
expected_test_user_1_dynamics_scores = [1 / 2, (1 + 1) / (2 * 2), (1 + 1 + 0) / (2 * 3)]
expected_test_user_2_dynamics_scores = [2 / 2, (2 + 0) / (2 * 2), (2 + 0 + 1) / (2 * 3)]

expected_test_notification_1 = {"text": "This is notification #1", "status": "read"}
expected_test_notification_2 = {"text": "This is notification #3", "status": "unread"}
expected_test_notification_2_update = {
    "text": "This is notification #3",
    "status": "read",
}
