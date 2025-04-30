# import fastapi_admin
# from fastapi_admin.app import app as admin_app
# from fastapi import FastAPI
# from starlette.middleware.sessions import SessionMiddleware
# from app.database import DATABASE_URL

# # Initialize the admin panel
# async def create_admin():
#     await fastapi_admin.app.init(
#         admin_secret="your_secret_key",
#         database_url=DATABASE_URL,
#         templates_dir="templates",  # if you have HTML templates
#     )

# # Create FastAPI app
# app = FastAPI()

# app.add_middleware(SessionMiddleware, secret_key="your_secret_key")

# @app.on_event("startup")
# async def startup():
#     await create_admin()

# # Mount the admin app
# app.mount("/admin", admin_app)
