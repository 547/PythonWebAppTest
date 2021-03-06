import asyncio, logging
import aiomysql

def log(sql, args=()):
    logging.info("sql:%s" %sql)

@asyncio.coroutine
def  create_pool(loop, **kw):
    logging.info("create database connection pool")
    global __pool
    __pool = yield from aiomysql.create_pool(
        loop=loop,
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset', 'utf8'),
        autocommit=kw.get('autocommit', True)
    )
@asyncio.coroutine
def select(sql, args, size=None):
    log(sql,args)
    global __pool
    with (yield from __pool) as conn:
        cur = yield from conn.cursor(aiomysql.DictCursor)
        yield from cur.execute(sql.replace("?", "%s"), args or ())
        if size:
            rs = yield from cur.fetchmany(size)
        else:
            rs = yield from cur.fetchall()
        yield from cur.close()
        logging.info("rows return :%s" %len(rs))
        return rs
@asyncio.coroutine
def excute(sql, args):
    log(sql,args)
    with (yield from __pool) as conn:
        try:
            cur = yield from conn.cursor()
            yield from cur.exeture(sql.replace("?" , "%s"), args)
            affected = cur.rowcount
            yield from cur.close()
        except BaseException as e:
            raise
        return affected


#metaclass 元类：就是类的生成模板
#attrs 就是将一个类的属性整合成一个字典的样子有点像oc的kvc
class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if name=="Model":
            return type.__new__(cls,name,bases,attrs)
        tableName = attrs.get("__table__", None) or name
        logging.info("found model:%s (table : %s)" %(name, tableName))
        mappings = dict()
        fields = []
        primaryKey = None
        for k, v in attrs.items():
            if isinstance(v,fields):
                logging.info("found mappings :%s ==> %s" %(k,v))
                mappings[k] = v
                if v.primary_key:
                    if primaryKey:
                        raise RuntimeError(" Duplicate primary key for field: %s" %k)
                    primaryKey = k
                else:
                    fields.append(k)
        if not primaryKey:
            raise RuntimeError("Primary key no found")
        for k in mappings.keys():
            attrs.pop(k)
        escaped_fields = list(map(lambda f: '`%s`' % f, fields))
        attrs["__mappings__"] = mappings
        attrs["__table__"] = tableName
        attrs["__primary_key__"] = primaryKey
        attrs["__fields__"] = fields
        attrs["__selected__"] = "select %s , %s from %s" %(primaryKey, ",".join(escaped_fields), tableName)
        attrs["__insert__"] = "insert into `%s` (%s, `%s`) values (%s)" %(tableName, ",".join(escaped_fields), primaryKey, str(len(escaped_fields) + 1))
        attrs["__update__"] = "update `%s` set %s where `%s`=?" %(tableName, ",".join(map(lambda f: "`%s`=?" %(mappings.get(f).name or f), fields)), primaryKey)
        attrs["__delete__"] = "delete frome `%s` where `%s`=?" %(tableName, primaryKey)
        return type.__new__(cls,name,bases,attrs)


class Model(dict, metaclass=ModelMetaclass):
    def getValueOrDefault(self, key):
        value = getattr(self,key,None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug("using default value for %s : %s" %(key, str(value)))
                setattr(self,key,value)
        return value



    @classmethod
    @asyncio.coroutine
    def find(cls, pk):
        rs = yield from select("%s where `%s`=?" %(cls.__select__,cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        else:
            return cls(**rs[0])


    @asyncio.coroutine
    def remove(self):
        args = [self.get(self.__primary_key__)]
        rows = excute(self.__delete__, args)






