from app.schemas.user_schemas import SignUpRequest, UserUpdateRequest

test_user_1 = SignUpRequest(
    id="11aed3b0-3cd9-4a45-8479-bd5497df241b",
    name="test user 1",
    username="test1",
    email="test1@test.com",
    password="testpassword1",
)
expected_test_user_1 = {
    "id": "11aed3b0-3cd9-4a45-8479-bd5497df241b",
    "name": "test user 1",
    "username": "test1",
    "email": "test1@test.com",
    "disabled": False,
}

test_user_2 = SignUpRequest(
    id="f84fa696-42bb-42bb-981d-ee63707ceae7",
    name="test user 2",
    username="test2",
    email="test2@test.com",
    password="testpassword2",
)
expected_test_user_2 = {
    "id": "f84fa696-42bb-42bb-981d-ee63707ceae7",
    "name": "test user 2",
    "username": "test2",
    "email": "test2@test.com",
    "disabled": False,
}

test_user_3 = SignUpRequest(
    id="f84fa696-33bb-42bb-981d-ee63707ceae7",
    name="test user 3",
    username="test3",
    email="test3@test.com",
    password="testpassword3",
)
expected_test_user_3 = {
    "id": "f84fa696-33bb-42bb-981d-ee63707ceae7",
    "name": "test user 3",
    "username": "test3",
    "email": "test3@test.com",
    "disabled": False,
}

test_user_1_update = UserUpdateRequest(
    name="updated test user 1", password="updatedtestpassword1"
)
expected_test_user_1_update = {
    "id": "11aed3b0-3cd9-4a45-8479-bd5497df241b",
    "name": "updated test user 1",
    "username": "test1",
    "email": "test1@test.com",
    "disabled": False,
}
