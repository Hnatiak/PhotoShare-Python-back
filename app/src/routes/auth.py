from typing import List
from src.services.email import send_email
from fastapi import APIRouter, HTTPException, Depends, status, Security, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.repository import users as repository_users
from src.services.auth import auth_service

from src.schemas.schemas import UserResponse, UserSchema, TokenModel
from src.schemas.schemas import RequestEmail
from src.repository.users import add_to_blacklist

from src.entity.models import User

router = APIRouter(prefix='/auth', tags=["auth"])
security = HTTPBearer()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserSchema, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    """
    The signup function creates a new user in the database.
    It takes a JSON object with the username, email, password, and is_active fields.

    :param body: UserSchema: Specify the type of the body parameter
    :param background_tasks: BackgroundTasks: Pass tasks to be run in the background
    :param request: Request: Get the base url of the application
    :param db: Session: Pass the database session to the repository
    :return: The user object and a success message

    Args:
        body: UserSchema
        background_tasks: BackgroundTasks
        request: Request
        db: Session

    Returns:
        The user object and a success message
    """
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)

    # background_tasks.add_task(send_email, new_user.email, new_user.username, request.base_url)
    token_verification = auth_service.create_email_token(
        {"sub": new_user.email})
    print(f"{request.base_url}api/auth/confirmed_email/{token_verification}")

    return {"user": new_user, "detail": "User successfully created. Check your email for confirmation."}


@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """
    The confirmed_email function takes a token as input and returns a message if the token is valid.

    :param token: str: Pass the token to the function
    :param db: Session: Pass the database session to the repository
    :return: A message if the token is valid
    Args:
        token:
        db:

    Returns:

    """
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repository_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post('/request_email')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: Session = Depends(get_db)):
    """
    The request_email function takes in a body and sends an email to the user
    with a link that allows them to confirm their email address.

    :param body: RequestEmail: Get the email from the request body
    :param background_tasks: BackgroundTasks: Add a task to the background tasks
    :param request: Request: Get the base url of the application
    :param db: Session: Pass the database session to the repository
    :return: A message
    Args:
        body:
        background_tasks:
        request:
        db:

    Returns:

    """
    user = await repository_users.get_user_by_email(body.email, db)
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(send_email, user.email, user.username, request.base_url)
    return {"message": "Check your email for confirmation."}


@router.post("/login", response_model=TokenModel)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    The login function is used to authenticate a user and generate an access token.
    It takes in a username and password, and returns an access token.

    :param body: OAuth2PasswordRequestForm: Get the username and password from the request
    :param db: Session: Pass the database session to the repository
    :return: The access token and refresh token
    Args:
        body:
        db:

    Returns:

    """
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed")
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    # Generate JWT
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_token(user, refresh_token, db)
    db.add(user)
    db.commit()
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/refresh_token', response_model=TokenModel)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    """
    The refresh_token function takes in a refresh token, and returns an access token
    if the refresh token is valid.

    :param credentials: HTTPAuthorizationCredentials: Get the refresh token from the request
    :param db: Session: Pass the database session to the repository
    :return: The access token
    Args:
        credentials:
        db:

    Returns:

    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """
    The logout function is used to log out a user. It takes in a background_tasks, credentials, and db
    and returns a message.

    :param background_tasks: BackgroundTasks: Add a task to the background tasks
    :param credentials: HTTPAuthorizationCredentials: Get the credentials from the request
    :param db: Session: Pass the database session to the repository
    :param user: User: Get the current user from the request
    :return: A message
    Args:
        background_tasks:
        credentials:
        db:
        user:

    Returns:

    """
    try:
        token = credentials.credentials
        await repository_users.add_to_blacklist(token, db)

        user.refresh_token = None
        db.commit()
        #########################
        expired = await auth_service.get_exp_from_token(token)
        background_tasks.add_task(repository_users.dell_from_bleck_list, expired, token, db)
        #########################
        return {"message": "Successfully logged out"}
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You are successfully logged out")
