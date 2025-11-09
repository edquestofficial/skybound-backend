from jose import jwt 
from db_config import get_connection

async def get_user(username: str, password: str, alias_name: str):
    conn =  get_connection()
    if conn is None:
        return False
    cursor = conn.cursor()
    tabel_name = alias_name + "_employees"
    query = f"SELECT {tabel_name}.username,{tabel_name}.role,company_details.alias_name FROM {tabel_name} LEFT JOIN company_details ON {tabel_name}.company_id = company_details.id WHERE {tabel_name}.username=%s AND {tabel_name}.password=%s"
    try:    
        cursor.execute(query, (username, password))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print("Error while fetching user:", e)
        return None

async def authenticate_user(username: str, password: str, alias_name: str):
    user_data = await get_user(username,password ,alias_name)
    if user_data is None:
        return {"message": "Error during authentication",
                "data": None}
    
    token = jwt.encode({'data': user_data}, 'secret_key', algorithm='HS256')
    return {"message": "Authentication successful",
            "data": token}

async def verify_token(token: str):
    try:
        decoded_token = jwt.decode(token, 'secret_key', algorithms=['HS256'])  
        return decoded_token['data']
    except jwt.ExpiredSignatureError:
        return None
    
# print(verify_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjpbIk1hbmplZXQxMjMiLCJociIsImVkIl19.gDNrzy9KZBJlyk5FeygnxKdep4YW-aktl51CvhYF-UM"))
