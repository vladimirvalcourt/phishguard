# Swagger UI Integration for FastAPI
#
# Add the following to your backend/main.py to serve interactive API docs:
#
# from fastapi import FastAPI
# from fastapi.openapi.docs import get_swagger_ui_html
#
# app = FastAPI()
#
# @app.get("/docs", include_in_schema=False)
# async def custom_swagger_ui_html():
#     return get_swagger_ui_html(openapi_url="/openapi.json", title="PhishGuard API Docs")
#
# Your OpenAPI spec (docs/openapi.yaml) will be auto-served at /openapi.json if using FastAPI.
#
# For more customization, see FastAPI docs: https://fastapi.tiangolo.com/advanced/extending-openapi/
