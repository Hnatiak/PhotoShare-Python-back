from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks, Request, Response
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import FileResponse
from src.database.db import get_db
from src.repository import users as repositories_users
from src.schemas.user import UserSchema, TokenSchema, UserResponse, RequestEmail
from src.services.auth import auth_service
from src.services.email import send_email
from src.conf import messages

router = APIRouter(prefix='/auth', tags=['auth'])
get_refresh_token = HTTPBearer()

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserSchema, bt: BackgroundTasks, request: Request, db: AsyncSession = Depends(get_db)):
    """
    The signup function creates a new user in the database.

    :param body: UserSchema: Define the input for the user
    :param bt: BackgroundTasks: Add a task to the background tasks
    :param request: Request: Get the base url
    :param db: AsyncSession: Access the database
    :return: A user object
    """
    exist_user = await repositories_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.ACCOUNT_EXIST)
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repositories_users.create_user(body, db)

    # send email notification
    bt.add_task(send_email, new_user.email, new_user.username, str(request.base_url))
    return new_user

@router.post("/login", response_model=TokenSchema)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    The login function is used to authenticate a user and generate an access token.

    :param body: OAuth2PasswordRequestForm: Get the username and password from the request
    :param db: AsyncSession: Pass the database session to the repository
    :return: A token object
    """
    user = await repositories_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INVALID_EMAIL)
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.NOT_CONFIRMED)
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INVALID_PASSWORD)
    # Generate JWT
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repositories_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.get('/refresh_token', response_model=TokenSchema)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(get_refresh_token), db: AsyncSession = Depends(get_db)):
    """
    The refresh_token function is used to refresh the access token.

    :param credentials: HTTPAuthorizationCredentials: Get the refresh token from the request
    :param db: AsyncSession: Pass the database session to the repository
    :return: A token object
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repositories_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INVALID_REFRESH_TOKEN)

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repositories_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    The confirmed_email function is used to confirm a user's email address.

    :param token: str: Get the token from the request
    :param db: AsyncSession: Pass the database session to the repository
    :return: A message
    """
    email = await auth_service.get_email_from_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages.VERIFICATION_ERROR)
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repositories_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post('/request_email')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: AsyncSession = Depends(get_db)):
    """
    The request_email function sends an email to the user with a link to confirm their email address.

    :param body: RequestEmail: Get the email from the request body
    :param background_tasks: BackgroundTasks: Add a task to the background tasks
    :param request: Request: Get the base url
    :param db: AsyncSession: Pass the database session to the repository
    :return: A message
    """
    user = await repositories_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(send_email, user.email, user.username, str(request.base_url))
    return {"message": "Check your email for confirmation."}


@router.get('/{username}')
async def request_email(username: str, response: Response, db: AsyncSession = Depends(get_db)):
    """
    The request_email function is used to send an email to the user with a link to confirm their email address.

    :param username: str: Get the username from the url
    :param response: Response: Create a response object
    :param db: AsyncSession: Pass the database session to the repository
    :return: A message
    """
    print("__________________________________________________")
    print(f"{username} - зберігаємо що Він відкрив емейл в БД")
    print("__________________________________________________")
    return FileResponse('src/static/open_check.png', media_type="image/png", content_disposition_type="inline")