from jose import jwt 
from db_config import get_connection
from util.config import response, MESSAGES
from model.user import User
import json

def get_user(userdata):
    conn =  get_connection()
    cursor = conn.cursor()
    tabel_name = userdata.alias_name + "_employees"
    query = f"SELECT {tabel_name}.username,{tabel_name}.role,company_details.alias_name,company_details.id FROM {tabel_name} LEFT JOIN company_details ON {tabel_name}.company_id = company_details.id WHERE {tabel_name}.username=%s AND {tabel_name}.password=%s"
    try:    
        cursor.execute(query, (userdata.username, userdata.password))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result:
            return response(
                status="success",
                code=200,
                message=MESSAGES["USER_DATA_FETCHED"],
                data=result,
                )
        else:
            return response(
                status="error",
                code=404,
                message=MESSAGES["NO_USER_FOUND"],
                error="No user with the provided credentials."
            )
    except Exception as e:
        print("Error while fetching user:", e)
        return response(
            status="error",
            code=500,
            message=MESSAGES["USER_FETCH_ERROR"],
            error=str(e),
            )

def authenticate_user(userdata):
    user_data = get_user(userdata)

    print(user_data)
    if user_data.status == "error":
        return user_data
    
    token = jwt.encode({'data': user_data.data}, 'secret_key', algorithm='HS256')
    return response(
        status="success",
        code=200,
        message=user_data.message,
        data={
            "token": token,
            "username":user_data.data[0],
            "role":user_data.data[1],
            "alias_name":user_data.data[2],
            "company_id":user_data.data[3]
        }
    )

async def verify_token(token: str):
    try:
        decoded_token = jwt.decode(token, 'secret_key', algorithms=['HS256'])  
        return decoded_token['data']
    except jwt.ExpiredSignatureError:
        return None
    
# print(verify_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjpbIk1hbmplZXQxMjMiLCJociIsImVkIl19.gDNrzy9KZBJlyk5FeygnxKdep4YW-aktl51CvhYF-UM"))
