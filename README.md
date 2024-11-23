# Avrio-Energy
Task Management system

# Task Management System

This project is a Task Management System built using **FastAPI** with JWT authentication. The system exposes eight APIs for managing tasks and users. It also supports OTP validation for user registration.

## APIs

The following eight APIs are available:

- **LIST_TASKS**: `/tasks/task_list`  
  Retrieve the list of tasks.

- **CREATE_TASK**: `/tasks/create_task`  
  Create a new task.

- **UPDATE_TASK**: `/tasks/update_task`  
  Update an existing task.

- **DELETE_TASK**: `/tasks/delete_task`  
  Delete a task.

- **ORDER_TASKS**: `/tasks/order_task`  
  Order tasks in a specific sequence.

- **REGISTER_USER**: `/tasks/register_user`  
  Register a new user.

- **VALIDATE_OTP**: `/tasks/verify_otp`  
  Validate the OTP sent to the user for verification.

- **GENERATE_OTP**: `/tasks/generate_otp`  
  Generate an OTP for user registration.

## Database Schema

The system uses three main tables in the PostgreSQL database:

1. **users table**
   - `user_id`: Unique identifier for the user
   - `username`: Username of the user
   - `password_hash`: Hashed password for secure authentication
   - `created_at`: Date and time when the user was created
   - `updated_at`: Date and time when the user was last updated
   - `mobile_no`: Mobile number of the user
   - `email`: Email address of the user

2. **tasks table**
   - `task_id`: Unique identifier for the task
   - `title`: Title of the task
   - `description`: Description of the task
   - `status`: Status of the task (e.g., "To Do", "In Progress", "Done")
   - `due_date`: Due date for the task
   - `created_at`: Date and time when the task was created
   - `updated_at`: Date and time when the task was last updated
   - `user_id`: The user who owns the task (foreign key to the users table)

3. **validate_otp table**
   - `id`: Unique identifier for the OTP entry
   - `mobile`: Mobile number associated with the OTP
   - `otp`: OTP value
   - `created`: Date and time when the OTP was generated
   - `updated_at`: Date and time when the OTP entry was last updated

## Database

This application uses **PostgreSQL** as the database for storing user data, task data, and OTP details.

## Setup Instructions

1. Clone the repository.
2. Install the dependencies from the `requirements.txt` file:
   ```bash
   pip install -r requirements.txt
