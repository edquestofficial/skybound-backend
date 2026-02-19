import re
import sqlite3
from  utility.statemgmt import state
from core.config import db_query

conn = None
def get_db():
    _conn = sqlite3.connect("skybound.db")
    _conn.row_factory = sqlite3.Row
    return _conn

def init_db(query):
    conn = get_db()
    cursor = conn.cursor()
    cursor.executescript(query)
    conn.commit()
    conn.close()

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
        return None
    finally:
        # This runs NO MATTER WHAT, even after a return statement
        if conn:
            conn.close()

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
        return []
    finally:
        # This runs NO MATTER WHAT, even after a return statement
        if conn:
            conn.close()

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
        return None
    finally:
        # This runs NO MATTER WHAT, even after a return statement
        if conn:
            conn.close()
      
def update_query(query,set_clause,values):
        try:
            conn = get_db()
            aliasname = state.value
            query = query.replace('<set_clause>',set_clause)
            if aliasname :
                query = query.replace('<>',aliasname)
            conn.execute(query, values)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print("Exception in update Exceution", e)
            return None
        finally:
        # This runs NO MATTER WHAT, even after a return statement
            if conn:
                conn.close()

def execute_select_query(base_query,conditions,values):
     try:
            conn = get_db()
            cur = conn.cursor()
            aliasname = state.value
            if aliasname :
                base_query = re.sub(r'<>', aliasname, base_query)
            if len(conditions) > 0:
                base_query = base_query + " WHERE " + conditions
            cur =conn.execute(base_query, values)
            rows = cur.fetchall()
            conn.commit()
            conn.close()
            return [{k: v for k, v in dict(r).items() } for r in rows ]
     except Exception as e:
            print("Exception in select User Exceution", e)
            return None
     finally:
        # This runs NO MATTER WHAT, even after a return statement
        if conn:
            conn.close()

def excute_simple_query(query,*args):
    try:
        conn = get_db()
        conn.execute(query,args)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Exception in simple Query Exceution", e)
        return None
    finally:
        # This runs NO MATTER WHAT, even after a return statement
        if conn:
            conn.close()

def execute_filter_lead(base_query,conditions,values):
     try:
            conn = get_db()
            cur = conn.cursor()
            aliasname = state.value
            if aliasname :
                base_query = re.sub(r'<>', aliasname, base_query)
            # if len(conditions) > 0:
                base_query = re.sub(r'{conditions}', conditions, base_query)

            cur =conn.execute(base_query, values)
            rows = cur.fetchall()
            conn.commit()
            conn.close()
            return [{k: v for k, v in dict(r).items() } for r in rows ]
     except Exception as e:
            print("Exception in select User Exceution", e)
            return []
     finally:
        # This runs NO MATTER WHAT, even after a return statement
        if conn:
            conn.close()

def get_state(query,*args):
        conn = get_db()
        cur = conn.cursor()
        cur= conn.execute(query,args)
        rows = cur.fetchall()
        conn.commit()
        conn.close()
        return [{k: v for k, v in dict(r).items() } for r in rows ]

# create multiple table using query with ; separator
def create_table(query):
    try:
        conn = get_db()
        aliasname = state.value
        if aliasname :
            query = query.replace('<>',aliasname)
        conn.executescript(query)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Exception in create table Exceution", e)
        return None
    finally:
        # This runs NO MATTER WHAT, even after a return statement
        if conn:
            conn.close()



def truncate_table(table_name):
    try:
        conn = get_db()
        aliasname = state.value
        if aliasname :
             table_name = table_name.replace('<>',aliasname)
        query = f"DELETE FROM {table_name};DELETE FROM sqlite_sequence WHERE name='{table_name}';"
        conn.executescript(query)
        conn.commit()
        conn.close()
    except Exception as e:
        print("Exception in company Query Exceution", e)
        return []
    finally:
        # This runs NO MATTER WHAT, even after a return statement
        if conn:
            conn.close()