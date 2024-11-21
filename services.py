from database import execute_query
import logging
from helpers import jwt_verifier, hash_password, build_response, extract_payload_data, validate_otp, get_user_data, prepare_response_data, extract_form_data, check_for_duplicate_keys, validate_data, otp_util
from validation_strings import message_strings
import datetime as dt



# user registration
async def user_registration_logic(request):
    logging.info("Received request for user registration")

    try:
        payload = await request.form()
        logging.info(f"Payload received: {payload}")

        # Validate required fields
        username = payload.get("name")
        email = payload.get("email")
        password = payload.get("password")
        mobile = payload.get("mobile_no")

        if not username or not email or not password or not mobile:
            return await build_response(
                message="Username, email, password and mobile number are required",
                status=message_strings["status_0"],
                status_code=400
            )

        # Check if the user already exists
        existing_user_check = await execute_query(
            "SELECT user_id FROM users WHERE mobile_no = $1", (mobile,), flag="get"
        )

        if existing_user_check:
            return await build_response(
                message="User with this mobile already exists",
                status=message_strings["status_0"],
                status_code=400
            )

        # Hash the password before storing it
        hashed_password = hash_password(password)

        # Insert the new user into the database
        insert_user_query = """
            INSERT INTO users (username, email, password_hash, mobile_no) 
            VALUES ($1, $2, $3, $4) 
            RETURNING user_id
        """
        new_user = await execute_query(
            insert_user_query, params=(username, email, hashed_password, mobile,), flag="insert"
        )

        if not new_user:
            return await build_response(
                message="User registration failed",
                status=message_strings["status_0"],
                status_code=400
            )

        else:
            otp_payload = {"mobile_no": mobile}
            
            # Generate OTP and send to mobile
            response = await generate_otp_logic(data=otp_payload)
            
            if response[1] == 200:  # OTP generation success        
                logging.info(f"User registeration successfull for id: {new_user}")
                
                otp = response[0]['data'].get('otp')
                new_user['otp'] = otp
                # Return successful response
                return await build_response(
                    message="User registered successfully",
                    status=message_strings["status_1"],
                    data= new_user,
                    status_code=200,    
                )

    except Exception as e:
        logging.error(f"Unexpected error in user_registration_logic: {e}")
        return await build_response(
            message= message_strings['internal_error'],
            status=message_strings["status_0"],
            status_code=400
        )


# list tasks
async def list_tasks_logic(request, status=None):
    logging.info("Received request to list tasks")

    try:
        user_id = await jwt_verifier(request)
        if isinstance(user_id, tuple):
            return user_id

        logging.info(f"User ID: {user_id}, Status filter: {status}")

        query = "SELECT * FROM tasks"
        if status:
            query += " WHERE status = $1"
            tasks = await execute_query(query, params=(status,), flag="get")
        else:
            tasks = await execute_query(query, flag="get")

        if not tasks:
            return await build_response(
                message="No tasks found",
                status=message_strings["status_0"],
                status_code=404
            )

        logging.info(f"Tasks retrieved: {tasks}")
        return await build_response(
            message="Tasks retrieved successfully",
            status=message_strings["status_1"],
            data=tasks,
            status_code=200
        )
    except Exception as e:
        logging.error(f"Unexpected error in list_tasks_logic: {e}")
        return await build_response(
            message= message_strings['internal_error'],
            status=message_strings["status_0"],
            status_code=400
        )


# create task
async def create_task_logic(request):
    logging.info("Received request to create a new task")

    try:
        user_id = await jwt_verifier(request)
        if isinstance(user_id, tuple):
            return user_id

        payload = await request.form()
        logging.info(f"Payload received: {payload}")

        title = payload.get("title")
        description = payload.get("description")
        status = payload.get("status")
        due_date = payload.get("due_date")

        if not title or not due_date:
            return await build_response(
                message="Title and due_date are required",
                status=message_strings["status_0"],
                status_code=400
            )

        due_date = dt.datetime.strptime(due_date, "%y-%m-%d").date()
        query = """
            INSERT INTO tasks (title, description, status, due_date, created_at, updated_at, user_id)
            VALUES ($1, $2, $3, $4, NOW(), NOW(), $5)
            RETURNING task_id
        """
        task_id = await execute_query(query, params=(title, description, status, due_date, user_id), flag="insert")

        if not task_id:
            return await build_response(
                message="Task creation failed",
                status=message_strings["status_0"],
                status_code=400
            )

        logging.info(f"Task created successfully with ID: {task_id}")
        return await build_response(
            message="Task created successfully",
            status=message_strings["status_1"],
            data={"task_id": task_id.get("task_id")},
            status_code=201
        )
    except Exception as e:
        logging.error(f"Unexpected error in create_task_logic: {e}")
        return await build_response(
            message= message_strings['internal_error'],
            status=message_strings["status_0"],
            status_code=400
        )



# update task
async def update_task_logic(request):
    logging.info("Received request to update task")

    try:
        user_id = await jwt_verifier(request)
        if isinstance(user_id, tuple):
            return user_id

        payload = await request.form()
        logging.info(f"Payload received: {payload}")

        task_id = payload.get("task_id")
        fields_to_update = {key: value for key, value in payload.items() if key != "task_id" and value is not None}

        if not task_id:
            return await build_response(
                message="Task ID is required",
                status=message_strings["status_0"],
                status_code=400
            )

        if not fields_to_update:
            return await build_response(
                message="No fields to update",
                status=message_strings["status_0"],
                status_code=400
            )

        set_clause = ", ".join([f"{key} = ${i+2}" for i, key in enumerate(fields_to_update.keys())])
        query = f"UPDATE tasks SET {set_clause}, updated_at = NOW() WHERE id = $1 RETURNING id"

        params = [task_id] + list(fields_to_update.values())
        result = await execute_query(query, params=tuple(params), flag="update")

        if not result:
            return await build_response(
                message="Task not found",
                status=message_strings["status_0"],
                status_code=404
            )

        logging.info(f"Task {task_id} updated successfully")
        return await build_response(
            message="Task updated successfully",
            status=message_strings["status_1"],
            data={"task_id": result.get("id")},
            status_code=200
        )
    except Exception as e:
        logging.error(f"Unexpected error in update_task_logic: {e}")
        return await build_response(
            message= message_strings['internal_error'],
            status=message_strings["status_0"],
            status_code=400
        )



# delete task
async def delete_task_logic(request):
    logging.info("Received request to delete task")

    try:
        user_id = await jwt_verifier(request)
        if isinstance(user_id, tuple):
            return user_id

        payload = request.query_params
        logging.info(f"Payload received: {payload}")

        task_id = payload.get("task_id")

        if not task_id:
            return await build_response(
                message="Task ID is required",
                status=message_strings["status_0"],
                status_code=400
            )

        query = "DELETE FROM tasks WHERE id = $1 RETURNING id"
        result = await execute_query(query, params=(task_id,), flag="delete")

        if not result:
            return await build_response(
                message="Task not found",
                status=message_strings["status_0"],
                status_code=404
            )

        logging.info(f"Task {task_id} deleted successfully")
        return await build_response(
            message="Task deleted successfully",
            status=message_strings["status_1"],
            data={"task_id": result.get("id")},
            status_code=200
        )
    except Exception as e:
        logging.error(f"Unexpected error in delete_task_logic: {e}")
        return await build_response(
            message= message_strings['internal_error'],
            status=message_strings["status_0"],
            status_code=400
        )




# order task
async def order_tasks_logic(request):
    logging.info("Received request to order tasks")

    try:
        user_id = await jwt_verifier(request)
        if isinstance(user_id, tuple):
            return user_id

        payload = await request.form()
        logging.info(f"Payload received: {payload}")

        task_id = payload.get("task_id")
        position = payload.get("position")

        if not task_id or position is None:
            return await build_response(
                message="Task ID and position are required",
                status=message_strings["status_0"],
                status_code=400
            )

        # Ensure the position is a valid integer (e.g., 1st, 2nd, etc.)
        if not isinstance(position, int) or position < 1:
            return await build_response(
                message="Position must be a positive integer",
                status=message_strings["status_0"],
                status_code=400
            )

        # Query to get the current list of tasks ordered by priority or created_at
        current_tasks = await execute_query(
            "SELECT id FROM tasks ORDER BY priority DESC, created_at ASC", flag="get"
        )

        # Check if the task_id is valid and exists
        if not current_tasks or task_id not in [task['id'] for task in current_tasks]:
            return await build_response(
                message="Task ID not found",
                status=message_strings["status_0"],
                status_code=404
            )

        # Reordering logic based on the provided position
        # For simplicity, we will adjust the priority based on the requested position.
        # This could be more complex if you're tracking specific priorities in the database.
        # Here, we are simply shifting other tasks up/down to make room for the reordered task.

        # First, let's update the task's position (or priority)
        query = """
            UPDATE tasks 
            SET priority = $1, updated_at = NOW() 
            WHERE id = $2 
            RETURNING id
        """
        result = await execute_query(query, params=(position, task_id), flag="update")

        if not result:
            return await build_response(
                message="Task ordering failed",
                status=message_strings["status_0"],
                status_code=400
            )

        logging.info(f"Task {task_id} ordered successfully with position {position}")
        return await build_response(
            message="Task ordered successfully",
            status=message_strings["status_1"],
            data={"task_id": result.get("id")},
            status_code=200
        )

    except Exception as e:
        logging.error(f"Unexpected error in order_task_logic: {e}")
        return await build_response(
            message= message_strings['internal_error'],
            status=message_strings["status_0"],
            status_code=400
        )

    
# verify otp logic
async def verify_otp_logic(request):
    try:
        logging.info("Verify OTP logic called for OTP verification and FCM update")
        form_data = await extract_form_data(request)
        
        if form_data is None:
            return await build_response(
                message=message_strings['duplicate_values'],
                status=message_strings['status_0'],
                status_code=400
            )
        
        mobile, otp = await extract_payload_data(form_data)
        if not mobile or not otp:
            return await build_response(message="Mobile number or OTP missing", status=False, status_code=400)
        
        # Validate OTP
        if not await validate_otp(mobile, otp):
            return await build_response(
                message=message_strings["incorrect_details"],
                status=False,
                status_code=400
            )

        user_data, token = await get_user_data(mobile)
        if not user_data:
            return await build_response(
                message='User not found with this mobile number',
                status=False,
                status_code=400
            )
        
        responsedata = await prepare_response_data(user_data, token)

        return await build_response(
            message="Mobile verified",
            status=True,
            status_code=200,
            data= responsedata
        )
    
    except Exception as e:
        logging.error(f"Error at verify_otp: {str(e)}")
        return await build_response(message=str(e), status=False, status_code=400)


# Generate otp logic
async def generate_otp_logic(request=None, data=None):
    logging.info('Received request for generating OTP')
    try:
        if request:
            try:
                data = await request.json()
                logging.info("Received JSON payload for OTP generation")
            except Exception:
                data = await request.form()
                # Check for duplicate values
                data = await check_for_duplicate_keys(data)
                if data == None:
                    return await build_response(
                        message= message_strings[ 'duplicate_values'],
                        status= message_strings['status_0'],
                        status_code= 400
                    )

                logging.info("Fallback to form data for OTP generation")

        if not data:
            raise ValueError("No data provided for OTP generation")

        message, validdata = await validate_data(data, 'send')
        logging.info('Validating data')

        if not validdata:
            return await build_response(message=message, status=message_strings['status_0'], status_code=400)

        mobile_no = data.get('mobile_no')

        # Check if the user exists in the 'user' table
        validate_user_query = """
            SELECT user_id FROM users WHERE mobile_no = $1
        """
        validate_user_params = (mobile_no,)
        user_exists = await execute_query(query=validate_user_query, params=validate_user_params, flag='get')

        if not user_exists:
            # User does not exist, return is_registered = 0
            return await build_response(
                message='otp not generated',
                status=message_strings['status_1'],
                status_code=200
            )

        # Otp generate logic
        otp = await otp_util(6)
        logging.info(f"Generated OTP: {otp}")

        create_date = dt.datetime.now()
        update_date = dt.datetime.now()

        # Check if a record exists in the validate_otp table
        validation_query = """
            INSERT INTO validate_otp (mobile, otp, created, updated)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (mobile)
            DO UPDATE SET otp = EXCLUDED.otp, updated = EXCLUDED.updated
            RETURNING id
        """
        query_params = (mobile_no, otp, create_date, update_date)
        await execute_query(query=validation_query, params=query_params, flag='insert')

        return await build_response(
            message="OTP sent successfully",
            status=message_strings['status_1'],
            status_code=200,
            data = {'otp' : otp}
        )

    except Exception as e:
        logging.error(f"Error in generate_otp_logic: {str(e)}")
        return await build_response(message=str(e), status=message_strings['status_0'], status_code=400)