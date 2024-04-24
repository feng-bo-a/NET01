import mysql.connector
import yaml
from contextlib import contextmanager

from class_tools.log_tools import Log

log = Log()

with open('./config_yaml/database.yaml', 'r', encoding='utf-8') as db_file:
    data = yaml.safe_load(db_file)
    user = data['MYSQL_USER']
    password = data['MYSQL_PASSWORD']
    host = data['MYSQL_HOST']
    database = data['MYSQL_DB']


class DbTools:
    def __init__(self):
        try:
            self.conn = mysql.connector.connect(user=user, password=password, host=host, database=database)
        except mysql.connector.Error as err:
            log.error(f"Error: '{err}'")
            raise  # 重新抛出异常，调用时判断是否连接失败

    @contextmanager
    def connect(self):
        """@contextmanager 装饰器应该用于一个生成器函数，不是__init__构造函数。通常定义一个单独的方法"""
        try:
            yield self.conn
        finally:
            if self.conn.is_connected():
                self.conn.close()
                log.info("MySQL connection is closed")

    def execute_query(self, sql, args=None):
        cur = self.conn.cursor()
        try:
            cur.execute(sql, args)
            # 经过小写转换后的sql字符串是否以"select"开头
            if sql.lower().startswith('select'):
                result = cur.fetchall()
                log.info('本次查询到{}条数据'.format(len(result)))
                return result
            else:
                self.conn.commit()
                total = cur.rowcount
                log.info('本次执行影响了{}条数据,执行的SQL是:{}'.format(total, sql))
                return total
        except mysql.connector.Error as err:
            log.error(f"Error: '{err}'")
        finally:
            cur.close()


if __name__ == '__main__':
    db_test = DbTools()
    select_data = "select * from token_mgnt"
    # update_data = "UPDATE new_token SET token = '12345' WHERE id = 1;"
    db_test.execute_query(select_data)
