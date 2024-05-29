# FastAPI PhotoShare Project

This project is a FastAPI application that allows users to share photos and comments on them. It includes user authentication, photo uploading, commenting, and role-based access control.

## Features

- User registration and authentication with JWT tokens
- Photo uploading and transformation (greyscale, delete background, oil paint, sepia, outline)
- Commenting on photos
- QR code generation for photo URLs
- User roles (admin, moderator, user) with different access levels
- Rate limiting to prevent abuse
- Cloudinary integration for photo storage
- Redis for caching and rate limiting
- PostgreSQL database for data storage
- Email verification and password reset
- User banning and role management

## Getting Started

1. Clone the repository:

```bash
git clone https://github.com/your-username/fastapi-photo-share.git
cd fastapi-photo-share
```

2. Install the dependencies:

```bash
pip install poetry
poetry shell
poetry update
```

3. Please rename `.env.example` file to `.env` and set up the environment variables in it.

4. Populate database schema:

```bash
alembic upgrade head
```

5. Run the application:

```bash
python main.py
```

6. Access the API documentation at `http://localhost:8000/docs`.

## API Endpoints

### Authentication

- **POST /api/auth/signup**: Register a new user.
- **POST /api/auth/login**: Log in an existing user.
- **POST /api/auth/refresh_token**: Refresh the access token.
- **POST /api/auth/logout**: Log out the current user.

### Photos

- **GET /api/photos/**: Get a list of photos.
- **GET /api/photos/{photo_id}**: Get a specific photo by its ID.
- **GET /api/photos/link/{photo_id}**: Get a link or QR code for a specific photo.
- **POST /api/photos/**: Upload a new photo.
- **POST /api/photos/transform/{photo_id}**: Transform a photo (e.g., apply filters).
- **DELETE /api/photos/{photo_id}**: Delete a specific photo.
- **PUT /api/photos/{photo_id}**: Update a specific photo's details.

### Comments

- **POST /api/comments/{photo_id}**: Add a new comment to a photo.
- **GET /api/comments/{photo_id}**: Get a list of comments for a specific photo.
- **GET /api/comments/users/{user_id}**: Get a list of comments by a specific user.
- **GET /api/comments/users/{user_id}**: Get a list of comments by a specific user for a specific photo.
- **DELETE /api/comments/record/{comment_id}**: Delete a specific comment.

### Users

- **GET /api/users/me**: Get the current user's profile.
- **PUT /api/users/**: Update the current user's profile.
- **PUT /api/users/avatar**: Update the current user's avatar.
- **GET /api/users/all**: Get a list of all users (admin only).
- **GET /api/users/{user_id}**: Get a specific user by their ID.
- **PUT /api/users/role/{user_id}**: Change a user's role (admin only).
- **PUT /api/users/ban/{user_id}**: Ban or unban a user (admin only).

## Developed by:

### PyMagic team:

- [Roman Hnatiak](https://github.com/Hnatiak)
- [Yuliia Chorna](https://github.com/YuliiaChorna1)
- [Gennadiy Shpak](https://github.com/gyshpak)
- [Andrii Demenin](https://github.com/demagoit)
- [Olena Polkhova](https://github.com/ElenaPolkhovaS)

## FOR DEVS:

HERE IS FRONTEND REPO: https://github.com/gyshpak/PhotoShare-Python-front

HERE IS FRONTEND RENDER: https://photoshare-python-front.onrender.com/

&#xa0;
