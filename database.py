import sqlite3
from  utility.statemgmt import state

def get_db():
    conn = sqlite3.connect("skybound.db")
    conn.row_factory = sqlite3.Row
    return conn

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
        cur = None
        aliasname = state.value
        if aliasname :
             query = query.replace('<>',aliasname)
        if args:
            print("query and args",query,args)
            cur = conn.execute(query, args)   # ← pass args as tuple
        else:
            cur = conn.execute(query)

        rows = cur.fetchall()
        
        conn.commit()
        conn.close()
        for r in rows :
            print("fetched data", r)

        
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
        conn.commit()
        conn.close()
        return data
    except Exception as e:
        print("Exception in company Query Exceution", e)
        raise