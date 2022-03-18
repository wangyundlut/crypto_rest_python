from datetime import datetime, timedelta

# local时间为东八区的时间
HOURS8 = 8

def binance_timestamp():
    now = int((datetime.utcnow() + timedelta(hours=HOURS8)).timestamp() * 1000)
    return now

def exch_to_local(time_exchange):
    # 交易所的时间 -> 本地的时间 int -> datetime
    time_local = datetime.utcfromtimestamp(int(time_exchange / 1000))
    time_local = time_local.replace(tzinfo=None)
    time_local = time_local + timedelta(hours=HOURS8)
    # time_local = CHINA_TZ.localize(time_local)
    return time_local

def local_to_exch(time_local):
    # 本地的时间 ->交易所的时间 datetime -> int
    # time.strptime会自动忽略毫秒，只取最小精度秒
    # time_local = datetime.now()
    time_utc = time_local - timedelta(hours=HOURS8)
    stamp_utc = int(time_utc.timestamp() * 1000)
    time_exchange = stamp_utc + HOURS8 * 3600 * 1000

    return time_exchange

def local_timestamp(time_local):
    # 本地时间 -> 数据库时间 datetime -> str
    return time_local.strftime("%Y-%m-%d %H:%M:%S")