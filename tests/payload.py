from app.schemas.user_schemas import SignUpRequest, UserUpdateRequest

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

test_user_1_update = UserUpdateRequest(
    name="updated test user 1", password="updatedtestpassword1"
)
expected_test_user_1_update = {
    "name": "updated test user 1",
    "username": "test1",
    "email": "test1@test.com",
    "disabled": False,
}
