
import opteryx

SQL = "SELECT * FROM test/data/tweets WHERE user_name = %s"

conn = opteryx.connect(

)
cursor = conn.cursor()
cursor.execute(SQL, ("BBCNews",))

print(cursor.fetchmany(100))