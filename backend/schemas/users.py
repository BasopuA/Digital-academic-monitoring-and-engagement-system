"""
Creating schema for user entity.
"""

# pylint: disable=import-error,too-few-public-methods
from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    """
    Base schema for User.

    Attributes:
        username (str): The username of the user.
        active (bool): Whether the user is active.
    """

    username: str
    password: str 


class UserCreate(UserBase):
    """
    Schema for creating a new User.

    Attributes:
        password (str): Password for the user.
        employee_id (Optional[int]): Related employee ID.
    """

class UserUpdate(BaseModel):
    """
    Schema for updating a User.

    Attributes:
        username (Optional[str]): Updated username.
        password (Optional[str]): Updated password.
        active (Optional[bool]): Updated active status.
        employee_id (Optional[int]): Updated employee reference.
    """

    username: Optional[str] = None
    active: Optional[bool] = None
    password:  Optional[str] = None


class UserResponse(UserBase):
    """
    Schema for returning User data in API responses.

    Attributes:
        id (int): Unique identifier of the user.
        employee (Optional[EmployeeResponse]): Related employee information.
    """


class UserInfo(BaseModel):
    """Represents a user's basic information.

    Attributes:
        preferred_username (str): The user's preferred username.
        email (Optional[str]): The user's email address. Defaults to None.
        full_name (Optional[str]): The user's full name. Defaults to None.
    """

    preferred_username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
