import sqlite3
from  utility.statemgmt import state
from core.config import db_query
# _conn = None
def get_db():
    # global _conn
    # if _conn is None:
    _conn = sqlite3.connect("skybound.db")
    _conn.row_factory = sqlite3.Row
    return _conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(db_query['COMPANY']['CREATE'])
    conn.commit()

init_db()

def execute_query(query,*args):
    try:
        conn = get_db()
        cur = None
        if args:
            cur = conn.execute(query, args)   # ← pass args as tuple
        else:
            cur = conn.execute(query)
        data = cur.fetchone()
        conn.commit()
        conn.close()
        return data
    except Exception as e:
        print("Exception in Query Exceution", e)
        raise

def execute_company_query(query,*args):
    try:
        conn = get_db()
        cur = conn.cursor()
        aliasname = state.value
        if aliasname :
             query = query.replace('<>',aliasname)
        if args:
            cur = conn.execute(query, args)   # ← pass args as tuple
        else:
            cur = conn.execute(query)

        rows = cur.fetchall()
        
        conn.commit()
        conn.close()
        
        return [dict(r) for r in rows]
    except Exception as e:
        print("Exception in company Query Exceution", e)
        raise

def fetch_single_record(query,*args):
    try:
        conn = get_db()
        cur = None
        aliasname = state.value
        if aliasname :
             query = query.replace('<>',aliasname)
        if args:
            cur = conn.execute(query, args)   # ← pass args as tuple
        else:
            cur = conn.execute(query)

        data = cur.fetchone()
        conn.close()
        return data
    except Exception as e:
        print("Exception in company Query Exceution", e)
        raise

def update_record(set_clause,values):
        try:
            conn = get_db()
            aliasname = state.value
           
            query = f"UPDATE <>_lead SET {set_clause} WHERE id = ?"
            if aliasname :
                query = query.replace('<>',aliasname)
            
            conn.execute(query, values)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print("Exception in update Query Exceution", e)
            raise
        